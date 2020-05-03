from dataclasses import dataclass
from time import monotonic
from typing import Tuple

from ppb import Vector
from ppb import Sprite
from ppb import Square


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
