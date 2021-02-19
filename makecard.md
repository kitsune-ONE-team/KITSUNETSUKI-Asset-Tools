makecard
========

Card maker tool. This is alternative to **egg-texture-cards** included with [Panda3D](https://panda3d.org).


Features
--------

* Makes sprite-based animations, but automatically packs all images into a single spritesheet texture
* Pack multiple animations into single file


Usage
-----

Create a single animation from 4 frames:
```
makecard --frames 4 --fps 10 --output anim.egg --input 1.png 2.png 3.png 4.png
```

Create 2 animations (first animation will have 2 frames, and second one is 3 frames):
```
makecard --frames 2,3 --fps 15 --output anim.egg --input a1.png a2.png b1.png b2.png b3.png
```
