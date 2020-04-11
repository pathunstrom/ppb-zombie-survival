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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = Neutral(self, None)

    def on_button_released(self, event: events.ButtonReleased, signal):
        self.state.on_button_released(event, signal)

    def on_mouse_motion(self, event: events.MouseMotion, signal):
        self.state.on_mouse_motion(event, signal)

    def on_update(self, event: events.Update, signal):
        self.state.on_update(event, signal)


class State:

    def __init__(self, parent, last_state):
        self.parent = parent
        self.last_state = last_state

    def on_button_released(self, event, signal):
        pass

    def on_mouse_motion(self, event, signal):
        pass

    def on_update(self, event, signal):
        pass


class Neutral(State):

    def on_button_released(self, event, signal):
        if event.button == buttons.Primary:
            event.scene.add(
                Hitbox(
                    position=self.parent.position + self.parent.facing * 2
                )
            )

    def on_mouse_motion(self, event, signal):
        self.parent.target_facing = (
                event.position - self.parent.position
        ).normalize()

    def on_update(self, event, signal):
        if self.parent.target_facing is not None:
            self.parent.facing = calculate_rotation(
                self.parent.facing, self.parent.target_facing
            ).normalize()
