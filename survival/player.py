from time import monotonic

from ppb import buttons as button
from ppb import events
from ppb import keycodes as key
from ppb import Sprite
from ppb import Vector
from ppb.assets import Square

from survival.utils import asymptotic_average_builder

calculate_rotation = asymptotic_average_builder(12)


class Hitbox(Sprite):
    image = Square(150, 40, 40)
    life_span = .20

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start = monotonic()

    def on_update(self, event, signal):
        if monotonic() >= self.start + self.life_span:
            event.scene.remove(self)


class Player(Sprite):
    image = Square(200, 55, 40)
    target_facing = None
    layer = 5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = Neutral(self, None)

    def on_button_released(self, event: events.ButtonReleased, signal):
        self.state.on_button_released(event, signal)

    def on_key_pressed(self, event: events.KeyPressed, signal):
        self.state.on_key_pressed(event, signal)

    def on_key_released(self, event: events.KeyReleased, signal):
        self.state.on_key_released(event, signal)

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

    def on_key_pressed(self, event, signal):
        pass

    def on_key_released(self, event, signal):
        pass

    def on_mouse_motion(self, event, signal):
        pass

    def on_update(self, event, signal):
        pass


class Neutral(State):
    speed = 3  # TODO: CONFIG
    vertical_value = 0
    horizontal_value = 0

    def on_button_released(self, event, signal):
        if event.button == button.Primary:
            event.scene.add(
                Hitbox(
                    position=self.parent.position + self.parent.facing * 2
                )
            )

    def on_key_pressed(self, event, signal):
        if event.key == key.W:
            self.vertical_value += 1
        elif event.key == key.S:
            self.vertical_value += -1
        elif event.key == key.A:
            self.horizontal_value += -1
        elif event.key == key.D:
            self.horizontal_value += 1

    def on_key_released(self, event, signal):
        if event.key == key.W:
            self.vertical_value += -1
        elif event.key == key.S:
            self.vertical_value += 1
        elif event.key == key.A:
            self.horizontal_value += 1
        elif event.key == key.D:
            self.horizontal_value += -1

    def on_mouse_motion(self, event, signal):
        self.parent.target_facing = (
                event.position - self.parent.position
        ).normalize()

    def on_update(self, event, signal):
        if self.parent.target_facing is not None:
            self.parent.facing = calculate_rotation(
                self.parent.facing, self.parent.target_facing
            ).normalize()
        direction_vector = Vector(self.horizontal_value, self.vertical_value)
        if direction_vector:
            self.parent.position += direction_vector.scale(self.speed * event.time_delta)
