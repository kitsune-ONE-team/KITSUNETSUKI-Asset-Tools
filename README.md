KITSUNETSUKI Asset Tools
========================

Collection of asset tools designed for automated pipeline.


Tools
-----

* [blend2egg](blend2egg.md) - BLEND to EGG (Panda3D model format) converter
* [blend2gltf](blend2gltf.md) - BLEND to [glTF](https://github.com/KhronosGroup/glTF) converter
* [blend2vrm](blend2vrm.md) - BLEND to [VRM](https://vrm.dev/) converter
* [gltf-inspect](gltf-inspect.md) - Tiny tool for browsing [glTF](https://github.com/KhronosGroup/glTF) file's structure
* [makecard](makecard.md) - Card maker tool for Panda3D


Installation
------------

**Installing into [Anaconda](https://www.anaconda.com/products/individual) / [Miniconda](https://docs.conda.io/en/latest/miniconda.html) Python**

This is an easiest way to install.
It uses [prebuilt](https://anaconda.org/kitsune.ONE/python-blender) Blender's Python module from Anaconda Cloud.
You can also [build](https://github.com/kitsune-ONE-team/KITSUNETSUKI-SDK/tree/master/conda/blender) one by yourself.

```
conda install -c kitsune.one python-blender
pip install git+https://github.com/kitsune-ONE-team/KITSUNETSUKI-Asset-Tools.git
```


**Installing into Python**

This is the most difficult way to install.
You have to find the Blender's Python module or build it by yourself.

```
pip install git+https://github.com/kitsune-ONE-team/KITSUNETSUKI-Asset-Tools.git
```


**Installing into [Blender](https://www.blender.org/download/) Python**

The installation process is a little bit tricky for this one.
You need to install Python modules into Blender's Python and run Python scripts with Blender.
You can't run scripts which depends on Panda3D, for example *blend2egg*.

```
2.83/python/bin/python3.7m -m ensurepip
2.83/python/bin/python3.7m -m pip install git+https://github.com/kitsune-ONE-team/KITSUNETSUKI-Asset-Tools.git
```


**Running asset tools from [Blender](https://www.blender.org/download/) Python**

```
blender -b -P 2.83/python/lib/python3.7/site-packages/kitsunetsuki/blend2gltf.py model.blend -o model.gltf
```
