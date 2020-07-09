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

from setuptools import setup


setup(
    name='kitsunetsuki-asset-tools',
    version='0.3.1',
    description='KITSUNETSUKI Asset Tools',
    long_description='KITSUNETSUKI Asset Tools',
    url='https://kitsune.one/',
    download_url='https://kitsune.one/',
    author='Yonnji',
    license='GPL3',
    packages=(
        'kitsunetsuki',
        'kitsunetsuki.base',
        'kitsunetsuki.exporter',
        'kitsunetsuki.exporter.base',
        'kitsunetsuki.exporter.egg',
        'kitsunetsuki.exporter.gltf',
        'kitsunetsuki.cardmaker',
    ),
    entry_points={
        'console_scripts': (
            'blend2gltf=kitsunetsuki.blend2gltf:main',
            'blend2egg=kitsunetsuki.blend2egg:main',
            'makecard=kitsunetsuki.makecard:main',
        ),
    },
)
