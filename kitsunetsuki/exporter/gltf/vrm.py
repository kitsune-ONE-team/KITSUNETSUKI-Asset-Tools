import bpy
import configparser
import os

from kitsunetsuki.base.armature import is_left_bone, is_bone_matches
from kitsunetsuki.base.objects import get_parent

from . import spec


def make_vrm_thumbnail(output_filepath, render_filepath):
    thumbnail = None

    if render_filepath and not os.path.isdir(render_filepath):
        dirpath = os.path.join(
            os.path.dirname(output_filepath), os.path.dirname(render_filepath))
        if os.path.exists(dirpath):
            filename = os.path.basename(render_filepath)
            prefix, _, suffix = filename.rpartition('.')
            for filename2 in os.listdir(dirpath):
                if (filename2.startswith(prefix) and
                        filename2.endswith(suffix)):
                    thumbnail = os.path.join(dirpath, filename2)
                    break

    if thumbnail:
        gltf_sampler = {
            'name': os.path.basename(thumbnail),
            'wrapS': spec.CLAMP_TO_EDGE,
            'wrapT': spec.CLAMP_TO_EDGE,
        }

        gltf_image = {
            'name': os.path.basename(thumbnail),
            'mimeType': 'image/png',
            'extras': {
                'uri': thumbnail,
            }
        }

        return gltf_sampler, gltf_image

    return None, None


def make_vrm_meta(gltf_root):
    data = {}
    text = bpy.data.texts.get('VRM.ini')
    if text:
        cp = configparser.ConfigParser()
        cp.read_string(text.as_string())
        data = cp

    return {
        'exporterVersion': gltf_root['asset']['generator'],
        'specVersion': '0.0',

        'meta': {
            'title': data['meta']['title'],
            'version': data['meta']['version'],
            'author': data['meta']['author'],
            'contactInformation': data['meta']['contactInformation'],
            'reference': data['meta']['reference'],
            'texture': 0,
            'allowedUserName': data['meta'].get('allowedUserName', 'OnlyAuthor'),
            'violentUssageName': data['meta'].get('violentUssageName', 'Disallow'),
            'sexualUssageName': data['meta'].get('sexualUssageName', 'Disallow'),
            'commercialUssageName': data['meta'].get('commercialUssageName', 'Disallow'),
            'otherPermissionUrl': data['meta'].get('otherPermissionUrl', ''),
            'licenseName': data['meta']['licenseName'],
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
            'meshAnnotations': [{
                'firstPersonFlag': 'Auto',
                'mesh': 0,
            }],
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


def make_vrm_bone(gltf_node_id, bone):
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
        if 'hand' in get_parent(bone, 3).name.lower():  # 3 level deep parent
            part_name = 'Distal'
        elif 'hand' in get_parent(bone, 2).name.lower():  # 2 level deep parent
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


def make_vrm_material(material):
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
