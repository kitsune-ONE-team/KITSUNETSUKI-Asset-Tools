#!/usr/bin/env python3

import os
import zipfile
from kitsunetsuki import bl_info


version = '{}.{}.{}'.format(*bl_info['version'])


with open(f'KAT_blender_addon_{version}.zip', 'wb') as f:
    with zipfile.ZipFile(f, 'w') as z:
        for root, dirs, files in os.walk('kitsunetsuki'):
            for i in files:
                if i != '__pycache__' and not i.endswith('.pyc'):
                    z.write(os.path.join(root, i))
