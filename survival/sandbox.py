from ppb import BaseScene

from survival.player import Player
from survival.utils import asymptotic_average_builder


calc_cam_pos = asymptotic_average_builder(5)


class Sandbox(BaseScene):
    background_color = 0, 0, 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add(Player())

    def on_pre_render(self, event, signal):
        player = next(self.get(kind=Player))
        camera = self.main_camera

        camera.position = calc_cam_pos(camera.position, player.position)
