#!/usr/bin/env python3

import os
import shutil


confpath = os.path.join(os.path.expanduser('~'), '.config', 'blender')
versions = []
for i in os.listdir(confpath):
    versions.append((i, map(int, i.split('.'))))
versions.sort(key=lambda x: x[1])

print('using version {}'.format(versions[0][0]))
addonpath = os.path.join(confpath, versions[0][0], 'scripts', 'addons', 'kitsunetsuki')

if os.path.exists(addonpath):
    print('removing existing installation in {}'.format(addonpath))
    shutil.rmtree(addonpath)

print('installing to {}'.format(addonpath))
shutil.copytree('kitsunetsuki', addonpath)
