from dataclasses import dataclass
from time import monotonic
from typing import Type

from ppb import buttons as button
from ppb import events
from ppb import Sprite
from ppb import Vector
from ppb.assets import Square
from ppb.flags import DoNotRender

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


class ChargeBox(Sprite):
    """Temporary debug item."""
    parent: 'Player'
    value: int = 4
    idle_image = DoNotRender
    active_image = Square(50, 70, 200)
    active = False
    offsets = [1, 0.33, -0.33, -1]
    size = 0.25

    @property
    def image(self):
        return self.active_image if self.active else self.idle_image

    def on_pre_render(self, event, signal):
        behind = self.parent.facing * -0.8
        home = behind.rotate(-90).scale(0.40)
        self.position = self.parent.position + behind + (home * self.offsets[self.value - 1])
        self.facing = self.parent.facing

    def on_increased_charge_level(self, event: 'IncreasedChargeLevel', signal):
        if event.level >= self.value:
            self.active = True

    def on_charge_ended(self, event: 'ChargeEnded', signal):
        self.active = False


class Player(Sprite):
    image = Square(200, 55, 40)
    target_facing = None
    layer = 5
    dashed_at = None
    charge_level = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = Neutral(self, None)

    def on_button_released(self, event: events.ButtonReleased, signal):
        self.state.on_button_released(event, signal)

    def on_dash_requested(self, event: DashRequested, signal):
        self.state.on_dash_requested(event, signal)

    def on_charge_dash(self, event, signal):
        self.state.on_charge_dash(event, signal)

    def on_mouse_motion(self, event: events.MouseMotion, signal):
        self.state.on_mouse_motion(event, signal)

    def on_update(self, event: events.Update, signal):
        self.state.on_update(event, signal)


# Player States

class State:

    def __init__(self, parent, return_state):
        self.parent = parent
        self.return_state = return_state

    def on_button_released(self, event, signal):
        pass

    def on_charge_dash(self, event, signal):
        pass

    def on_dash_requested(self, event, signal):
        pass

    def on_mouse_motion(self, event, signal):
        self.parent.target_facing = (
                event.position - self.parent.position
        ).normalize()

    def on_update(self, event, signal):
        pass


class ChargeState(State):
    level_timer = 0.25
    level = 0
    state_to_enter: Type

    def __init__(self, parent, return_state):
        super().__init__(parent, return_state)
        self.start_time = monotonic()
        self.levels = [
            self.start_time + (self.level_timer * level)
            for level
            in range(1, 5)
        ]

    def on_update(self, event, signal):
        now = monotonic()
        if self.level < 4 and now >= self.levels[self.level]:
            self.level += 1
            signal(IncreasedChargeLevel(self.level))

    def exit_stance(self, signal):
        self.parent.charge_level = self.level
        self.parent.state = self.state_to_enter(self.parent, self.return_state)
        signal(ChargeEnded(self.level))


class TimedState(State):
    duration = 0.25
    start_time = None

    def __init__(self, parent, return_state):
        super().__init__(parent, return_state)
        self.start_time = monotonic()

    def on_update(self, event, signal):
        now = monotonic()
        if now >= self.start_time + self.duration:
            self.parent.state = self.return_state
            return True


class Dash(TimedState):
    target_change = None
    start_location = None
    duration = 0.25  # TODO: CONFIG
    start_time = None
    dash_lengths = [3, 4, 5, 6]  # TODO: CONFIG

    def on_update(self, event, signal):
        super().on_update(event, signal)
        if self.target_change is None:
            target_location = self.parent.target_facing.scale(self.dash_lengths[self.parent.charge_level - 1])
            self.target_change = target_location
            self.start_location = self.parent.position
        run_time = monotonic() - self.start_time
        self.parent.position = utils.quadratic_ease_out(
            run_time,
            self.start_location,
            self.target_change,
            self.duration
        )


class DashCharge(ChargeState):
    state_to_enter = Dash

    def on_dash_requested(self, event, signal):
        self.parent.dashed_at = monotonic()
        self.exit_stance(signal)


class Neutral(State):
    speed = 3  # TODO: CONFIG
    dash_cool_down = 0.75  # TODO: CONFIG

    def on_button_released(self, event, signal):
        if event.button == button.Primary:
            self.parent.state = Slash(self.parent, self)

    def on_charge_dash(self, event, signal):
        now = monotonic()
        if self.parent.dashed_at is None or self.parent.dashed_at + self.dash_cool_down <= now:
            self.parent.state = DashCharge(self.parent, self)

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


class SwordCharge(ChargeState):
    state_to_enter = Slash

    def on_slash_requested(self, _, signal):
        self.exit_stance(signal)


@dataclass
class IncreasedChargeLevel:
    level: int


@dataclass
class ChargeEnded:
    level: int
