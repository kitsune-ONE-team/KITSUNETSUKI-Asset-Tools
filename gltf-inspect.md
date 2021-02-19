gltf-inspect
============

Tiny tool for browsing [glTF](https://github.com/KhronosGroup/glTF) file's structure.


Usage
-----

```
gltf-inspect ruby_mesh.gltf
```


Output
------

```
 [R] Scene
  + [S] Object <RST>
  |  + [J] Bip001_Root <RST>
  |  |  + [J] Bip001_Pelvis <RST>
  |  |  |  + [J] Bip001_Belt <RST>
  |  |  |  |  + [J] Bip001_BeltBck <RST>
  |  |  |  |  + [J] Bip001_BeltFrt <RST>
  |  |  |  |  + [J] Bip001_Belt_L <RST>
  |  |  |  |  |  + [J] Bip001_Round <RST>
  |  |  |  |  |  + [J] Bip001_Round1 <RST>
  |  |  |  |  |  + [J] Bip001_Round2 <RST>
  |  |  |  |  |  + [J] Bip001_Round3 <RST>
  |  |  |  |  |  + [J] Bip001_Round4 <RST>
  |  |  |  |  |  + [J] Bip001_Round5 <RST>
  |  |  |  |  |  + [J] Bip001_Round6 <RST>
  |  |  |  |  + [J] Bip001_Belt_R <RST>
  |  |  |  |  + [J] Bip001_Mount_Belt <RST>

...

  |  |  |  + [J] Bip001_Thigh_L <RST>
  |  |  |  |  + [J] Bip001_Thigh1_L <RST>
  |  |  |  |  |  + [J] Bip001_Thigh2_L <RST>
  |  |  |  |  |  |  + [J] Bip001_Thigh3_L <RST>
  |  |  |  |  |  |  |  + [J] Bip001_Calf_L <RST>
  |  |  |  |  |  |  |  |  + [J] Bip001_Calf1_L <RST>
  |  |  |  |  |  |  |  |  |  + [J] Bip001_Calf2_L <RST>
  |  |  |  |  |  |  |  |  |  |  + [J] Bip001_Calf3_L <RST>
  |  |  |  |  |  |  |  |  |  |  |  + [J] Bip001_Foot_L <RST>
  |  |  |  |  |  |  |  |  |  |  |  |  + [J] Bip001_Toe_L <RST>
  |  |  |  |  |  |  |  |  |  |  |  |  |  + [J] Bip001_ToeNub_L <RST>
  |  |  |  |  |  |  |  + [J] Bip001_Knee_L <RST>
  |  |  |  + [J] Bip001_Thigh_R <RST>
  |  |  |  |  + [J] Bip001_Thigh1_R <RST>
  |  |  |  |  |  + [J] Bip001_Thigh2_R <RST>
  |  |  |  |  |  |  + [J] Bip001_Thigh3_R <RST>
  |  |  |  |  |  |  |  + [J] Bip001_Calf_R <RST>
  |  |  |  |  |  |  |  |  + [J] Bip001_Calf1_R <RST>
  |  |  |  |  |  |  |  |  |  + [J] Bip001_Calf2_R <RST>
  |  |  |  |  |  |  |  |  |  |  + [J] Bip001_Calf3_R <RST>
  |  |  |  |  |  |  |  |  |  |  |  + [J] Bip001_Foot_R <RST>
  |  |  |  |  |  |  |  |  |  |  |  |  + [J] Bip001_Toe_R <RST>
  |  |  |  |  |  |  |  |  |  |  |  |  |  + [J] Bip001_ToeNub_R <RST>
  |  |  |  |  |  |  |  + [J] Bip001_Knee_R <RST>
  |  + [N] mesh_bullet {skin: Object (368 joints), mesh: mesh_bullet}
  |  + [N] mesh_bullet1 {skin: Object (368 joints), mesh: mesh_bullet1}
  |  + [N] mesh_crescentRose {skin: Object (368 joints), mesh: mesh_crescentRose}
  |  + [N] mesh_ruby {skin: Object (368 joints), mesh: mesh_ruby}
  |  + [N] mesh_rubyBelt {skin: Object (368 joints), mesh: mesh_rubyBelt}
  |  + [N] mesh_rubyCloak {skin: Object (368 joints), mesh: mesh_rubyCloak}
  |  + [N] mesh_rubyEyeAO {skin: Object (368 joints), mesh: mesh_rubyEyeAO}
  |  + [N] mesh_rubyEyes {skin: Object (368 joints), mesh: mesh_rubyEyes}
  |  + [N] mesh_rubyHair {skin: Object (368 joints), mesh: mesh_rubyHair}
  |  + [N] mesh_rubyPouch {skin: Object (368 joints), mesh: mesh_rubyPouch}
```
