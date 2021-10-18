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


Installing into Blender as addon
--------------------------------

* Download addon in ZIP format from [Releases](https://github.com/kitsune-ONE-team/KITSUNETSUKI-Asset-Tools/releases)
* Open _Edit_ - _Preferences_ - _Add-ons_ in Blender
* Click _Install_ and choose downloaded ZIP file
* Activate **KITSUNETSUKI Asset Tools** in the add-ons list

Add-on will add two new menu entries in _File_ - _Export_:

* Export glTF
* Export VRM

[![YouTube](http://img.youtube.com/vi/B-bRDg-Odco/0.jpg)](https://www.youtube.com/watch?v=B-bRDg-Odco)


Installing into Anaconda / Miniconda as tool
--------------------------------------------

* Install [Anaconda](https://www.anaconda.com/products/individual) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) Python
* Install [prebuilt](https://anaconda.org/kitsune.ONE/python-blender) Blender as Python module from Anaconda Cloud or [build](https://github.com/kitsune-ONE-team/KITSUNETSUKI-SDK/tree/master/conda/blender) one by yourself:

```
conda install -c kitsune.one python-blender
```

* Install **KITSUNETSUKI Asset Tools**

```
pip install git+https://github.com/kitsune-ONE-team/KITSUNETSUKI-Asset-Tools.git
```
