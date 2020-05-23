from typing import Union

from ppb import Sprite
from ppb.events import Update

from survival.assets import zombie, dead_zombie
from survival.hitbox import PlayerHurtBox


class Body(Sprite):
    image = dead_zombie


class Enemy(Sprite):
    image = zombie
    dead = False
    push_velocity = None
    stunned = False

    def collided_with(self, other: Union[PlayerHurtBox, 'Enemy']):
        if isinstance(other, PlayerHurtBox):
            if self.push_velocity is None:
                self.push_velocity = (self.position - other.position).scale_to(other.intensity ** 1.75)
                self.stunned = True
        elif isinstance(other, Enemy):
            if self.stunned and not other.stunned and not other.dead:
                self.dead = True

    def on_update(self, event: Update, signal):
        if self.dead:
            event.scene.remove(self)
            event.scene.add(Body(position=self.position))
        if self.push_velocity is not None:
            self.position += self.push_velocity * event.time_delta
            self.push_velocity *= .30 ** event.time_delta
            if self.push_velocity.length <= 0.1:
                self.push_velocity = None
                self.stunned = False
