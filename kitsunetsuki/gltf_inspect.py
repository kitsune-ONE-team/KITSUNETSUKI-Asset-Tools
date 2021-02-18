#!/usr/bin/env python3
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

import argparse
import json
import struct


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'input', type=str, help='Input .gltf file path.')

    return parser.parse_args()


def print_node(gltf_data, node_id, joints=None, indent=1, parent_node=None):
    gltf_node = gltf_data['nodes'][node_id]

    type_ = 'N'
    extra = ''

    matrix = ''
    if 'rotation' in gltf_node:
        matrix += 'R'
    if 'scale' in gltf_node:
        matrix += 'S'
    if 'translation' in gltf_node:
        matrix += 'T'

    if matrix:
        extra += ' <{}>'.format(matrix)

    if node_id in (joints or []):
        type_ = 'J'  # joint/bone

    elif 'skin' in gltf_node:
        refs = []

        if 'skin' in gltf_node:
            skin_id = gltf_node['skin']
            gltf_skin = gltf_data['skins'][skin_id]
            v = '{} ({} joints)'.format(
                gltf_skin['name'],
                len(gltf_skin['joints']))
            refs.append(('skin', v))

        if 'mesh' in gltf_node:
            mesh_id = gltf_node['mesh']
            gltf_mesh = gltf_data['meshes'][mesh_id]
            refs.append(('mesh', gltf_mesh['name']))

        extra += ' {' + ', '.join(['{}: {}'.format(*i) for i in refs]) + '}'

    if 'VRM' in gltf_data['extensions']:
        vrm_bones = gltf_data['extensions']['VRM']['humanoid']['humanBones']
        for vrm_bone in vrm_bones:
            if node_id == vrm_bone['node']:
                extra += ' {VRM: %s}' % vrm_bone['bone']

    for child_node_id in gltf_node.get('children', []):
        child_gltf_node = gltf_data['nodes'][child_node_id]
        if 'skin' in child_gltf_node:
            type_ = 'S'  # skeleton/armature
            skin_id = child_gltf_node['skin']
            gltf_skin = gltf_data['skins'][skin_id]
            joints = gltf_skin['joints']

    is_ = ''
    for i in range(indent):
        if i < indent - 1:
            is_ += '  |'
        else:
            is_ += '  +'
    print('{} [{}] {}{}'.format(
        is_, type_, gltf_node['name'], extra))

    for child_node_id in gltf_node.get('children', []):
        print_node(
            gltf_data, child_node_id,
            joints=joints, indent=indent + 1, parent_node=gltf_node)


def print_scene(gltf_data, scene_id):
    gltf_scene = gltf_data['scenes'][scene_id]
    print(' [R] {}'.format(gltf_scene['name']))

    for node_id in gltf_scene['nodes']:
        print_node(gltf_data, node_id)


def print_anim(gltf_data, gltf_anim):
    extra = ''
    input_id = gltf_anim['samplers'][0]['input']
    extra += '{} frames'.format(gltf_data['accessors'][input_id]['count'])
    if extra:
        extra = ' {' + extra + '}'

    print(' [A] {}{}'.format(gltf_anim['name'], extra))


def main():
    args = parse_args()
    gltf_data = {
        'scene': {},
    }

    if args.input.endswith('.glb') or args.input.endswith('.vrm'):
        with open(args.input, 'rb') as f:
            assert f.read(4) == b'glTF'  # header
            assert struct.unpack('<I', f.read(4))[0] == 2  # version
            full_size = struct.unpack('<I', f.read(4))

            chunk_type = None
            chunk_data = None
            while True:
                chunk_size = struct.unpack('<I', f.read(4))[0]
                chunk_type = f.read(4)
                chunk_data = f.read(chunk_size)
                if chunk_type == b'JSON':
                    break

            if chunk_type == b'JSON':
                gltf_data = json.loads(chunk_data)

    else:
        with open(args.input, 'r') as f:
            gltf_data = json.load(f)

    print_scene(gltf_data, gltf_data['scene'])

    for gltf_anim in (gltf_data.get('animations') or []):
        print_anim(gltf_data, gltf_anim)


if __name__ == '__main__':
    main()
