from ppb import Sprite
from ppb.assets import Circle, Square


class Body(Sprite):
    image = Circle(79, 140, 105)


class Enemy(Sprite):
    image = Square(117, 163, 128)
    dead = False

    def collided_with(self, other):
        self.dead = True

    def on_update(self, event, signal):
        if self.dead:
            event.scene.remove(self)
            event.scene.add(Body(position=self.position))
