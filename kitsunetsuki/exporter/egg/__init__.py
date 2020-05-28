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

import json
import math

from panda3d.core import CS_zup_right
from panda3d.egg import EggComment, EggData, EggGroup, EggPolygon

from kitsunetsuki.base.armature import get_armature
from kitsunetsuki.base.collections import get_object_collection
from kitsunetsuki.base.matrices import (
    get_object_matrix, get_bone_matrix, matrix_to_panda)
from kitsunetsuki.base.objects import is_collision, get_object_properties

from kitsunetsuki.exporter.base import Exporter

from .animation import AnimationMixin
from .geom import GeomMixin
from .material import MaterialMixin
from .texture import TextureMixin
from .vertex import VertexMixin


class EggExporter(
        AnimationMixin, GeomMixin, MaterialMixin, TextureMixin,
        VertexMixin, Exporter):
    """
    BLEND to EGG converter.
    """
    def __init__(self, args):
        super().__init__(args)
        self._output = args.output or args.input.replace('.blend', '.egg')

    def make_root_node(self):
        egg_root = EggData()
        egg_root.set_coordinate_system(CS_zup_right)  # Z-up

        egg_comment = EggComment(
            '', 'Made with KITSUNETSUKI SDK by kitsune.ONE - '
            'https://kitsune.one/')
        egg_root.add_child(egg_comment)

        return egg_root

    def _setup_node(self, node, obj=None):
        if obj is not None:
            armature = get_armature(obj)

            obj_matrix = get_object_matrix(obj, armature=armature)
            node.add_matrix4(matrix_to_panda(obj_matrix))

            # get custom object properties
            obj_props = get_object_properties(obj)

            if obj_props.get('type') == 'Portal':
                node.set_portal_flag(True)

            # setup collisions
            elif is_collision(obj):
                # collision name
                node.set_collision_name(obj.name)

                # collision solid type
                shape = {
                    'BOX': EggGroup.CST_box,
                    'SPHERE': EggGroup.CST_sphere,
                    'CAPSULE': EggGroup.CST_tube,
                    'MESH': EggGroup.CST_polyset,
                }.get(obj.rigid_body.collision_shape, EggGroup.CST_polyset)

                # custom shape
                if obj.rigid_body.collision_shape == 'CONVEX_HULL':
                    # trying to guess the best shape
                    polygons = list(filter(
                        lambda x: isinstance(x, EggPolygon),
                        node.get_children()))
                    if len(polygons) == 1 and polygons[0].is_planar():
                        # shape = EggGroup.CST_plane  # <- is it infinite?
                        shape = EggGroup.CST_polygon
                node.set_cs_type(shape)

                # collision flags
                # inherit collision by children nodes?
                flags = EggGroup.CF_descend
                if (not obj.collision or not obj.collision.use):
                    # don't actually collide (ghost)
                    flags |= EggGroup.CF_intangible
                node.set_collide_flags(flags)

            # save object custom properties
            for k, v in obj_props.items():
                if node.get_tag(k):  # tag exists
                    tag = node.get_tag(k)

                    if k == 'type':
                        continue

                if type(v) in (tuple, list, dict):
                    tag = json.dumps(v)
                else:
                    tag = '{}'.format(v)
                node.set_tag(k, tag)

            if obj_props.get('type') == 'Portal':
                node.set_portal_flag(True)

    def make_empty(self, parent_node, obj):
        egg_group = EggGroup(obj.name)

        self._setup_node(egg_group, obj)
        parent_node.add_child(egg_group)

        return egg_group

    def make_armature(self, parent_node, obj):
        egg_group = EggGroup(obj.name)
        egg_group.set_dart_type(EggGroup.DT_structured)

        egg_joints = {}

        for bone_name, bone in obj.data.bones.items():
            bone_matrix = get_bone_matrix(bone, armature=obj)

            egg_joint = EggGroup(bone_name)
            egg_joint.set_group_type(EggGroup.GT_joint)
            egg_joint.add_matrix4(matrix_to_panda(bone_matrix))

            if bone.parent:
                egg_joints[bone.parent.name].add_child(egg_joint)
            else:  # root bone
                egg_group.add_child(egg_joint)

            egg_joints[bone_name] = egg_joint

        self._setup_node(egg_group, obj)
        parent_node.add_child(egg_group)

        return egg_group

    def make_mesh(self, parent_node, obj):
        egg_group = None

        # merged nodes
        if self.can_merge(obj):
            collection = get_object_collection(obj)

            for child in parent_node.get_children():
                if (isinstance(child, EggGroup) and
                        child.get_name() == collection.name):
                    egg_group = child
                    break
            else:
                egg_group = EggGroup(collection.name)
                self._setup_node(egg_group)
                parent_node.add_child(egg_group)

            self.make_geom(egg_group, obj, can_merge=True)

        # separate nodes
        if not self.can_merge(obj) or self._keep:
            egg_group = EggGroup(obj.name)
            self._setup_node(egg_group, obj)
            parent_node.add_child(egg_group)

            self.make_geom(egg_group, obj, can_merge=False)

        return egg_group

    def make_light(self, parent_node, obj):
        LIGHT_TYPES = {
            'POINT': 'PointLight',
            'SPOT': 'SpotLight',
        }

        egg_group = EggGroup(obj.name)
        egg_group.set_tag('type', 'Light')
        egg_group.set_tag('light', LIGHT_TYPES[obj.data.type])

        egg_group.set_tag('color', json.dumps(tuple(obj.data.color)))
        egg_group.set_tag('scale', json.dumps(tuple(obj.scale)))
        egg_group.set_tag('energy', '{:.3f}'.format(
            obj.data.energy))
        egg_group.set_tag('far', '{:.3f}'.format(
            obj.data.shadow_soft_size))

        if obj.data.type == 'SPOT':
            egg_group.set_tag('fov', '{:.3f}'.format(
                math.degrees(obj.data.spot_size)))

        self._setup_node(egg_group, obj)
        parent_node.add_child(egg_group)

        return egg_group
