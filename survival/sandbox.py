from ppb import BaseScene

from ppb import Vector

from survival.player import Player
from survival.player import ChargeBox
from survival.utils import asymptotic_average_builder


calc_cam_pos = asymptotic_average_builder(5)


class Sandbox(BaseScene):
    background_color = 0, 0, 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        player = Player()
        self.add(player)
        for x in range(1, 5):
            self.add(ChargeBox(parent=player, value=x))

    def on_pre_render(self, event, signal):
        player = next(self.get(kind=Player))
        camera = self.main_camera

        camera.position = calc_cam_pos(camera.position, player.position)
