from ppb import BaseScene

from survival.enemies import Body
from survival.player import Player
from survival.player import ChargeBox
from survival.utils import asymptotic_average_builder


calc_cam_pos = asymptotic_average_builder(5)


class Sandbox(BaseScene):
    background_color = 0, 0, 0

    def __init__(self, **kwargs):
        super().__init__(pixel_ration=32, **kwargs)
        player = Player()
        self.add(player)
        for x in range(1, 5):
            self.add(ChargeBox(parent=player, value=x))
        for x in range(2, 11, 2):
            self.add(Body(position=(0, x)))

    def on_pre_render(self, event, signal):
        player = next(self.get(kind=Player))
        camera = self.main_camera

        camera.position = calc_cam_pos(camera.position, player.position)
