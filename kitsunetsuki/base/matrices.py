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
import itertools

from bpy_types import PoseBone

from panda3d.core import LMatrix4d


def quat_to_list(quat):
    return [quat.x, quat.y, quat.z, quat.w]


def matrix_to_list(matrix):
    return list(itertools.chain(*map(tuple, matrix.col)))


def matrix_to_panda(matrix):
    return LMatrix4d(*itertools.chain(*map(tuple, matrix.col)))


def _bone_matrix(bone):
    if isinstance(bone, PoseBone):
        return bone.matrix
    else:
        return bone.matrix_local


def get_bone_matrix(bone, armature=None):
    if bone.parent:
        return _bone_matrix(bone.parent).inverted() @ _bone_matrix(bone)
    else:  # root bone
        if armature is None:
            return _bone_matrix(bone)
        else:
            return armature.matrix_world @ _bone_matrix(bone)


def get_inverse_bind_matrix(bone, obj, armature):
    return bone.matrix_local.inverted() @ armature.matrix_world.inverted() @ obj.matrix_world


def get_object_matrix_local(obj):
    if isinstance(obj, (bpy.types.Bone, bpy.types.PoseBone)):
        return obj.matrix
    else:
        return obj.matrix_local


def get_object_matrix(obj, armature=None):
    if armature is None:
        return get_object_matrix_local(obj)
    else:
        if obj.parent:
            return (
                get_object_matrix_local(obj.parent).inverted() @
                get_object_matrix_local(obj))
        else:
            return armature.matrix_world @ get_object_matrix_local(obj)
