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

from kitsunetsuki.base.collections import get_object_collection
from kitsunetsuki.base.objects import (
    get_object_properties, is_collision, is_object_visible)

from .geom import GeomMixin
from .material import MaterialMixin
from .texture import TextureMixin
from .vertex import VertexMixin


NOT_MERGED_TYPES = (
    'Portal',
    'Text',
    'Sprite',
    'Transparent',
    'Protected',
    'Dynamic',
)


class Exporter(GeomMixin, MaterialMixin, TextureMixin, VertexMixin):
    def __init__(self, args):
        self._input = args.input
        self._output = args.output
        bpy.ops.wm.open_mainfile(filepath=args.input)

        # export type
        self._export_type = args.export or 'all'
        self._action = args.action  # animation/action name to export

        # render type
        self._render_type = args.render or 'default'

        # animations
        self._speed_scale = args.speed or 1

        # geom scale
        self._geom_scale = args.scale or 1

        # scripting
        self._script_names = (args.exec or '').split(',')
        self._script_locals = {}

        # merging
        self._merge = args.merge
        self._keep = args.keep

        # materials, textures, UVs
        self._no_materials = args.no_materials is True
        self._no_extra_uv = args.no_extra_uv is True
        self._no_textures = args.no_textures is True
        self._empty_textures = args.empty_textures
        self._set_origin = args.set_origin is True

    def execute_script(self, name):
        script = bpy.data.texts.get(name)
        if script:
            code = compile(script.as_string(), name, 'exec')
            exec(code, None, self._script_locals)

            if 'SPEED_SCALE' in self._script_locals:
                self._speed_scale = self._script_locals['SPEED_SCALE']

    def can_merge(self, obj):
        if not self._merge:
            return False

        collection = get_object_collection(obj)
        if not collection:
            return False

        if is_collision(obj):
            return False

        obj_props = get_object_properties(obj)
        if obj_props.get('type') in NOT_MERGED_TYPES:
            return False

        return True

    def make_root_node(self):
        raise NotImplementedError()

    def make_empty(self, parent_node, obj):
        raise NotImplementedError()

    def make_mesh(self, parent_node, obj):
        raise NotImplementedError()

    def make_light(self, parent_node, obj):
        raise NotImplementedError()

    def make_armature(self, parent_node, obj):
        raise NotImplementedError()

    def make_animation(self, parent_node, obj=None):
        for child in bpy.data.objects:
            # print(child)
            if not is_object_visible(child):
                continue

            if child.type == 'ARMATURE':
                self.make_action(parent_node, child)
                return

    def make_node(self, parent_node, obj=None):
        node = None

        if obj is None:
            node = parent_node

        else:
            if obj.type == 'EMPTY':
                node = self.make_empty(parent_node, obj)

            elif obj.type == 'ARMATURE':
                node = self.make_armature(parent_node, obj)

            elif obj.type == 'MESH':
                node = self.make_mesh(parent_node, obj)

            elif obj.type in ('LIGHT', 'LAMP'):
                if obj.data.type in ('SPOT', 'POINT'):
                    node = self.make_light(parent_node, obj)

        if node is None:
            return

        # make children of the current node
        if obj is None:  # root objects
            children = filter(lambda o: not o.parent, bpy.data.objects)
        else:  # children on current object
            children = obj.children

        for child in children:
            # print(child)
            if not is_object_visible(child) and not is_collision(child):
                continue

            if self._export_type == 'collision':
                if child.type in ('ARMATURE', 'LIGHT', 'LAMP'):
                    continue

                if child.type == 'MESH' and not is_collision(child):
                    continue

            self.make_node(node, child)

    def convert(self):
        if self._script_names:
            for script_name in self._script_names:
                if script_name:
                    self.execute_script(script_name)

        self._root = self.make_root_node()

        if self._export_type == 'animation':
            self.make_animation(self._root)
        else:
            self.make_node(self._root)

        return self._root
