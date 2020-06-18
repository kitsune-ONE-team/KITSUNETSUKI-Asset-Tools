# Copyright (c) 2020 kitsune.ONE team.

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
import collections
import copy
import math

from kitsunetsuki.base.matrices import get_bone_matrix, quat_to_list

from . import spec


class AnimationMixin(object):
    def _make_sampler(self, path, input_id):
        gltf_sampler = {
            'interpolation': 'LINEAR',
            'input': input_id,
        }

        # transforms
        channel = self._buffer.add_channel({
            'componentType': spec.TYPE_FLOAT,
            'type': 'VEC4' if path == 'rotation' else 'VEC3',
            'extra': {
                'reference': path,
            },
        })
        gltf_sampler['output'] = channel['bufferView']

        return gltf_sampler

    def make_action(self, node, armature):
        gltf_armature = self.make_armature(node, armature)
        self._setup_node(gltf_armature, armature)
        self._add_child(self._root, gltf_armature)

        gltf_skin = self._make_skin(armature, armature)
        gltf_node = {
            'name': 'ARMATURE',
            'children': [],
            'skin': len(self._root['skins']) - 1,
        }
        # self._setup_node(gltf_node, armature)
        self._add_child(gltf_armature, gltf_node)

        # <-- animation
        gltf_animation = {
            'name': self._action or 'GLTF_ANIMATION',
            'channels': [],
            'samplers': [],
        }

        # time or animation frame
        channel = self._buffer.add_channel({
            'componentType': spec.TYPE_FLOAT,
            'type': 'SCALAR',
            'extra': {
                'reference': 'input',
            },
        })
        input_id = channel['bufferView']

        # setup bones
        gltf_channels = {}
        gltf_samplers = []
        for bone_name, bone in armature.data.bones.items():
            gltf_joint = None
            for i, child in enumerate(self._root['nodes']):
                if child['name'] == bone_name:
                    gltf_joint = i
                    break

            gltf_target = {}
            if gltf_joint is not None:
                gltf_target['node'] = gltf_joint

            for path in ('rotation', 'scale', 'translation'):
                gltf_samplers.append(self._make_sampler(path, input_id))

                gltf_channel = {
                    'sampler': len(gltf_samplers) - 1,
                    'target': copy.copy(gltf_target),
                }
                gltf_channel['target']['path'] = path
                gltf_channels['{}/{}'.format(bone_name, path)] = gltf_channel

        gltf_animation['channels'] = list(gltf_channels.values())
        gltf_animation['samplers'] = gltf_samplers

        # set animation data
        frame_start = bpy.context.scene.frame_start
        frame_end = bpy.context.scene.frame_end
        if self._action:
            if self._action in bpy.data.actions:
                action = bpy.data.actions[self._action]
                frame_start, frame_end = action.frame_range

        frame = float(frame_start)
        frame_int = None
        input_ = 0
        while frame <= frame_end:
            # switch frame
            if frame_int != math.floor(frame):
                frame_int = math.floor(frame)
                bpy.context.scene.frame_current = frame_int
                bpy.context.scene.frame_set(frame_int)

            if isinstance(self._speed_scale, collections.Callable):
                speed_scale = self._speed_scale(frame_int)
            else:
                speed_scale = self._speed_scale

            # switch subframe
            if speed_scale != 1:
                bpy.context.scene.frame_subframe = frame - frame_int

            # write bone matrices
            for bone_name, bone in armature.pose.bones.items():
                bone_matrix = get_bone_matrix(bone, armature)

                rotation = quat_to_list(bone_matrix.to_quaternion())
                scale = list(bone_matrix.to_scale())
                translation = list(bone_matrix.to_translation())

                gltf_channel = gltf_channels['{}/{}'.format(bone_name, 'rotation')]
                gltf_sampler = gltf_samplers[gltf_channel['sampler']]
                self._buffer.write(gltf_sampler['output'], *rotation)

                gltf_channel = gltf_channels['{}/{}'.format(bone_name, 'scale')]
                gltf_sampler = gltf_samplers[gltf_channel['sampler']]
                self._buffer.write(gltf_sampler['output'], *scale)

                gltf_channel = gltf_channels['{}/{}'.format(bone_name, 'translation')]
                gltf_sampler = gltf_samplers[gltf_channel['sampler']]
                self._buffer.write(gltf_sampler['output'], *translation)

                self._buffer.write(gltf_sampler['input'], input_)

            # advance to the next frame
            frame += speed_scale
            input_ += 1

        # animation -->

        self._root['animations'].append(gltf_animation)
