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
import configparser
import copy
import math
import os
import typing

from bpy_extras.io_utils import ExportHelper

from kitsunetsuki.base.armature import is_left_bone, is_bone_matches
from kitsunetsuki.base.objects import get_parent

from ..gltf import spec, GLTFExporter


BLENDSHAPE_PRESETS = (
    'neutral',
    'a',
    'i',
    'u',
    'e',
    'o',
    'blink',
    'joy',
    'angry',
    'sorrow',
    'fun',
    'lookup',
    'lookdown',
    'lookleft',
    'lookright',
    'blink_l',
    'blink_r',
)


class VRMExporter(GLTFExporter):
    def __init__(self, args):
        super().__init__(args)
        self._z_up = False
        self._pose_freeze = True

    @property
    def export_settings(self):
        settings = {}
        settings.update(super().export_settings)
        settings.update({
            'gltf_keep_original_textures': False,
            'gltf_format': 'GLB',
        })

        return settings

    def _add_vrm_thumbnail(self, gltf_node, filepath):
        gltf_sampler = {
            'name': os.path.basename(filepath),
            'wrapS': spec.CLAMP_TO_EDGE,
            'wrapT': spec.CLAMP_TO_EDGE,
        }
        gltf_node['samplers'].append(gltf_sampler)

        gltf_image = {
            'name': os.path.basename(filepath),
            'mimeType': 'image/png',
            'extras': {
                'uri': filepath,
            }
        }
        gltf_node['images'].append(gltf_image)

        gltf_texture = {
            'sampler': len(gltf_node['samplers']) - 1,
            'source': len(gltf_node['images']) - 1,
        }
        gltf_node['textures'].append(gltf_texture)

        texid = len(gltf_node['textures']) - 1
        gltf_node['extensions']['VRM']['meta']['texture'] = texid

    def _make_vrm_meta(self):
        data = {}
        text = bpy.data.texts.get('VRM.ini')
        if text:
            data = configparser.ConfigParser()
            data.read_string(text.as_string())
        else:
            raise RuntimeError('Missing "VRM.ini" text block.')

        return {
            'exporterVersion': (
                'KITSUNETSUKI Asset Tools by kitsune.ONE - '
                'https://github.com/kitsune-ONE-team/KITSUNETSUKI-Asset-Tools'),
            'specVersion': '0.0',

            'meta': {
                'title': data['meta']['title'],
                'version': data['meta']['version'],
                'author': data['meta']['author'],
                'contactInformation': data['meta']['contactInformation'],
                'reference': data['meta']['reference'],
                'texture': 0,  # thumbnail texture
                'allowedUserName': data['meta'].get('allowedUserName', 'OnlyAuthor'),
                'violentUssageName': data['meta'].get('violentUssageName', 'Disallow'),
                'sexualUssageName': data['meta'].get('sexualUssageName', 'Disallow'),
                'commercialUssageName': data['meta'].get('commercialUssageName', 'Disallow'),
                'otherPermissionUrl': data['meta'].get('otherPermissionUrl', ''),
                'licenseName': data['meta'].get('licenseName', 'Redistribution_Prohibited'),
                'otherLicenseUrl': data['meta'].get('otherLicenseUrl', ''),
            },

            'humanoid': {
                'armStretch': 0.0,
                'legStretch': 0.0,
                'lowerArmTwist': 0.0,  # LowerArm bone roll
                'upperArmTwist': 0.0,  # UpperArm bone roll
                'lowerLegTwist': 0.0,  # LowerLeg bone roll
                'upperLegTwist': 0.0,  # UpperLeg bone roll
                'feetSpacing': 0.0,
                'hasTranslationDoF': False,
                'humanBones': [],
            },

            'firstPerson': {
                'firstPersonBone': None,
                'firstPersonBoneOffset': {
                    'x': 0,
                    'y': 0,
                    'z': 0,
                },
                'meshAnnotations': [],
                'lookAtTypeName': 'Bone',
                # 'lookAtTypeName': 'BlendShape',
                'lookAtHorizontalInner': None,
                'lookAtHorizontalOuter': None,
                'lookAtVerticalDown': None,
                'lookAtVerticalUp': None,
            },

            'blendShapeMaster': {
                'blendShapeGroups': [],
            },
            'secondaryAnimation': {
                'boneGroups': [],
                # 'colliderGroups': [],
            },
            'materialProperties': [],
        }

    def _make_vrm_material(self, material):
        vrm_material = {
            'floatProperties': {
                '_BlendMode': 0 if material.blend_method == 'OPAQUE' else 1,
                '_BumpScale': 1,
                '_CullMode': 2 if material.use_backface_culling else 0,
                '_Cutoff': material.alpha_threshold,
                '_DebugMode': 0,
                '_DstBlend': 0,
                '_IndirectLightIntensity': 0.1,
                '_LightColorAttenuation': 0,
                '_MToonVersion': 35,
                '_OutlineColorMode': 0,
                '_OutlineCullMode': 1,
                '_OutlineLightingMix': 1,
                '_OutlineScaledMaxDistance': 1,
                '_OutlineWidth': 0.5,
                '_OutlineWidthMode': 0,
                '_ReceiveShadowRate': 1,
                '_RimFresnelPower': 1,
                '_RimLift': 0,
                '_RimLightingMix': 0,
                '_ShadeShift': 0,
                '_ShadeToony': 0.9,
                '_ShadingGradeRate': 1,
                '_SrcBlend': 1,
                '_UvAnimRotation': 0,
                '_UvAnimScrollX': 0,
                '_UvAnimScrollY': 0,
                '_ZWrite': 1,
            },

            'keywordMap': {},
            'name': material.name,
            'renderQueue': 2000,
            'shader': 'VRM_USE_GLTFSHADER',
            'tagMap': {},
            'textureProperties': {},

            'vectorProperties': {
                '_BumpMap': [0, 0, 1, 1],
                '_Color': [1, 1, 1, 1],
                '_EmissionColor': [0, 0, 0, 1],
                '_EmissionMap': [0, 0, 1, 1],
                '_MainTex': [0, 0, 1, 1],
                '_OutlineColor': [0, 0, 0, 1],
                '_OutlineWidthTexture': [0, 0, 1, 1],
                '_ReceiveShadowTexture': [0, 0, 1, 1],
                '_RimColor': [0, 0, 0, 1],
                '_RimTexture': [0, 0, 1, 1],
                '_ShadeColor': [1, 1, 1, 1],
                '_ShadeTexture': [0, 0, 1, 1],
                '_ShadingGradeTexture': [0, 0, 1, 1],
                '_SphereAdd': [0, 0, 1, 1],
                '_UvAnimMaskTexture': [0, 0, 1, 1],
            },
        }

        return vrm_material

    def _make_vrm_blend_shape(self, name):
        """
        Standby expression:
        - Neutral

        Lip-sync:
        - A (aa)
        - I (ih)
        - U (ou)
        - E (e)
        - O (oh)

        Blink:
        - Blink
        - Blink_L
        - Blink_R

        Emotion:
        - Fun
        - Angry
        - Sorrow
        - Joy

        Eye control:
        - LookUp
        - LookDown
        - LookLeft
        - LookRight
        """

        vrm_name = {
            # try to get VRM blend shapes from VRChat
            'vrc.v_aa': 'A',
            'vrc.v_ih': 'I',
            'vrc.v_ou': 'U',
            'vrc.v_e': 'E',
            'vrc.v_oh': 'O',
            'vrc.blink': 'Blink',
            'vrc.blink_left': 'Blink_L',
            'vrc.blink_right': 'Blink_R',
        }.get(name, name)

        preset = 'unknown'
        if vrm_name.lower() in BLENDSHAPE_PRESETS:
            preset = vrm_name.lower()

        vrm_blend_shape = {
            'name': vrm_name,
            'presetName': preset,
            'isBinary': False,
            'binds': [],  # bind to mesh ID and shape key ID with shape key weight
            'materialValues': [],  # material values override
        }

        return vrm_blend_shape

    def _make_vrm_bone(self, bone):
        vrm_bone = {
            'bone': None,
            # 'node': gltf_node_id,
            'useDefaultValues': True,
            'extras': {
                'name': bone.name,
            }
        }

        def is_hips(bone):
            return is_bone_matches(bone, ('hips',))

        def is_upper_leg(bone, strict=True):
            names = ['thigh']
            if not strict:
                names.append('leg')
            is_upper = is_bone_matches(bone, names)
            is_child = is_hips(get_parent(bone))
            return is_upper or is_child

        def is_lower_leg(bone):
            is_lower = is_bone_matches(bone, ('calf', 'shin', 'knee'))
            is_child = is_upper_leg(get_parent(bone), strict=False)
            return is_lower or is_child

        def is_hand(bone):
            return is_bone_matches(bone, ('hand', 'wrist'))

        side = 'left' if is_left_bone(bone) else 'right'

        parents = []
        for i in range(1, 3+1):
            parent = get_parent(bone, i)
            if parent:
                parents.append(parent)

        if is_hips(bone):
            vrm_bone['bone'] = 'hips'

        elif (is_bone_matches(bone, ('upperchest',)) or
                (is_bone_matches(bone, ('spine',)) and is_hips(get_parent(bone, 3)))):
            vrm_bone['bone'] = 'upperChest'

        elif (is_bone_matches(bone, ('chest',)) or
                (is_bone_matches(bone, ('spine',)) and is_hips(get_parent(bone, 2)))):
            vrm_bone['bone'] = 'chest'

        elif is_bone_matches(bone, ('spine',)):
            vrm_bone['bone'] = 'spine'

        elif is_bone_matches(bone, ('neck',)):
            vrm_bone['bone'] = 'neck'

        elif is_bone_matches(bone, ('head',)):
            vrm_bone['bone'] = 'head'

        elif is_bone_matches(bone, ('eye',)):
            vrm_bone['bone'] = '{}Eye'.format(side)

        elif is_bone_matches(bone, ('foot', 'ankle')):
            vrm_bone['bone'] = '{}Foot'.format(side)

        elif is_lower_leg(bone):
            vrm_bone['bone'] = '{}LowerLeg'.format(side)

        elif is_upper_leg(bone):
            vrm_bone['bone'] = '{}UpperLeg'.format(side)

        elif is_bone_matches(bone, ('toe',)):
            vrm_bone['bone'] = '{}Toes'.format(side)

        elif is_bone_matches(bone, ('shoulder', 'clavicle')):
            vrm_bone['bone'] = '{}Shoulder'.format(side)

        elif is_bone_matches(bone, ('lowerarm', 'lower_arm', 'forearm', 'elbow')):
            vrm_bone['bone'] = '{}LowerArm'.format(side)

        elif is_bone_matches(bone, ('upperarm', 'upper_arm', 'arm')):
            vrm_bone['bone'] = '{}UpperArm'.format(side)

        elif any(map(is_hand, parents)):  # hand in parents -> finger
            if is_hand(get_parent(bone, 3)):  # 3 level deep parent
                part_name = 'Distal'
            elif is_hand(get_parent(bone, 2)):  # 2 level deep parent
                part_name = 'Intermediate'
            else:  # 1 level deep parent - direct parent
                part_name = 'Proximal'

            if is_bone_matches(bone, ('thumb',)):
                vrm_bone['bone'] = '{}Thumb{}'.format(side, part_name)

            elif is_bone_matches(bone, ('index',)):
                vrm_bone['bone'] = '{}Index{}'.format(side, part_name)

            elif is_bone_matches(bone, ('middle',)):
                vrm_bone['bone'] = '{}Middle{}'.format(side, part_name)

            elif is_bone_matches(bone, ('ring',)):
                vrm_bone['bone'] = '{}Ring{}'.format(side, part_name)

            elif is_bone_matches(bone, ('pinky', 'little')):
                vrm_bone['bone'] = '{}Little{}'.format(side, part_name)

        elif is_hand(bone):
            vrm_bone['bone'] = '{}Hand'.format(side)

        return vrm_bone

    def _make_vrm_spring(self, bone):
        vrm_spring = {
            'comment': bone.name,
            'stiffiness': 1,  # The resilience of the swaying object (the power of returning to the initial pose)
            'gravityPower': 0,
            'dragForce': 0,  # The resistance (deceleration) of automatic animation
            'gravityDir': {
                'x': 0,
                'y': -1,
                'z': 0,
            },  # down
            'center': -1,
            'hitRadius': 0,
            # 'bones': [gltf_node_id],
            # 'colliderGroups': [],
        }

        if bone.get('jiggle_stiffness', None) is not None:
            vrm_spring['stiffiness'] = bone.get('jiggle_stiffness')

        if bone.get('jiggle_gravity', None) is not None:
            vrm_spring['gravityPower'] = bone.get('jiggle_gravity')

        if bone.get('jiggle_amplitude', None) is not None:
            max_amp = 200
            jiggle_amplitude = min(max_amp, bone.get('jiggle_amplitude'))
            vrm_spring['dragForce'] = (max_amp - jiggle_amplitude) / max_amp

        return vrm_spring

    def _process_data(self, data):
        data = copy.copy(super()._process_data(data))

        # define extensions

        if 'extensionsUsed' not in data:
            data['extensionsUsed'] = []
        data['extensionsUsed'].append('VRM')
        if 'extensions' not in data:
            data['extensions'] = {}
        data['extensions']['VRM'] = self._make_vrm_meta()

        # materials

        for gltf_material_id, gltf_material in enumerate(data['materials']):
            material = bpy.data.materials[gltf_material['name']]
            vrm_material = self._make_vrm_material(material)

            if gltf_material.get('alphaMode') == 'OPAQUE':
                vrm_material['tagMap']['RenderType'] = 'Opaque'
                vrm_material['shader'] = 'VRM/MToon'
            else:
                vrm_material['shader'] = 'VRM/UnlitCutout'

            if gltf_material['pbrMetallicRoughness'].get('baseColorTexture'):
                vrm_material['textureProperties']['_MainTex'] = gltf_material['pbrMetallicRoughness']['baseColorTexture']['index']

            data['extensions']['VRM']['materialProperties'].append(vrm_material)

        # blend shapes

        vrm_blend_shapes = {
            'Neutral': {
                'name': 'Neutral',
                'presetName': 'neutral',
                'isBinary': False,
                'binds': [],
                'materialValues': [],
            }
        }
        for gltf_mesh_id, gltf_mesh in enumerate(data['meshes']):
            vrm_annotation = {
                'firstPersonFlag': 'Auto',
                'mesh': gltf_mesh_id,
            }
            data['extensions']['VRM']['firstPerson']['meshAnnotations'].append(vrm_annotation)

            for gltf_primitive_id, gltf_primitive in enumerate(gltf_mesh['primitives']):
                target_names = (
                    gltf_primitive.get('extras', {}).get('targetNames') or
                    gltf_mesh.get('extras', {}).get('targetNames') or
                    [])

                for sk_id, sk_name in enumerate(target_names):
                    if sk_name in vrm_blend_shapes:
                        vrm_blend_shape = vrm_blend_shapes[sk_name]
                    else:
                        vrm_blend_shape = self._make_vrm_blend_shape(sk_name)
                        vrm_blend_shapes[sk_name] = vrm_blend_shape

                    for vrm_bind in vrm_blend_shape['binds']:
                        if vrm_bind['mesh'] == gltf_mesh_id and vrm_bind['index'] == sk_id:
                            break
                    else:
                        vrm_bind = {
                            'mesh': gltf_mesh_id,
                            'index': sk_id,
                            'weight': 100,
                        }
                        vrm_blend_shape['binds'].append(vrm_bind)

        for vrm_blend_shape in vrm_blend_shapes.values():
            data['extensions']['VRM']['blendShapeMaster']['blendShapeGroups'].append(vrm_blend_shape)

        # bones

        vrm_bones = {}
        vrm_springs = {}
        for gltf_skin in data['skins']:
            for joint_id in gltf_skin['joints']:
                gltf_node = data['nodes'][joint_id]
                armature = bpy.data.objects[gltf_skin['name']]
                bone = armature.data.bones[gltf_node['name']]
                pose_bone = armature.pose.bones[gltf_node['name']]

                vrm_bone = self._make_vrm_bone(bone)
                vrm_bone['node'] = joint_id

                if vrm_bone['bone'] and vrm_bone['bone'] not in vrm_bones:
                    vrm_bones[vrm_bone['bone']] = vrm_bone
                    data['extensions']['VRM']['humanoid']['humanBones'].append(vrm_bone)

                    fp = data['extensions']['VRM']['firstPerson']

                    if vrm_bone['bone'] == 'head':
                        fp['firstPersonBone'] = joint_id
                        fp['extras'] = {'name': bone.name}

                    elif vrm_bone['bone'] == 'leftEye':
                        fp.update({
                            'lookAtHorizontalOuter': {
                                'curve': [0, 0, 0, 1, 1, 1, 1, 0],
                                'xRange': 90,
                                'yRange': 10,
                            },
                            'lookAtHorizontalInner': {
                                'curve': [0, 0, 0, 1, 1, 1, 1, 0],
                                'xRange': 90,
                                'yRange': 10,
                            },
                            'lookAtVerticalDown': {
                                'curve': [0, 0, 0, 1, 1, 1, 1, 0],
                                'xRange': 90,
                                'yRange': 10,
                            },
                            'lookAtVerticalUp': {
                                'curve': [0, 0, 0, 1, 1, 1, 1, 0],
                                'xRange': 90,
                                'yRange': 10,
                            },
                        })

                        for c in pose_bone.constraints:
                            if c.type == 'LIMIT_ROTATION':
                                fp['lookAtHorizontalOuter']['xRange'] = -math.degrees(c.min_x)
                                fp['lookAtHorizontalInner']['xRange'] = math.degrees(c.max_x)
                                fp['lookAtVerticalDown']['yRange'] = -math.degrees(c.min_z)
                                fp['lookAtVerticalUp']['yRange'] = math.degrees(c.max_z)
                                break

                # Wiggle Bones addon
                # https://blenderartists.org/t/wiggle-bones-a-jiggle-bone-implementation-for-2-8/1154726
                if pose_bone.get('jiggle_enable', False):
                    # search for root bone
                    while (pose_bone.parent and
                            pose_bone.parent.get('jiggle_enable', False)):
                        pose_bone = pose_bone.parent

                    if pose_bone.name in vrm_springs:
                        continue

                    vrm_spring = self._make_vrm_spring(pose_bone)
                    vrm_spring['bones'] = [joint_id]
                    data['extensions']['VRM']['secondaryAnimation']['boneGroups'].append(vrm_spring)

                    vrm_springs[pose_bone.name] = vrm_spring

        return data


class VRMExporterOperator(bpy.types.Operator, ExportHelper):
    bl_idname = 'avatar.vrm'
    bl_label = 'Export VRM'
    bl_description = 'Export VRM'
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = '.vrm'
    filter_glob: bpy.props.StringProperty(default='*.vrm', options={'HIDDEN'})

    def execute(self, context: bpy.types.Context):
        if not self.filepath:
            return {'CANCELLED'}

        class Args(object):
            inputs = []
            output = self.filepath
            exec = None

        args = Args()
        e = VRMExporter(args)
        e.convert()

        bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)  # re-open current file
        return {'FINISHED'}

    def invoke(self, context, event):
        return typing.cast(typing.Set[str], ExportHelper.invoke(self, context, event))

    def draw(self, context):
        pass


def export(export_op, context):
    export_op.layout.operator(
        VRMExporterOperator.bl_idname,
        text='VRM using KITSUNETSUKI Asset Tools (.vrm)')
