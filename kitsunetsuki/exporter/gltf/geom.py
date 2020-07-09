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

import math

from kitsunetsuki.base.armature import get_armature
from kitsunetsuki.base.mesh import obj2mesh
from kitsunetsuki.base.objects import apply_modifiers, is_collision
from kitsunetsuki.base.matrices import (
    get_bone_matrix, get_object_matrix, get_inverse_bind_matrix,
    matrix_to_list, quat_to_list)

from . import spec


class GeomMixin(object):
    def _get_joints(self, gltf_node):
        results = {}

        for i, child_id in enumerate(gltf_node['joints']):
            child = self._root['nodes'][child_id]
            results[child['name']] = i

        return results

    def _make_primitive(self):
        gltf_primitive = {
            'attributes': {},
            'material': 0,
            'extra': {
                'highest_index': -1,
            },
        }

        channel = self._buffer.add_channel({
            'componentType': spec.TYPE_UNSIGNED_SHORT,
            'type': 'SCALAR',
            'extra': {
                'reference': 'indices',
            },
        })
        gltf_primitive['indices'] = channel['bufferView']

        channel = self._buffer.add_channel({
            'componentType': spec.TYPE_FLOAT,
            'type': 'VEC3',
            # 'max': [1] * 3,
            # 'min': [-1] * 3,
            'extra': {
                'reference': 'NORMAL',
            },
        })
        gltf_primitive['attributes']['NORMAL'] = channel['bufferView']

        channel = self._buffer.add_channel({
            'componentType': spec.TYPE_FLOAT,
            'type': 'VEC3',
            'extra': {
                'reference': 'POSITION',
            },
        })
        gltf_primitive['attributes']['POSITION'] = channel['bufferView']

        return gltf_primitive

    def make_geom(self, gltf_node, gltf_mesh, obj, can_merge=False):
        triangulate = True
        if self._geom_scale != 1:
            obj.scale.x = self._geom_scale
            obj.scale.y = self._geom_scale
            obj.scale.z = self._geom_scale
        apply_modifiers(obj, triangulate=triangulate)
        mesh = obj2mesh(obj, triangulate=triangulate)

        # get or create materials and textures
        gltf_materials = {}
        if not self._no_materials and not is_collision(obj):
            for material in mesh.materials.values():
                # material
                for i, child in enumerate(self._root['materials']):  # existing material
                    if child['name'] == material.name:
                        gltf_materials[material.name] = i
                        break
                else:  # new material
                    gltf_material = self.make_material(material)
                    self._root['materials'].append(gltf_material)
                    gltf_materials[material.name] = len(self._root['materials']) - 1

                # textures
                if not self._no_textures:
                    for type_, gltf_sampler, gltf_image in self.make_textures(material):
                        tname = gltf_image['name']
                        for i, child in enumerate(self._root['images']):  # existing texture
                            if child['name'] == tname:
                                texid = i
                                break
                        else:  # new texture
                            self._root['samplers'].append(gltf_sampler)
                            self._root['images'].append(gltf_image)

                            gltf_texture = {
                                'sampler': len(self._root['samplers']) - 1,
                                'source': len(self._root['images']) - 1,
                            }
                            self._root['textures'].append(gltf_texture)
                            texid = len(self._root['textures']) - 1

                        matid = gltf_materials[material.name]
                        if type(type_) == tuple and len(type_) == 2:
                            type_l1, type_l2 = type_
                            self._root['materials'][matid][type_l1][type_l2] = {'index': texid}
                        else:
                            self._root['materials'][matid][type_] = {'index': texid}

        # get primitives
        gltf_primitives = {}
        gltf_primitive_indices = {}
        if can_merge:
            for i, gltf_primitive in enumerate(gltf_mesh['primitives']):
                mname = None
                if 'material' in gltf_primitive:
                    matid = gltf_primitive['material']
                    mname = self._root['materials'][matid]['name']
                gltf_primitives[mname] = gltf_primitive
                gltf_primitive_indices[mname] = gltf_primitive['extra']['highest_index']

        # get armature and joints
        armature = get_armature(obj)
        max_joints = 0  # get max joints per vertex
        gltf_joints = {}
        if armature:
            max_joints = 1
            for polygon in mesh.polygons:
                for vertex_id in polygon.vertices:
                    vertex = mesh.vertices[vertex_id]
                    joints = 0
                    for vertex_group in vertex.groups:
                        obj_vertex_group = obj.vertex_groups[vertex_group.group]
                        if vertex_group.weight > 0:
                            joints += 1
                    max_joints = max(max_joints, joints)

            if 'skin' in gltf_node:
                gltf_skin = self._root['skins'][gltf_node['skin']]

                # for i, child in enumerate(self._root['skins']):
                #     if child['name'] == armature.name:
                #         gltf_joints = self._get_joints(child)
                #         break
                gltf_joints = self._get_joints(gltf_skin)

        # get max joint layers (4 bones per layer)
        max_joint_layers = math.ceil(max_joints / 4)
        # max_joint_layers = 1

        sharp_vertices = self.get_sharp_vertices(mesh)
        uv_tb = self.get_tangent_bitangent(mesh)
        gltf_vertices = {}
        obj_matrix = self._matrix @ get_object_matrix(obj, armature)

        for polygon in mesh.polygons:
            # <-- polygon
            material = None
            mname = None
            if not self._no_materials:
                try:
                    material = mesh.materials[polygon.material_index]
                    mname = material.name
                except IndexError:
                    pass

            # get or create primitive
            if mname in gltf_primitives:
                gltf_primitive = gltf_primitives[mname]
            else:
                gltf_primitive = self._make_primitive()
                gltf_primitives[mname] = gltf_primitive
                gltf_primitive_indices[mname] = -1
                gltf_mesh['primitives'].append(gltf_primitive)

            # set material
            if material and not self._no_materials and not is_collision(obj):
                if material.name in gltf_materials:
                    gltf_primitive['material'] = gltf_materials[mname]
            # else:
            #     gltf_primitive['material'] = 0

            # vertices
            for i, vertex_id in enumerate(polygon.vertices):
                # i is vertex counter inside a polygon
                # (0, 1, 2) for triangle
                # vertex_id is reusable id,
                # because multiple polygons can share the same vertices

                # <-- vertex
                vertex = mesh.vertices[vertex_id]
                use_smooth = (
                    polygon.use_smooth and
                    vertex_id not in sharp_vertices and
                    not is_collision(obj))

                # try to reuse shared vertices
                if (polygon.use_smooth and
                        vertex_id in gltf_vertices and
                        not is_collision(obj)):
                    shared = False
                    for gltf_vertex in gltf_vertices[vertex_id]:
                        loop_id = polygon.loop_indices[i]
                        gltf_vertex_uv = gltf_vertex[1]
                        if self.can_share_vertex(mesh, loop_id, gltf_vertex_uv):
                            self._buffer.write(
                                gltf_primitive['indices'], gltf_vertex[0])
                            shared = True
                            break
                    if shared:
                        continue

                # make new vertex data
                self.make_vertex(
                    obj_matrix, gltf_primitive, polygon, vertex,
                    use_smooth=use_smooth, can_merge=can_merge)

                # uv layers, active first
                active_uv = 0, 0
                if not is_collision(obj):
                    uv_layers = sorted(
                        mesh.uv_layers.items(), key=lambda x: not x[1].active)
                    for uv_id, (uv_name, uv_layer) in enumerate(uv_layers):
                        # <-- vertex uv
                        loop_id = polygon.loop_indices[i]
                        uv_loop = uv_layer.data[loop_id]

                        # not active layer and extra UV disabled
                        if not uv_layer.active and self._no_extra_uv:
                            continue

                        u, v = uv_loop.uv.to_2d()
                        if uv_layer.active:
                            active_uv = u, v
                        self._write_uv(gltf_primitive, uv_id, u, v)
                        if uv_name in uv_tb and uv_layer.active:
                            self._write_tbs(
                                obj_matrix, gltf_primitive, *uv_tb[uv_name][loop_id],
                                can_merge=can_merge)
                        # vertex uv -->

                # generate new ID, add vertex and save last ID
                gltf_primitive_indices[mname] += 1
                self._buffer.write(
                    gltf_primitive['indices'], gltf_primitive_indices[mname])
                gltf_primitive['extra']['highest_index'] = gltf_primitive_indices[mname]

                # save vertex data for sharing
                if vertex_id not in gltf_vertices:
                    gltf_vertices[vertex_id] = []
                gltf_vertices[vertex_id].append((
                    gltf_primitive_indices[mname], active_uv,
                ))

                # attach joints to vertex
                if gltf_joints:
                    joints_weights = []  # list of vec4
                    vertex_groups = reversed(sorted(
                        vertex.groups, key=lambda vg: vg.weight))
                    for vertex_group in vertex_groups:
                        obj_vertex_group = obj.vertex_groups[vertex_group.group]
                        if (obj_vertex_group.name in gltf_joints and
                                vertex_group.weight > 0):
                            if not joints_weights or len(joints_weights[-1]) >= 4:
                                if len(joints_weights) >= max_joint_layers:
                                    break
                                joints_weights.append([])
                            joint_id = gltf_joints[obj_vertex_group.name]
                            joint_weight = joint_id, vertex_group.weight
                            joints_weights[-1].append(joint_weight)  # push to vec4

                    # padding
                    if joints_weights:
                        while len(joints_weights[-1]) < 4:  # up to vec4
                            joints_weights[-1].append((0, 0))  # push to vec4
                    while len(joints_weights) < max_joint_layers:  # up to max joints
                        vec4 = [(0, 0)] * 4  # make empty vec4
                        joints_weights.append(vec4)

                    assert len(joints_weights) == max_joint_layers
                    self._write_joints_weights(
                        gltf_primitive, len(tuple(gltf_joints.keys())), joints_weights)

                # vertex -->
            # polygon -->
