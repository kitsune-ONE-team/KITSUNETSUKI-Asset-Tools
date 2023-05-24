# Copyright (c) 2023 kitsune.ONE team.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import bpy
import copy
import decimal
import math
import os
import typing
import mathutils

try:
    from collections.abc import Callable
except ImportError:
    from collections import Callable

from pathlib import Path

from bpy_extras.io_utils import ExportHelper

from kitsunetsuki.exporter.base import Exporter
from kitsunetsuki.base.objects import apply_modifiers, make_local


class BVHQExporter(Exporter):
    def __init__(self, args):
        super().__init__(args)
        self._action = args.action and bpy.data.actions[args.action]
        self._speed_scale = 1
        self._output = args.output or args.inputs[0].replace('.blend', '.bvhq')

    def _export(self, armature):
        hierarchy = []

        def add_bone(bone):
            channels = []
            if not bone.use_connect or not bone.parent:
                channels += ['Xposition', 'Yposition', 'Zposition']
            channels += ['Irotation', 'Jrotation', 'Krotation', 'Rrotation']

            if bone.parent:
                offset = bone.head_local - bone.parent.head_local
                offset_end = bone.tail_local - bone.parent.tail_local
            else:
                offset = bone.head_local
                offset_end = bone.tail_local

            bone_data = {
                'joint': bone.name,
                'offset': tuple(offset),
                'offset_end': tuple(offset_end),
                'channels': channels,
                'children': [],
            }
            hierarchy.append(bone_data)

            if bone.parent:
                for bone_data in hierarchy:
                    if bone_data['joint'] == bone.parent.name:
                        bone_data['children'].append(len(hierarchy) - 1)
                        break

            for child in bone.children:
                add_bone(child)

        for bone in armature.data.bones:
            if not bone.parent:
                add_bone(bone)

        frame_start = bpy.context.scene.frame_start
        frame_end = bpy.context.scene.frame_end
        if self._action and armature.animation_data:
            armature.animation_data.action = self._action
            frame_start, frame_end = self._action.frame_range

        speed_scale = 1
        frame = float(frame_start)
        frame_int = None
        t = decimal.Decimal(0)
        fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
        dt = decimal.Decimal(1 / fps)
        t += dt

        motion = {
            'frames': 0,
            'frame_time': 1,
            'data': [],
        }
        while frame <= frame_end:
            # switch frame
            if frame_int != math.floor(frame):
                frame_int = math.floor(frame)
                bpy.context.scene.frame_current = frame_int
                bpy.context.scene.frame_set(frame_int)

            if isinstance(self._speed_scale, Callable):
                speed_scale = self._speed_scale(frame_int)
            else:
                speed_scale = self._speed_scale

            # switch subframe
            if speed_scale != 1:
                bpy.context.scene.frame_subframe = frame - frame_int

            # write bone matrices
            frame_data = []
            for bone_data in hierarchy:
                bone = armature.pose.bones[bone_data['joint']]
                matrix = bone.matrix
                pos = matrix.to_translation()
                quat = matrix.to_quaternion()
                channels = {
                    'Xposition': pos.x,
                    'Yposition': pos.y,
                    'Zposition': pos.z,
                    'Irotation': quat.x,
                    'Jrotation': quat.y,
                    'Krotation': quat.z,
                    'Rrotation': quat.w,
                }
                for channel in bone_data['channels']:
                    frame_data.append(channels[channel])
            motion['data'].append(frame_data)
            motion['frames'] += 1

            # advance to the next frame
            frame += speed_scale
            t += dt

        return {
            'hierarchy': hierarchy,
            'motion': motion,
        }

    def _process_data(self, data):
        lines = []

        def append(l, level, s, *args, **kwargs):
            l.append(('\t' * level) + s.format(*args, **kwargs))

        def add_bone(hid, level=0):
            bone_data = data['hierarchy'][hid]

            append(lines, level, '{type} {joint}', **{
                'type': 'ROOT' if level == 0 else 'JOINT',
                'joint': bone_data['joint'],
            })
            append(lines, level, '{{')
            append(lines, level, '\tOFFSET {:.6f} {:.6f} {:.6f}', *bone_data['offset'])
            append(lines, level, '\tCHANNELS {num} {ch}', **{
                'num': len(bone_data['channels']),
                'ch': ' '.join(bone_data['channels']),
            })

            if bone_data['children']:
                for hid in bone_data['children']:
                    add_bone(hid, level + 1)
            else:
                append(lines, level, '\tEnd Site')
                append(lines, level, '\t{{')
                append(lines, level, '\t\tOFFSET {:.6f} {:.6f} {:.6f}', *bone_data['offset_end'])
                append(lines, level, '\t}}')
            append(lines, level, '}}')

        lines.append('HIERARCHY')
        add_bone(0)

        lines.append('MOTION')
        frames = data['motion']['frames']
        frame_time = data['motion']['frame_time']
        lines.append(f'Frames: {frames}')
        lines.append('Frame Time: {:.6f}'.format(frame_time))
        for frame_data in data['motion']['data']:
            lines.append(' '.join(map(lambda x: '{:.6f}'.format(x), frame_data)))
        lines += [''] * 3
        return '\n'.join(lines)

    def convert(self):
        if self._script_names:
            for script_name in self._script_names:
                if script_name:
                    self._execute_script(script_name)

        for c in bpy.data.collections:
            # hide all objects inside the collection because we can't hide the collection
            if c.hide_viewport:
                for obj in c.objects:
                    obj.hide_set(True)
                continue

            objects = []
            for obj in c.objects:
                if obj.hide_viewport:
                    obj.hide_set(True)
                    continue

                if obj.hide_get():
                    continue

                objects.append(obj)

            if not objects:
                continue

            for obj in objects:
                make_local(obj)
                apply_modifiers(obj)

            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects:
                if obj.type == 'ARMATURE':
                    bpy.context.view_layer.objects.active = obj
                    break

        if self._post_script_names:
            for script_name in self._post_script_names:
                if script_name:
                    self._execute_script(script_name)

        frame = bpy.context.scene.frame_current

        bpy.context.scene.frame_set(0)
        data = self._export(bpy.context.view_layer.objects.active)
        data = self._process_data(data)
        with open(self._output, 'w') as f:
            f.write(data)
        bpy.context.scene.frame_set(int(frame))


class BVHQExporterOperator(bpy.types.Operator, ExportHelper):
    bl_idname = 'animation.bvhq'
    bl_label = 'Export BVHQ'
    bl_description = 'Export BVHQ'
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = '.bvhq'
    filter_glob: bpy.props.StringProperty(default='*.bvhq', options={'HIDDEN'})

    def execute(self, context: bpy.types.Context):
        if not self.filepath:
            return {'CANCELLED'}

        class Args(object):
            inputs = []
            output = self.filepath
            exec = None

        args = Args()
        e = BVHQExporter(args)
        e.convert()

        bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)  # re-open current file
        return {'FINISHED'}

    def invoke(self, context, event):
        return typing.cast(typing.Set[str], ExportHelper.invoke(self, context, event))

    def draw(self, context):
        pass


def export(export_op, context):
    export_op.layout.operator(
        GLTFExporterOperator.bl_idname,
        text='BVHQ using KITSUNETSUKI Asset Tools (.bvhq)')
