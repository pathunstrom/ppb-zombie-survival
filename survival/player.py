from ppb import buttons
from ppb import events
from ppb import Sprite
from ppb.assets import Square

from survival.utils import asymptotic_average_builder

calculate_rotation = asymptotic_average_builder(12)


class Hitbox(Sprite):
    image = Square(150, 40, 40)


class Player(Sprite):
    image = Square(200, 55, 40)
    target_facing = None

    def on_button_released(self, event: events.ButtonReleased, signal):
        if event.button == buttons.Primary:
            event.scene.add(
                Hitbox(
                    position=self.position + self.facing * 2
                )
            )

    def on_mouse_motion(self, event: events.MouseMotion, signal):
        self.target_facing = (event.position - self.position).normalize()

    def on_update(self, event: events.Update, signal):
        if self.target_facing is not None:
            self.facing = calculate_rotation(
                self.facing, self.target_facing
            ).normalize()
