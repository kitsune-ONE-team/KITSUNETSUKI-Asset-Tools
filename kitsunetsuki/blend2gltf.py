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
        'input', type=str, help='Input .blend file path.')
    parser.add_argument(
        '-b', '--background', action='store_true', required=False,
        help="Blender's argument placeholder.")
    parser.add_argument(
        '-P', '--python', type=str, required=False,
        help="Blender's argument placeholder.")
    parser.add_argument(
        '-o', '--output', type=str, required=False,
        help='Output .gltf file path.')
    parser.add_argument(
        '-e', '--export', type=str, required=False, default='all',
        help='Export type: all/animation/collision.')
    parser.add_argument(
        '-r', '--render', type=str, required=False, default='default',
        help='Render type: default/rp.')
    parser.add_argument(
        '-x', '--exec', type=str, required=False,
        help='Internal script name to execute.')
    parser.add_argument(
        '-a', '--action', type=str, required=False,
        help='Action name to export.')
    parser.add_argument(
        '-sp', '--speed', type=float, required=False,
        help='Animations speed scale.')
    parser.add_argument(
        '-sc', '--scale', type=float, required=False,
        help='Geom scale.')
    parser.add_argument(
        '-m', '--merge', action='store_true',
        help='Merge objects and meshes inside the collection.')
    parser.add_argument(
        '-k', '--keep', action='store_true',
        help='Keep the original objects and meshes before merging.')
    parser.add_argument(
        '-z', '--z-up', action='store_true',
        help="Skip conversion and keep Blender's Z-Up world.")
    parser.add_argument(
        '-pf', '--pose-freeze', action='store_true',
        help="Freezes pose, bakes bone rotation and scale.")
    parser.add_argument(
        '-nuv', '--no-extra-uv', action='store_true',
        help="Don't export extra non-primary UV.")
    parser.add_argument(
        '-nmat', '--no-materials', action='store_true',
        help="Don't export materials (skips textures aswell).")
    parser.add_argument(
        '-ntex', '--no-textures', action='store_true',
        help="Don't export textures.")
    parser.add_argument(
        '-etex', '--empty-textures', action='store_true',
        help="Use placeholder images for empty texture slots.")
    parser.add_argument(
        '-sorg', '--set-origin', action='store_true',
        help="Set origin to center of bounds for collisions.")
    parser.add_argument(
        '-prim', '--split-primitives', action='store_true',
        help="Split primitives into separate vertex buffers.")
    parser.add_argument(
        '-nw', '--normalize-weights', action='store_true',
        help="Normalize vertex weights.")

    return parser.parse_args()


def main():
    args = parse_args()

    from kitsunetsuki.exporter.gltf import GLTFExporter

    e = GLTFExporter(args)
    out, buf = e.convert()

    if args.output:
        if args.output.endswith('.gltf'):
            buf.export(out, args.output.replace('.gltf', '.bin'))
            with open(args.output, 'w') as f:
                json.dump(out, f, indent=4)

        else:
            with open(args.output, 'wb') as f:
                chunk1 = buf.export(out)  # export buffer first because it updates gltf data
                chunk0 = json.dumps(out, indent=4).encode()  # export gltf data

                # write global headers
                f.write(b'glTF')  # header
                f.write(struct.pack('<I', 2))  # version
                size = (
                    4 + 4 + 4 +  # global headers
                    4 + 4 + len(chunk0) +  # chunk0 + headers
                    4 + 4 + len(chunk1))  # chunk1 + headers
                f.write(struct.pack('<I', size))  # full size

                # write chunk0 with headers
                f.write(struct.pack('<I', len(chunk0)))
                f.write(b'JSON')
                f.write(chunk0)

                # write chunk1 with headers
                f.write(struct.pack('<I', len(chunk1)))
                f.write(b'BIN\0')
                f.write(chunk1)

    else:
        buf.export(out)
        print(json.dumps(out, indent=4))


if __name__ == '__main__':
    main()
