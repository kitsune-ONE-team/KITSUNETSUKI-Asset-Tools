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
import os

from kitsunetsuki.base.armature import is_left_bone, is_bone_matches
from kitsunetsuki.base.objects import get_parent

from ..gltf import GLTFExporter
from ..gltf import spec


class VRMExporter(GLTFExporter):
    def __init__(self, args):
        super().__init__(args)

        self._z_up = False
        self._pose_freeze = True

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

        gltf_node['extensions']['VRM']['meta']['texture'] = len(gltf_node['textures']) - 1

    def make_root_node(self):
        gltf_node = super().make_root_node()

        data = {}
        text = bpy.data.texts.get('VRM.ini')
        if text:
            data = configparser.ConfigParser()
            data.read_string(text.as_string())

        vrm_meta = {
            'exporterVersion': gltf_node['asset']['generator'],
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
                'colliderGroups': [],
            },
            'materialProperties': [],
        }

        gltf_node['extensionsUsed'].append('VRM')
        gltf_node['extensions']['VRM'] = vrm_meta
        gltf_node['materials'] = []

        # make thumbnail
        prefix = os.path.basename(self._input).replace('.blend', '.png')
        inpdir = os.path.dirname(os.path.abspath(self._input))
        if os.path.exists(inpdir) and os.path.isdir(inpdir):
            for filename in reversed(sorted(os.listdir(inpdir))):
                if filename.startswith(prefix):
                    self._add_vrm_thumbnail(gltf_node, os.path.join(inpdir, filename))
                    break

        return gltf_node

    def _make_vrm_bone(self, gltf_node_id, bone):
        vrm_bone = {
            'bone': None,
            'node': gltf_node_id,
            'useDefaultValues': True,
            'extras': {
                'name': bone.name,
            }
        }

        def is_hand(bone):
            return is_bone_matches(bone, ('hand', 'wrist'))

        side = 'left' if is_left_bone(bone) else 'right'

        parents = []
        for i in range(1, 3+1):
            parent = get_parent(bone, i)
            if parent:
                parents.append(parent)

        if is_bone_matches(bone, ('hips',)):
            vrm_bone['bone'] = 'hips'

        elif is_bone_matches(bone, ('spine',)):
            vrm_bone['bone'] = 'spine'

        elif is_bone_matches(bone, ('chest',)):
            vrm_bone['bone'] = 'chest'

        elif is_bone_matches(bone, ('neck',)):
            vrm_bone['bone'] = 'neck'

        elif is_bone_matches(bone, ('head',)):
            vrm_bone['bone'] = 'head'

        elif is_bone_matches(bone, ('eye',)):
            vrm_bone['bone'] = '{}Eye'.format(side)

        elif is_bone_matches(bone, ('lowerleg', 'calf', 'shin', 'knee')):
            vrm_bone['bone'] = '{}LowerLeg'.format(side)

        elif is_bone_matches(bone, ('upperleg', 'thigh', 'leg')):
            vrm_bone['bone'] = '{}UpperLeg'.format(side)

        elif is_bone_matches(bone, ('foot', 'ankle')):
            vrm_bone['bone'] = '{}Foot'.format(side)

        elif is_bone_matches(bone, ('toe',)):
            vrm_bone['bone'] = '{}Toes'.format(side)

        elif is_bone_matches(bone, ('shoulder', 'clavicle')):
            vrm_bone['bone'] = '{}Shoulder'.format(side)

        elif is_bone_matches(bone, ('lowerarm', 'elbow')):
            vrm_bone['bone'] = '{}LowerArm'.format(side)

        elif is_bone_matches(bone, ('upperarm', 'arm')):
            vrm_bone['bone'] = '{}UpperArm'.format(side)

        elif is_hand(bone):
            vrm_bone['bone'] = '{}Hand'.format(side)

        elif any(map(is_hand, parents)):  # hand in parents -> finger
            if is_hand(get_parent(bone, 3)):  # 3 level deep parent
                part_name = 'Distal'
            elif is_hand(get_parent(bone, 1)):  # 2 level deep parent
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

        return vrm_bone

    def make_armature(self, parent_node, armature):
        gltf_armature = super().make_armature(parent_node, armature)

        vrm_bones = set()
        for bone_name, bone in armature.data.bones.items():
            for gltf_node_id, gltf_node in enumerate(self._root['nodes']):
                if gltf_node['name'] == bone_name:
                    break
            else:
                continue

            vrm_bone = self._make_vrm_bone(gltf_node_id=gltf_node_id, bone=bone)

            if vrm_bone['bone'] and vrm_bone['bone'] not in vrm_bones:
                vrm_bones.add(vrm_bone['bone'])
                self._root['extensions']['VRM']['humanoid']['humanBones'].append(vrm_bone)

                fp = self._root['extensions']['VRM']['firstPerson']

                if vrm_bone['bone'] == 'head':
                    fp['firstPersonBone'] = len(self._root['nodes']) - 1
                    fp['extras'] = {'name': bone.name}

                elif vrm_bone['bone'] == 'leftEye':
                    look_at = {
                        'curve': [0, 0, 0, 1, 1, 1, 1, 0],
                        'xRange': 90,
                        'yRange': 10,
                    }
                    fp['lookAtHorizontalInner'] = look_at
                    fp['lookAtHorizontalOuter'] = look_at
                    fp['lookAtVerticalDown'] = look_at
                    fp['lookAtVerticalUp'] = look_at

        return gltf_armature

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
            # try to get VRM blend shapes from VRChat visemes
            'vrc.aa': 'A',
            'vrc.ih': 'I',
            'vrc.ou': 'U',
            'vrc.e': 'E',
            'vrc.oh': 'O',
        }.get(name, name)

        vrm_blend_shape = {
            'name': vrm_name,
            'presetName': vrm_name,
            'binds': [],  # bind to mesh ID, shape key ID, shake key weight
            'materialValues': [],
        }

        return vrm_blend_shape

    def convert(self):
        root, buffer_ = super().convert()

        for gltf_material_id, gltf_material in enumerate(root['materials']):
            material = bpy.data.materials[gltf_material['name']]
            vrm_material = self._make_vrm_material(material)

            if gltf_material['alphaMode'] == 'OPAQUE':
                vrm_material['tagMap']['RenderType'] = 'Opaque'
                vrm_material['shader'] = 'VRM/MToon'
            else:
                vrm_material['shader'] = 'VRM/UnlitCutout'

            if gltf_material['pbrMetallicRoughness'].get('baseColorTexture'):
                vrm_material['textureProperties']['_MainTex'] = gltf_material['pbrMetallicRoughness']['baseColorTexture']

            root['extensions']['VRM']['materialProperties'].append(vrm_material)

        vrm_blend_shapes = {}
        for gltf_mesh_id, gltf_mesh in enumerate(root['meshes']):
            vrm_annotation = {
                'firstPersonFlag': 'Auto',
                'mesh': gltf_mesh_id,
            }
            root['extensions']['VRM']['firstPerson']['meshAnnotations'].append(vrm_annotation)

            for gltf_primitive in gltf_mesh['primitives']:
                for sk_id, sk_name in enumerate(gltf_primitive['extras']['targetNames']):
                    if sk_name in vrm_blend_shapes:
                        vrm_blend_shape = vrm_blend_shapes[sk_name]
                    else:
                        vrm_blend_shape = self._make_vrm_blend_shape(sk_name)

                    vrm_bind = {
                        'mesh': gltf_mesh_id,
                        'index': sk_id,
                        'weight': 1,
                    }
                    vrm_blend_shape['binds'].append(vrm_bind)

        for vrm_blend_shape in vrm_blend_shapes.values():
            root['extensions']['VRM']['blendShapeMaster']['blendShapeGroups'].append(vrm_blend_shape)

        return root, buffer_
