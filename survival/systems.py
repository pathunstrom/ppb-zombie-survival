from dataclasses import dataclass

from ppb import buttons as button
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
        if event.key is key.W:
            self.vertical += 1
        elif event.key is key.S:
            self.vertical += -1
        elif event.key is key.A:
            self.horizontal += -1
        elif event.key is key.D:
            self.horizontal += 1
        elif event.key is key.Space:
            signal(ChargeDash())

    def on_key_released(self, event: ppb_events.KeyReleased, signal):
        if event.key is key.W:
            self.vertical += -1
        elif event.key is key.S:
            self.vertical += 1
        elif event.key is key.A:
            self.horizontal += 1
        elif event.key is key.D:
            self.horizontal += -1
        elif event.key is key.Space:
            signal(DashRequested())

    @staticmethod
    def on_button_pressed(event: ppb_events.ButtonPressed, signal):
        if event.button is button.Primary:
            signal(ChargeSlash())
        elif event.button is button.Secondary:
            signal(DrawBow())

    @staticmethod
    def on_button_released(event: ppb_events.ButtonReleased, signal):
        if event.button is button.Primary:
            signal(SlashRequested())
        elif event.button is button.Secondary:
            signal(ReleaseBow())


@dataclass
class DrawBow:
    scene = None
    controls: Controls = None


@dataclass
class ReleaseBow:
    scene = None
    controls: Controls = None


@dataclass
class ChargeDash:
    scene = None
    controls: Controls = None


@dataclass
class DashRequested:
    scene = None
    controls: Controls = None


@dataclass
class ChargeSlash:
    scene = None
    controls: Controls = None


@dataclass
class SlashRequested:
    scene = None
    controls: Controls = None
