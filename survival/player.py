from time import monotonic

from ppb import buttons as button
from ppb import events
from ppb import Sprite
from ppb.assets import Square

from survival import utils
from survival.enemies import Body

calculate_rotation = utils.asymptotic_average_builder(12)


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
    speed = 3  # TODO: CONFIG

    def on_button_released(self, event, signal):
        if event.button == button.Primary:
            self.parent.state = Slash(self.parent, self)

    def on_mouse_motion(self, event, signal):
        self.parent.target_facing = (
                event.position - self.parent.position
        ).normalize()

    def on_update(self, event, signal):
        if self.parent.target_facing is not None:
            self.parent.facing = calculate_rotation(
                self.parent.facing, self.parent.target_facing
            ).normalize()
        if event.controls.walk:
            self.parent.position += event.controls.walk.scale(self.speed * event.time_delta)


class Slash(State):
    duration = .15  # TODO: CONFIG
    initial_degrees = 60
    change_in_degrees = -80

    def __init__(self, parent, last_state):
        super().__init__(parent, last_state)
        self.start_time = monotonic()

    def on_update(self, event, signal):
        current_time = monotonic()
        if current_time >= self.start_time + self.duration:
            event.scene.add(Body(position=self.parent.position + self.parent.facing))
            self.parent.state = self.last_state
        else:
            run_time = current_time - self.start_time
            current_offset = self.parent.facing.rotate(
                utils.quadratic_ease_in(
                    run_time,
                    self.initial_degrees,
                    self.change_in_degrees,
                    self.duration
                )
            )
            event.scene.add(
                Hitbox(
                    position=self.parent.position + current_offset.scale(1)
                )
            )
