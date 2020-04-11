from ppb import events as ppb_events
from ppb import keycodes as key
from ppb import Vector
from ppb.engine import GameEngine
from ppb.systemslib import System


class Controls:

    def __init__(self, walk: Vector):
        """

        :param walk: A vector with the X value of [-1, 1] and y value of
        [-1, 1]
        """
        self.walk = walk


class Controller(System):
    horizontal = 0
    vertical = 0

    def __init__(self, *, engine: GameEngine, **kwargs):
        super().__init__(**kwargs)
        engine.register(..., self.add_controls)

    def add_controls(self, event):
        event.controls = Controls(
            walk=Vector(self.horizontal, self.vertical)
        )

    def on_key_pressed(self, event: ppb_events.KeyPressed, signal):
        if event.key == key.W:
            self.vertical += 1
        elif event.key == key.S:
            self.vertical += -1
        elif event.key == key.A:
            self.horizontal += -1
        elif event.key == key.D:
            self.horizontal += 1

    def on_key_released(self, event: ppb_events.KeyReleased, signal):
        if event.key == key.W:
            self.vertical += -1
        elif event.key == key.S:
            self.vertical += 1
        elif event.key == key.A:
            self.horizontal += 1
        elif event.key == key.D:
            self.horizontal += -1