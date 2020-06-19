KITSUNETSUKI Asset Tools
========================

Collection of asset tools designed for automated pipeline.


Installation
------------

**Installing into [Anaconda](https://www.anaconda.com/products/individual) / [Miniconda](https://docs.conda.io/en/latest/miniconda.html) Python**

This is an easiest way to install.
It uses prebuilt Blender's Python module from Anaconda Cloud. You can also build one by yourself.

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
blender -b -P 2.83/python/lib/python3.7/site-packages/kitsunetsuki/blend2gltf.py model.blend --output model.gltf
```


Using examples
--------------

Original model made by theStoff:

https://sketchfab.com/3d-models/ruby-rose-2270ee59d38e409491a76451f6c6ef80

Convert models from BLEND file:
```
make -C examples/ruby_rose
```

Open converted models using Panda3D and RenderPipeline (from EGG format):
```
python examples/ruby_rose/scene_rp_egg.py
```

Open converted models using Panda3D and RenderPipeline (from glTF format):
```
python examples/ruby_rose/scene_rp_gltf.py
```

![Preview in Blender](screenshots/preview_blender.png)
![Preview in RenderPipeline](screenshots/preview_rp1.png)


Expected material nodes setup
-----------------------------

Supported texture maps as BSDF inputs for RenderPipeline materials:
* Base Color
* Specular
* Roughness
* Normal Map

Supported BSDF input values as RenderPipeline material params:
* Metallic (RenderPipeline uses values 0 and 1 only)
* Roughness
* Normal Map Strength (from Normal Map Node)

Some input values could be specified as separate Math Nodes.

![Nodes 1](screenshots/nodes1.png)
![Nodes 2](screenshots/nodes2.png)


NodePath tags setup
-------------------

You can define object's tags using json-encoded Blender text blocks with the same name as an object.

![Text 1](screenshots/text1.png)

pview output (notice the "hp" and "type" tags):
```
GeomNode mesh_ruby (1 geoms: S:(MaterialAttrib TextureAttrib)) [hp type] T:m(scale 10000)
```

python usage example:
```
ruby_mesh = self.ruby.find('**/=type=body')
print('hp', ruby_mesh.get_tag('hp'))
```
outputs:
```
hp 100
```

blend2egg
---------

BLEND to EGG (Panda3D model format) converter.

Features:
* Export [RenderPipeline](https://github.com/tobspr/RenderPipeline) materials
* Export Blender-calculated tangents-bitangents
* Export NodePath "tags" from json-encoded Blender text blocks
* Skeletal animations

EGG export requirements:
* Panda3D (1.10.6+) for EGG generation
* python-blender (2.81+) (Blender as Python module) or Blender's Python

Exporting models:
```
blend2egg --output x.egg x.blend
```

Exporting animations (from Blender actions):
```
blend2egg --output x_action_name.egg --export animation --action action_name x.blend
```


blend2gltf
----------

BLEND to [glTF](https://github.com/KhronosGroup/glTF) converter.
Uses custom glTF properties and extensions targeting [Panda3D glTF loader](https://github.com/Moguri/panda3d-gltf).

Features:
* Export [RenderPipeline](https://github.com/tobspr/RenderPipeline) materials
* Export Blender-calculated tangents-bitangents
* Export NodePath "tags" from json-encoded Blender text blocks

It's still in experimental state, so some features are still broken:
* Can't export animations
* Can't export specular maps

glTF export requirements:
* python-blender (2.81+) (Blender as Python module) or Blender's Python

glTF loading requirements:
* panda3d-gltf (0.7+)

Exporting models:
```
blend2egg --output x.gltf x.blend
```
