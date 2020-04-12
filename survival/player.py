from time import monotonic

from ppb import buttons as button
from ppb import events
from ppb import Sprite
from ppb.assets import Square

from survival import utils
from survival.enemies import Body
from survival.systems import DashRequested

calculate_rotation = utils.asymptotic_average_builder(12)


class HurtBox(Sprite):
    image = Square(150, 40, 40)
    life_span = .20  # TODO: CONFIG

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start = monotonic()

    def on_update(self, event, _):
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

    def on_dash_requested(self, event: DashRequested, signal):
        self.state.on_dash_requested(event, signal)

    def on_mouse_motion(self, event: events.MouseMotion, signal):
        self.state.on_mouse_motion(event, signal)

    def on_update(self, event: events.Update, signal):
        self.state.on_update(event, signal)


class State:

    def __init__(self, parent, return_state):
        self.parent = parent
        self.last_state = return_state

    def on_button_released(self, event, signal):
        pass

    def on_dash_requested(self, event, signal):
        pass

    def on_mouse_motion(self, event, signal):
        pass

    def on_update(self, event, signal):
        pass


class TimedState(State):
    duration = 0.25
    start_time = None

    def __init__(self, parent, return_state):
        super().__init__(parent, return_state)
        self.start_time = monotonic()

    def on_update(self, event, signal):
        now = monotonic()
        if now >= self.start_time + self.duration:
            self.parent.state = self.last_state
            return True


class Dash(TimedState):
    target_change = None
    start_location = None
    duration = 0.25  # TODO: CONFIG
    start_time = None
    dash_length = 4  # TODO: CONFIG

    def on_update(self, event, signal):
        super().on_update(event, signal)
        if self.target_change is None:
            target_location = self.parent.target_facing.scale(self.dash_length)
            self.target_change = target_location
            self.start_location = self.parent.position
        run_time = monotonic() - self.start_time
        self.parent.position = utils.quadratic_ease_out(
            run_time,
            self.start_location,
            self.target_change,
            self.duration
        )


class Neutral(State):
    speed = 3  # TODO: CONFIG
    dash_cool_down = 0.75  # TODO: CONFIG
    dashed_at = None

    def on_button_released(self, event, signal):
        if event.button == button.Primary:
            self.parent.state = Slash(self.parent, self)

    def on_dash_requested(self, event, signal):
        now = monotonic()
        if self.dashed_at is None or self.dashed_at + self.dash_cool_down <= now:
            self.dashed_at = now
            self.parent.state = Dash(self.parent, self)

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


class Slash(TimedState):
    duration = .18  # TODO: CONFIG
    initial_degrees = 60  # TODO: CONFIG
    change_in_degrees = -80  # TODO: CONFIG

    def __init__(self, parent, return_state):
        super().__init__(parent, return_state)
        self.start_time = monotonic()

    def on_update(self, event, signal):
        did_end = super().on_update(event, signal)
        if did_end:
            event.scene.add(Body(position=self.parent.position + self.parent.facing))
        run_time = monotonic() - self.start_time
        current_offset = self.parent.facing.rotate(
            utils.quadratic_ease_in(
                run_time,
                self.initial_degrees,
                self.change_in_degrees,
                self.duration
            )
        )
        event.scene.add(
            HurtBox(
                position=self.parent.position + current_offset.scale(1)
            )
        )
