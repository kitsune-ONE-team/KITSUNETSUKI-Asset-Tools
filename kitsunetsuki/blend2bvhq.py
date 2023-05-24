#!/usr/bin/env python3
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

import argparse
import json
import struct

from . import bl_info


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'inputs', type=str, help='Input .blend file path.', nargs='*')
    parser.add_argument(
        '-b', '--background', action='store_true', required=False,
        help="Blender's argument placeholder.")
    parser.add_argument(
        '-P', '--python', type=str, required=False,
        help="Blender's argument placeholder.")
    parser.add_argument(
        '-o', '--output', type=str, required=False,
        help='Output .bvhq file path.')
    parser.add_argument(
        '-x', '--exec', type=str, required=False,
        help='Internal script name to execute.')
    parser.add_argument(
        '-xp', '--exec-post', type=str, required=False,
        help='Internal script name to execute in the post processing stage.')
    parser.add_argument(
        '-a', '--action', type=str, required=False,
        help='Action name to export.')
    parser.add_argument(
        '-sp', '--speed', type=float, required=False,
        help='Animations speed scale.')
    parser.add_argument(
        '-sc', '--scale', type=float, required=False,
        help='Geom scale.')

    return parser.parse_args()


def main():
    args = parse_args()

    from kitsunetsuki.exporter.bvhq import BVHQExporter

    e = BVHQExporter(args)
    r = e.convert()


def register(init_version):
    import bpy

    version = bl_info['version']
    if init_version != version:
        raise Exception(f"Version mismatch: {init_version} != {version}")

    from kitsunetsuki.exporter.bvhq import BVHQExporterOperator, export
    bpy.utils.register_class(BVHQExporterOperator)
    bpy.types.TOPBAR_MT_file_export.append(export)


def unregister():
    import bpy

    from kitsunetsuki.exporter.bvhq import BVHQExporterOperator, export
    bpy.types.TOPBAR_MT_file_export.remove(export)
    bpy.utils.unregister_class(BVHQExporterOperator)


if __name__ == '__main__':
    main()
