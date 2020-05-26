from dataclasses import dataclass
from time import monotonic
from typing import Tuple

from ppb import Vector
from ppb import Sprite
from ppb import Square
from ppb import Triangle


@dataclass
class HitBox:
    """
    A hit box to define a sprite area different from the sprite's size and
    shape.

    Is a rectangle. Can use Sprite.hit_box = HitBox(Sprite.top.left, Sprite.bottom.right)
    """
    definition: Tuple[Vector, Vector]


class HurtBox(Sprite):
    image = Square(150, 40, 40)
    life_span = .20  # TODO: CONFIG
    layer = -10
    intensity = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start = monotonic()

    def on_update(self, event, _):
        if monotonic() >= self.start + self.life_span:
            event.scene.remove(self)


class PlayerHurtBox(HurtBox):
    image = Square(150, 40, 40)


class EnemyHurtBox(HurtBox):
    image = Square(150, 75, 30)


class Arrow(PlayerHurtBox):
    image = Triangle(224, 218, 56)
    target = Vector(0, 4)
    origin = Vector(0, 0)
    speed = 8
    size = 0.25
    layer = 20

    def on_update(self, event, _):
        self.position += (self.target - self.position).scale_to(self.speed) * event.time_delta
        if (self.target - self.origin).length <= (self.origin - self.position).length:
            event.scene.remove(self)
