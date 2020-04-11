from ppb import BaseScene

from survival.player import Player


class Sandbox(BaseScene):
    background_color = 0, 0, 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add(Player())
