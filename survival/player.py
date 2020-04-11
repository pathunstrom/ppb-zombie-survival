from ppb import events
from ppb import Sprite
from ppb.assets import Square

from survival.utils import asymptotic_average_builder

calculate_rotation = asymptotic_average_builder(12)


class Player(Sprite):
    image = Square(200, 55, 40)
    target_facing = None

    def on_mouse_motion(self, event: events.MouseMotion, signal):
        self.target_facing = (event.position - self.position).normalize()

    def on_update(self, event: events.Update, signal):
        if self.target_facing is not None:
            self.facing = calculate_rotation(
                self.facing, self.target_facing
            ).normalize()
