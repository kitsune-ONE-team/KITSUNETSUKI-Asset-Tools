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

from kitsunetsuki.base.matrices import get_object_matrix

from . import spec


class VertexMixin(object):
    def make_vertex(self, obj_matrix, gltf_primitive, polygon, vertex,
                    use_smooth=False, can_merge=False):
        if can_merge:
            co = obj_matrix @ vertex.co
        else:
            co = vertex.co

        self._buffer.write(
            gltf_primitive['attributes']['POSITION'], *tuple(co))

        if use_smooth:
            if can_merge:
                normal = obj_matrix.to_euler().to_matrix() @ vertex.normal
            else:
                normal = vertex.normal
        else:
            if can_merge:
                normal = obj_matrix.to_euler().to_matrix() @ polygon.normal
            else:
                normal = polygon.normal

        self._buffer.write(
            gltf_primitive['attributes']['NORMAL'], *tuple(normal))

    def _write_uv(self, gltf_primitive, uv_id, u, v):
        texcoord = 'TEXCOORD_{}'.format(uv_id)
        if texcoord not in gltf_primitive['attributes']:
            channel = self._buffer.add_channel({
                'componentType': spec.TYPE_FLOAT,
                'type': 'VEC2',
                'extra': {
                    'reference': texcoord,
                },
            })
            gltf_primitive['attributes'][texcoord] = channel['bufferView']

        self._buffer.write(
            gltf_primitive['attributes'][texcoord], u, 1 - v)

    def _write_tbs(self, obj_matrix, gltf_primitive, t, b, s, can_merge=False):
        if 'TANGENT' not in gltf_primitive['attributes']:
            channel = self._buffer.add_channel({
                'componentType': spec.TYPE_FLOAT,
                'type': 'VEC4',
                'extra': {
                    'reference': 'TANGENT',
                },
            })
            gltf_primitive['attributes']['TANGENT'] = channel['bufferView']

        if can_merge:
            x, y, z = obj_matrix @ t
        else:
            x, y, z = t

        self._buffer.write(
            gltf_primitive['attributes']['TANGENT'], x, y, z, s)

    def _write_joints_weights(self, gltf_primitive, joints_num, joints_weights):
        for i, joint_weight in enumerate(joints_weights):
            joints = 'JOINTS_{}'.format(i)
            if joints not in gltf_primitive['attributes']:
                if joints_num > 255:
                    ctype = spec.TYPE_UNSIGNED_SHORT
                else:
                    ctype = spec.TYPE_UNSIGNED_BYTE
                channel = self._buffer.add_channel({
                    'componentType': ctype,
                    'type': 'VEC4',
                    'extra': {
                        'reference': joints,
                    },
                })
                gltf_primitive['attributes'][joints] = channel['bufferView']

            # write 4 joints
            keys = tuple(zip(*joint_weight))[0]
            assert len(keys) == 4
            self._buffer.write(gltf_primitive['attributes'][joints], *keys)

            weights = 'WEIGHTS_{}'.format(i)
            if weights not in gltf_primitive['attributes']:
                channel = self._buffer.add_channel({
                    'componentType': spec.TYPE_FLOAT,
                    'type': 'VEC4',
                    'extra': {
                        'reference': weights,
                    },
                })
                gltf_primitive['attributes'][weights] = channel['bufferView']

            # write 4 weights
            values = tuple(zip(*joint_weight))[1]
            assert len(values) == 4
            self._buffer.write(gltf_primitive['attributes'][weights], *values)
