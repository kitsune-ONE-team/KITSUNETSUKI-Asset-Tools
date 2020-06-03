#!/usr/bin/env python3

from panda3d.core import load_prc_file_data, Vec3

load_prc_file_data("", '''
win-size 1600 900
''')

from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor


class Demo(ShowBase):
    def __init__(self):
        from rpcore import RenderPipeline, PointLight
        from rpcore.util.movement_controller import MovementController

        self.render_pipeline = RenderPipeline()
        self.render_pipeline.create(self)

        self.render_pipeline.daytime_mgr.time = '08:00'

        self.point_light = PointLight()
        self.point_light.set_color(1, 1, 0.9)
        self.point_light.set_energy(10)
        self.point_light.set_pos(0, 5, 2)
        self.point_light.set_radius(20)
        self.render_pipeline.add_light(self.point_light)

        # load animations from EGG, because glTF animations aren't supported
        self.ruby_scene = self.loader.load_model('ruby.gltf')
        self.ruby = Actor(self.ruby_scene.find('+Character'), {'idle': 'ruby_anim.egg'})
        self.ruby.reparent_to(self.render)
        self.ruby.set_h(180)
        self.ruby.loop('idle')

        self.controller = MovementController(self)
        self.controller.set_initial_position_hpr(
            Vec3(0, 5, 1.75),  # position
            Vec3(180, -10, 0))  # hpr
        self.controller.setup()


if __name__ == '__main__':
    demo = Demo()
    demo.run()
