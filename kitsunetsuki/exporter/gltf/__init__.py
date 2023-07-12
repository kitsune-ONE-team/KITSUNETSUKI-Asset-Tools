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
import os
import typing
import mathutils

from pathlib import Path

from bpy_extras.io_utils import ExportHelper

from kitsunetsuki.exporter.base import Exporter
from kitsunetsuki.base.context import Mode
from kitsunetsuki.base.objects import (
    apply_modifiers, is_collision, make_local, get_object_properties)
from kitsunetsuki.base.mesh import obj2mesh

from io_scene_gltf2.blender.com import gltf2_blender_json
from io_scene_gltf2.blender.exp import gltf2_blender_gather
from io_scene_gltf2.blender.exp import gltf2_blender_gltf2_exporter
from io_scene_gltf2.io.exp import gltf2_io_export


class JSONEncoder(gltf2_blender_json.BlenderJSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs.pop('indent', None)
        super().__init__(*args, **kwargs, indent=4)


def fix_json(obj):
    fixed = obj
    if isinstance(obj, dict):
        fixed = {}
        for key, value in obj.items():
            if key == 'extras' and value is not None:
                fixed[key] = value
                continue
            if value is None:
                continue
            if key != 'KHR_materials_unlit':
                if isinstance(value, (dict, list)) and not value:
                    continue
            fixed[key] = fix_json(value)
    elif isinstance(obj, list):
        fixed = []
        for value in obj:
            fixed.append(fix_json(value))
    elif isinstance(obj, float):
        if int(obj) == obj:
            return int(obj)
    return fixed


class GLTFExporter(Exporter):
    def __init__(self, args):
        super().__init__(args)
        self._z_up = hasattr(args, 'z_up') and args.z_up
        self._pose_freeze = hasattr(args, 'pose_freeze') and args.pose_freeze
        self._merge = args.merge
        self._export_type = args.export
        self._output = args.output or args.inputs[0].replace('.blend', '.gltf')
        self._bone_tails = {}

    def _export(self, export_settings):
        exporter = gltf2_blender_gltf2_exporter.GlTF2Exporter(export_settings)

        active_scene_idx, scenes, animations = gltf2_blender_gather.gather_gltf2(export_settings)
        unused_skins = export_settings['vtree'].get_unused_skins()
        for idx, scene in enumerate(scenes):
            exporter.add_scene(scene, idx == active_scene_idx)
        for animation in animations:
            exporter.add_animation(animation)
        exporter.traverse_unused_skins(unused_skins)

        buf = bytes()
        dirname = os.path.dirname(self._output) + os.sep
        if self._output.endswith('.gltf'):
            filename = os.path.basename(self._output.replace('.gltf', '.bin'))
            exporter.finalize_buffer(dirname, filename)
        else:
            buf = exporter.finalize_buffer(dirname, is_glb=True)

        exporter.finalize_images()
        exporter.traverse_extensions()
        data = fix_json(exporter.glTF.to_dict())

        return data, buf

    def _process_data(self, data):
        data = copy.copy(data)

        if self._z_up:
            if 'extensionsUsed' not in data:
                data['extensionsUsed'] = []
            data['extensionsUsed'].append('BP_zup')

            outpath = Path(os.path.dirname(self._output)).resolve().absolute()
            for image in data.get('images') or []:
                imgpath = Path(os.path.join(outpath, image['uri'])).resolve().absolute()
                image['uri'] = os.path.relpath(imgpath, outpath)

        return data

    def gather_skin_hook(self, skin, blender_armature_object, export_settings):
        skin.extras = skin.extras or {}
        skin.extras['jointNames'] = [joint.name for joint in skin.joints]

    def gather_mesh_hook(
            self, mesh, blender_mesh, blender_object, vertex_groups, modifiers,
            skip_filter, materials, export_settings):
        mesh.extras = mesh.extras or {}
        mesh.extras['texcoordsNames'] = [uv.name for uv in blender_mesh.uv_layers]

    def gather_node_hook(self, node, blender_object, export_settings):
        if is_collision(blender_object):
            bbox = [
                blender_object.dimensions[i] /
                blender_object.matrix_local.to_scale()[i]
                for i in range(3)
            ]

            shape = {
                'shapeType': blender_object.rigid_body.collision_shape,
                'boundingBox': bbox,
            }
            if blender_object.rigid_body.collision_shape == 'MESH':
                shape['mesh'] = node.mesh

            collision = {
                'collisionShapes': [shape],
                'static': blender_object.rigid_body.type == 'PASSIVE' or
                    not blender_object.rigid_body.enabled,
                # don't actually collide (ghost)
                'intangible': not blender_object.collision or
                    not blender_object.collision.use,
            }

            node.extensions = node.extensions or {}
            node.extensions['BLENDER_physics'] = collision

        node.extras = node.extras or {}
        node.extras.update(get_object_properties(blender_object))

    def gather_joint_hook(self, node, blender_bone, export_settings):
        node.extras = node.extras or {}

        if blender_bone.name in self._bone_tails:
            tail = self._bone_tails[blender_bone.name]
        else:
            tail = mathutils.Matrix.Translation(blender_bone.tail)

        node.extras['tail'] = {
            'translation': list(tail.to_translation()),
        }

    @property
    def export_settings(self):
        return {
            'gltf_filepath': self._output,
            'gltf_filedirectory': os.path.dirname(self._output),
            'gltf_texturedirectory': os.path.dirname(self._output),
            'gltf_keep_original_textures': True,

            'gltf_format': 'GLTF' if self._output.endswith('.gltf') else 'GLB',
            'gltf_image_format': 'AUTO',
            'gltf_copyright': os.getenv('USERNAME'),
            'gltf_texcoords': True,
            'gltf_normals': True,
            'gltf_tangents': True,
            'gltf_loose_edges': False,
            'gltf_loose_points': False,

            'gltf_draco_mesh_compression': False,

            'gltf_materials': 'EXPORT',
            'gltf_colors': True,
            'gltf_attributes': True,
            'gltf_cameras': False,

            'gltf_original_specular': False,

            'gltf_visible': True,  # export visible objects only
            'gltf_renderable': False,

            'gltf_active_collection': False,
            'gltf_active_scene': True,

            'gltf_selected': False,
            'gltf_extras': True,
            'gltf_yup': not self._z_up,
            'gltf_apply': True,
            'gltf_current_frame': 0,
            'gltf_animations': True,
            'gltf_def_bones': True,
            'gltf_frame_range': True,
            'gltf_force_sampling': True,
            'gltf_nla_strips': False,
            'gltf_nla_strips_merged_animation_name': 'GLTF_ANIMATION',
            'gltf_optimize_animation': False,
            'gltf_export_anim_single_armature': True,
            'gltf_rest_position_armature': False,
            'gltf_flatten_bones_hierarchy': False,
            'gltf_animation_mode': 'ACTIONS',
            'gltf_morph_anim': True,
            'gltf_bake_animation': True,
            'gltf_negative_frames': 'SLIDE',
            'gltf_export_reset_pose_bones': True,
            'gltf_skins': True,
            'gltf_all_vertex_influences': False,  # limit to 4 bones and normalize
            'gltf_frame_step': 1,
            'gltf_morph': True,
            'gltf_morph_normal': False,
            'gltf_morph_tangent': False,

            'gltf_lights': True,
            'gltf_lighting_mode': 'RAW',

            'gltf_binary': bytearray(),
            'gltf_binaryfilename': os.path.basename(self._output.replace('.gltf', '.bin')),
            # 'gltf_embed_buffers': not self._output.endswith('.gltf'),

            'gltf_user_extensions': [self],
            'post_export_callbacks': [],
            'pre_export_callbacks': [],
        }

    def convert(self):
        if self._script_names:
            for script_name in self._script_names:
                if script_name:
                    self._execute_script(script_name)

        if bpy.context.active_object is not None:
            if bpy.context.active_object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

        for c in bpy.data.collections:
            # skip special collections
            if c.name in ('RigidBodyConstraints', 'RigidBodyWorld'):
                continue

            if c.hide_viewport:
                for obj in c.objects:
                    obj.hide_set(True)
                continue

            objects = []
            objects_merge = []
            for obj in c.objects:
                if obj.hide_viewport:
                    obj.hide_set(True)
                    continue

                if self._export_type == 'collision':
                    if obj.type == 'MESH' and not is_collision(obj):
                        obj.hide_set(True)
                        continue

                if obj.hide_get():
                    continue

                if obj.type == 'ARMATURE':
                    if self._pose_freeze:
                        bpy.context.view_layer.objects.active = obj

                        with Mode('EDIT'):
                            for bone_name, bone in obj.data.edit_bones.items():
                                self._bone_tails[bone_name] = mathutils.Matrix.Translation(
                                    bone.tail - bone.head)
                                if not self._z_up:
                                    self._bone_tails[bone_name] = mathutils.Matrix((
                                        (1.0, 0.0, 0.0),
                                        (0.0, 0.0, 1.0),
                                        (0.0, -1.0, 0.0),
                                    )).to_4x4() @ self._bone_tails[bone_name] @ mathutils.Matrix((
                                        (1.0, 0.0, 0.0),
                                        (0.0, 0.0, -1.0),
                                        (0.0, 1.0, 0.0),
                                    )).to_4x4()

                        # disconnect all bones
                        with Mode('EDIT'):
                            for bone_name, bone in obj.data.edit_bones.items():
                                bone.use_connect = False

                        # reset bones rotation
                        with Mode('EDIT'):
                            for bone_name, bone in obj.data.edit_bones.items():
                                bone.roll = 0
                                bone.length = 10
                                # bone.tail = bone.head + mathutils.Vector((0, bone.length, 0))
                                bone.tail = bone.head + mathutils.Vector((0, 0, bone.length))
                                bone.roll = 0

                    continue

                objects.append(obj)
                if self._can_merge(obj):
                    objects_merge.append(obj)

            if not objects:
                continue

            for obj in objects:
                make_local(obj)
                apply_modifiers(obj)

            if self._merge and objects_merge:
                bpy.ops.object.select_all(action='DESELECT')
                for obj in objects_merge:
                    obj.select_set(state=True)
                bpy.context.view_layer.objects.active = objects_merge[0]

                if len(objects_merge) > 1:
                    context = {
                        'active_object': objects_merge[0],
                        'selected_objects': objects_merge,
                        'selected_editable_objects': objects_merge,
                    }
                    bpy.ops.object.join(context)

                bpy.ops.object.select_all(action='DESELECT')
                obj = bpy.context.view_layer.objects.active
                bpy.context.view_layer.objects.active = None
                obj.name = c.name
                # mesh = obj2mesh(obj)
                # depsgraph = bpy.context.evaluated_depsgraph_get()
                # obj.data = bpy.data.meshes.new_from_object(
                #     obj.evaluated_get(depsgraph),
                #     preserve_all_data_layers=True, depsgraph=depsgraph)
                obj.data.name = c.name

        if self._post_script_names:
            for script_name in self._post_script_names:
                if script_name:
                    self._execute_script(script_name)

        frame = bpy.context.scene.frame_current

        bpy.context.scene.frame_set(0)
        data, buf = self._export(self.export_settings)
        data = self._process_data(data)
        gltf2_io_export.save_gltf(data, self.export_settings, JSONEncoder, buf)

        bpy.context.scene.frame_set(int(frame))


class GLTFExporterOperator(bpy.types.Operator, ExportHelper):
    bl_idname = 'scene.gltf'
    bl_label = 'Export glTF'
    bl_description = 'Export glTF'
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = '.gltf'
    filter_glob: bpy.props.StringProperty(default='*.gltf', options={'HIDDEN'})

    def execute(self, context: bpy.types.Context):
        if not self.filepath:
            return {'CANCELLED'}

        class Args(object):
            inputs = []
            output = self.filepath
            exec = None

        args = Args()
        e = GLTFExporter(args)
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
        text='glTF using KITSUNETSUKI Asset Tools (.gltf)')
