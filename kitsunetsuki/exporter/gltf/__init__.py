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
import json
import math
import mathutils  # make sure to "import bpy" before

from kitsunetsuki.base.armature import get_armature
from kitsunetsuki.base.collections import get_object_collection
from kitsunetsuki.base.matrices import (
    get_bone_matrix, get_object_matrix, get_inverse_bind_matrix,
    matrix_to_list, quat_to_list)
from kitsunetsuki.base.objects import (
    is_collision, is_object_visible, get_object_properties)

from kitsunetsuki.exporter.base import Exporter

from . import spec
from .buffer import GLTFBuffer
from .animation import AnimationMixin
from .geom import GeomMixin
from .material import MaterialMixin
from .vertex import VertexMixin
from .texture import TextureMixin


class GLTFExporter(AnimationMixin, GeomMixin, MaterialMixin,
                   VertexMixin, TextureMixin, Exporter):
    """
    BLEND to GLTF converter.
    """
    z_up = True

    def __init__(self, args):
        super().__init__(args)
        self._output = args.output or args.input.replace('.blend', '.gltf')

        if self.z_up:
            self._matrix = mathutils.Matrix((
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
                (0.0, 0.0, 1.0),
            )).to_4x4()
        else:
            # self._matrix = bpy_extras.io_utils.axis_conversion(
            #     to_forward='Z', to_up='Y').to_4x4()
            self._matrix = mathutils.Matrix((
                (-1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0),
                (0.0, 1.0, 0.0),
            )).to_4x4()

    def make_root_node(self):
        gltf_node = {
            'asset': {
                'generator': (
                    'KITSUNETSUKI Asset Tools by kitsune.ONE - '
                    'https://github.com/kitsune-ONE-team/KITSUNETSUKI-Asset-Tools'),
                'version': '2.0',
            },

            'extensions': {
                # 'BP_physics_engine': {'engine': 'bullet'},
            },
            'extensionsUsed': [],

            'scene': 0,
            'scenes': [{
                'name': 'Scene',
                'nodes': [],
            }],

            'nodes': [],
            'meshes': [],
            'materials': [{
                'name': 'GLTF_DEFAULT_MATERIAL',  # skips panda warnings
            }],
            'animations': [],
            'skins': [],

            'textures': [],  # links to samplers-images pair
            'samplers': [],
            'images': [],

            'accessors': [],
            'bufferViews': [],
            'buffers': [],
        }

        if self.z_up:
            gltf_node['extensionsUsed'].append('BP_zup')

        return gltf_node

    def _add_child(self, parent_node, child_node):
        self._root['nodes'].append(child_node)
        node_id = len(self._root['nodes']) - 1
        if 'scenes' in parent_node:
            self._root['scenes'][0]['nodes'].append(node_id)
        else:
            parent_node['children'].append(node_id)

    def _setup_node(self, node, obj=None, can_merge=False):
        if obj is None:
            return

        armature = get_armature(obj)
        obj_matrix = get_object_matrix(obj, armature=armature)

        # get custom object properties
        obj_props = get_object_properties(obj)

        if not can_merge and not armature:
            if self._geom_scale == 1:
                node.update({
                    'rotation': quat_to_list(obj_matrix.to_quaternion()),
                    'scale': list(obj_matrix.to_scale()),
                    'translation': list(obj_matrix.to_translation()),
                })
            else:
                x, y, z = list(obj_matrix.to_translation())
                x *= self._geom_scale
                y *= self._geom_scale
                z *= self._geom_scale
                node.update({
                    'rotation': quat_to_list(obj_matrix.to_quaternion()),
                    'scale': list(obj_matrix.to_scale()),
                    'translation': [x, y, z],
                })

        # setup collisions
        if not can_merge and is_collision(obj) and obj_props.get('type') != 'Portal':
            collision = {}
            node['extensions'] = {
                'BLENDER_physics': collision,
            }

            # collision shape
            shape = {
                'shapeType': obj.rigid_body.collision_shape,
                'boundingBox': [
                    obj.dimensions[i] / obj_matrix.to_scale()[i]
                    for i in range(3)
                ],
            }
            if obj.rigid_body.collision_shape == 'MESH':
                shape['mesh'] = node.pop('mesh')

            collision['collisionShapes'] = [shape]
            collision['static'] = obj.rigid_body.type == 'PASSIVE'

            # don't actually collide (ghost)
            if (not obj.collision or not obj.collision.use):
                collision['intangible'] = True

        # setup custom properties with tags
        if (obj_props or can_merge) and 'extras' not in node:
            node['extras'] = {}

        for k, v in obj_props.items():
            if node['extras'].get(k):  # tag exists
                tag = node['extras'].get(k)

            if type(v) in (tuple, list, dict):
                tag = json.dumps(v)
            else:
                tag = '{}'.format(v)

            node['extras'][k] = tag

        if can_merge and 'type' not in obj_props:
            node['extras']['type'] = 'Merged'

    def make_empty(self, parent_node, obj):
        gltf_node = {
            'name': obj.name,
            'children': [],
        }

        self._setup_node(gltf_node, obj)
        self._add_child(parent_node, gltf_node)

        return gltf_node

    def make_armature(self, parent_node, armature):
        gltf_node = {
            'name': armature.name,
            'children': [],
        }

        gltf_joints = {}

        for bone_name, bone in armature.data.bones.items():
            bone_matrix = get_bone_matrix(bone, armature)

            gltf_joint = {
                'name': bone_name,
                'children': [],
                'rotation': quat_to_list(bone_matrix.to_quaternion()),
                'scale': list(bone_matrix.to_scale()),
                'translation': list(bone_matrix.to_translation()),
            }

            if bone.parent:
                self._add_child(gltf_joints[bone.parent.name], gltf_joint)
            else:
                self._add_child(gltf_node, gltf_joint)

            gltf_joints[bone_name] = gltf_joint

        self._setup_node(gltf_node, armature)
        self._add_child(parent_node, gltf_node)

        return gltf_node

    def _make_skin(self, obj, armature):
        gltf_armature_id = None
        for i, child in enumerate(self._root['nodes']):
            if child['name'] == armature.name:
                gltf_armature_id = i
                break
        else:
            return

        channel = self._buffer.add_channel({
            'componentType': spec.TYPE_FLOAT,
            'type': 'MAT4',
            'extra': {
                'reference': 'inverseBindMatrices',
            },
        })

        gltf_skin = {
            'name': '{}_{}'.format(obj.name, armature.name),
            'joints': [],
            # 'skeleton': gltf_armature_id,
            'inverseBindMatrices': channel['bufferView'],
        }
        self._root['skins'].append(gltf_skin)

        for bone_name, bone in armature.data.bones.items():
            gltf_joint_id = None
            for i, child in enumerate(self._root['nodes']):
                if child['name'] == bone_name:
                    gltf_joint_id = i
                    break
            else:
                continue

            ib_matrix = get_inverse_bind_matrix(bone, armature)
            self._buffer.write(
                gltf_skin['inverseBindMatrices'],
                *matrix_to_list(ib_matrix))

            gltf_skin['joints'].append(gltf_joint_id)

        return gltf_skin

    def _make_node_mesh(self, parent_node, name, obj=None, can_merge=False):
        gltf_node = {
            'name': name,
            'children': [],
        }

        gltf_mesh = None
        need_mesh = False
        if can_merge:
            need_mesh = True
        else:
            if obj.rigid_body is None:
                need_mesh = True
            elif obj.rigid_body.collision_shape == 'MESH':
                need_mesh = True

        if need_mesh:
            gltf_mesh = {
                'name': name,
                'primitives': [],
            }
            self._root['meshes'].append(gltf_mesh)
            gltf_node['mesh'] = len(self._root['meshes']) - 1

        armature = obj and get_armature(obj)
        if armature:
            gltf_skin = self._make_skin(obj, armature)
            if gltf_skin:
                gltf_node['skin'] = len(self._root['skins']) - 1

        self._setup_node(gltf_node, obj, can_merge=can_merge)
        self._add_child(parent_node, gltf_node)

        return gltf_node, gltf_mesh

    def make_mesh(self, parent_node, obj):
        gltf_node = None

        # merged nodes
        if self.can_merge(obj):
            collection = get_object_collection(obj)

            for child in self._root['nodes']:
                if child['name'] == collection.name:
                    gltf_node = child

                    mesh_id = gltf_node['mesh']
                    gltf_mesh = self._root['meshes'][mesh_id]
                    break
            else:
                gltf_node, gltf_mesh = self._make_node_mesh(
                    parent_node, collection.name, obj, can_merge=True)

            if gltf_mesh:
                self.make_geom(gltf_node, gltf_mesh, obj, can_merge=True)

        # separate nodes
        if not self.can_merge(obj) or self._keep:
            obj_props = get_object_properties(obj)
            if obj_props.get('type') == 'Portal':
                vertices = [list(vertex.co) for vertex in obj.data.vertices]
                gltf_node = {
                    'name': obj.name,
                    'extras': {'vertices': json.dumps(vertices)},
                }
                self._setup_node(gltf_node, obj, can_merge=False)
                self._add_child(parent_node, gltf_node)
                return gltf_node

            gltf_node, gltf_mesh = self._make_node_mesh(
                parent_node, obj.name, obj, can_merge=False)

            if gltf_mesh:
                self.make_geom(gltf_node, gltf_mesh, obj, can_merge=False)

        return gltf_node

    def make_light(self, parent_node, obj):
        LIGHT_TYPES = {
            'POINT': 'PointLight',
            'SPOT': 'SpotLight',
        }

        gltf_light = {
            'name': obj.name,
            'children': [],
            'extras': {
                'type': 'Light',
                'light': LIGHT_TYPES[obj.data.type],
                'color': json.dumps(tuple(obj.data.color)),
                'scale': json.dumps(tuple(obj.scale)),
                'energy': '{:.3f}'.format(obj.data.energy),
                'far': '{:.3f}'.format(obj.data.shadow_soft_size),
            },
        }

        if obj.data.type == 'SPOT':
            gltf_light['extras']['fov'] = '{:.3f}'.format(
                math.degrees(obj.data.spot_size))

        self._setup_node(gltf_light, obj)
        self._add_child(parent_node, gltf_light)

        return gltf_light

    def convert(self):
        self._buffer = GLTFBuffer(self._output)
        root = super().convert()
        return root, self._buffer
