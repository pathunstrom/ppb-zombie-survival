from ppb import Sprite
from ppb.assets import Circle, Square
from ppb.events import Update

from survival.hitbox import PlayerHurtBox


class Body(Sprite):
    image = Circle(79, 140, 105)


class Enemy(Sprite):
    image = Square(117, 163, 128)
    dead = False
    push_velocity = None
    stunned = False

    def collided_with(self, other: PlayerHurtBox):
        if self.push_velocity is None:
            self.push_velocity = (self.position - other.position).scale_to(other.intensity * 3)
            self.stunned = True

    def on_update(self, event:Update, signal):
        if self.dead:
            event.scene.remove(self)
            event.scene.add(Body(position=self.position))
        if self.push_velocity is not None:
            self.position += self.push_velocity * event.time_delta
            self.push_velocity *= .30 ** event.time_delta
            if self.push_velocity.length <= 0.1:
                self.push_velocity = None
                self.stunned = False
