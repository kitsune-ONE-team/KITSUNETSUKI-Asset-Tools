KITSUNETSUKI Asset Tools
========================

Collection of asset tools designed for automated pipeline.


Installation
------------

```
pip install .
```


Using examples
--------------

The model included is not made by myself.
The model was made by theStoff - https://sketchfab.com/3d-models/ruby-rose-2270ee59d38e409491a76451f6c6ef80

Convert models from BLEND file:
```
make -C examples/ruby_rose
```

Open converted models using Panda3D and RenderPipelie (from EGG format):
```
python examples/ruby_rose/scene_rp_egg.py
```

Open converted models using Panda3D and RenderPipelie (from glTF format):
```
python examples/ruby_rose/scene_rp_gltf.py
```

![Preview in Blender](screenshots/preview_blender.png)
![Preview in RenderPipeline](screenshots/preview_rp1.png)


Expected material nodes setup
-----------------------------

![Nodes 1](screenshots/nodes1.png)
![Nodes 2](screenshots/nodes2.png)


NodePath tags setup
-------------------

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

Usage:
```
blend2egg --output x.egg x.blend
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
* Can't export specular map

Usage:
```
blend2egg --output x.gltf x.blend
```
