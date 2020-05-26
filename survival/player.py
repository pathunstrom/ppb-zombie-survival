from dataclasses import dataclass
from time import monotonic
from typing import Any
from typing import Type

import behavior_tree as bt
from ppb import events as ppb_events
from ppb import Sprite
from ppb import Vector
from ppb.assets import Square
from ppb.flags import DoNotRender

from survival import actions
from survival import events
from survival import utils
from survival import systems as control_events
from survival.assets import player
from survival.hitbox import PlayerHurtBox

calculate_rotation = utils.asymptotic_average_builder(12)


SLASH_LEVEL_1_TIME = 0.4
SLASH_LEVEL_2_TIME = 0.8
SLASH_LEVEL_3_TIME = 1.2
SLASH_LEVEL_4_TIME = 1.6

ARROW_LEVEL_1_TIME = 0.4
ARROW_LEVEL_2_TIME = 0.8
ARROW_LEVEL_3_TIME = 1.2
ARROW_LEVEL_4_TIME = 1.6


class BTPlayer(Sprite, bt.BehaviorMixin):
    image = player
    basis = Vector(0, 1)
    speed = 3
    target_facing = None
    slash_charge_levels = [
        SLASH_LEVEL_1_TIME,
        SLASH_LEVEL_2_TIME,
        SLASH_LEVEL_3_TIME,
        SLASH_LEVEL_4_TIME
    ]
    slash_charge = 0
    shoot_charge_levels = [
        ARROW_LEVEL_1_TIME,
        ARROW_LEVEL_2_TIME,
        ARROW_LEVEL_3_TIME,
        ARROW_LEVEL_4_TIME
    ]
    shoot_charge = 0
    behavior_tree = bt.Priority(
        bt.Priority(
            actions.TakeChargeAction("slash", actions.SlashHurtBoxArc),
            bt.Concurrent(  # Build a slash charge
                actions.CheckButtonControl("slash"),
                actions.BuildCharge("slash", slash_charge_levels)
            ),
        ),
        bt.Priority(
            actions.TakeChargeAction("shoot", actions.ReleaseArrow),
            bt.Concurrent(
                actions.CheckButtonControl("shoot"),
                actions.BuildCharge("shoot", shoot_charge_levels)
            )
        ),
        bt.Sequence(
            actions.ControlsMove(),
            actions.ChangeFacing(12),  # TODO: Configure
        )
    )

    def on_mouse_motion(self, event, signal):
        self.target_facing = (
                event.position - self.position
        ).normalize()


@dataclass
class UpdateInterface:
    scene: Any
    controls: control_events.Controls




class ChargeBox(Sprite):
    """Temporary debug item."""
    parent: 'Player'
    value: int = 4
    idle_image = DoNotRender
    active_image = Square(50, 70, 200)
    active = False
    offsets = [1, 0.33, -0.33, -1]  # These are magic and modified by eye.
    size = 0.25
    layer = 20

    @property
    def image(self):
        return self.active_image if self.active else self.idle_image

    def on_pre_render(self, _, __):
        behind = self.parent.facing * -0.8
        home = behind.rotate(-90).scale(0.40)
        self.position = self.parent.position + behind + (home * self.offsets[self.value - 1])
        self.facing = self.parent.facing

    def on_increased_charge_level(self, event: events.IncreasedChargeLevel, _):
        if event.level >= self.value:
            self.active = True

    def on_charge_ended(self, _: events.ChargeEnded, __):
        self.active = False


class Player(Sprite):
    image = player
    target_facing = None
    layer = 5
    dashed_at = None
    shot_at = None
    slashed_at = None
    charge_level = 0
    basis = Vector(0, 1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = Neutral(self, None)

    def on_charge_slash(self, event, signal):
        self.state.on_charge_slash(event, signal)

    def on_charge_dash(self, event, signal):
        self.state.on_charge_dash(event, signal)

    def on_dash_requested(self, event: control_events.DashRequested, signal):
        self.state.on_dash_requested(event, signal)

    def on_draw_bow(self, event: control_events.DrawBow, signal):
        self.state.on_draw_bow(event, signal)

    def on_release_bow(self, event: control_events.ReleaseBow, signal):
        self.state.on_release_bow(event, signal)

    def on_slash_requested(self, event: control_events.SlashRequested, signal):
        self.state.on_slash_requested(event, signal)

    def on_mouse_motion(self, event: ppb_events.MouseMotion, signal):
        self.state.on_mouse_motion(event, signal)

    def on_update(self, event: UpdateInterface, signal):
        self.state.on_update(event, signal)


# Player States

class State:

    def __init__(self, parent, return_state):
        self.parent = parent
        self.return_state = return_state

    def on_charge_dash(self, event, signal):
        pass

    def on_charge_slash(self, event, signal):
        pass

    def on_dash_requested(self, event, signal):
        pass

    def on_draw_bow(self, event, signal):
        pass

    def on_release_bow(self, event, signal):
        pass

    def on_slash_requested(self, event, signal):
        pass

    def on_mouse_motion(self, event, _):
        self.parent.target_facing = (
                event.position - self.parent.position
        ).normalize()

    def on_update(self, event, signal):
        pass


class ChargeState(State):
    level_timer = 0.4
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
            signal(events.IncreasedChargeLevel(self.parent, self.level))

    def exit_stance(self, signal):
        self.parent.charge_level = self.level
        self.parent.state = self.state_to_enter(self.parent, self.return_state)
        signal(events.ChargeEnded(self.parent, self.level))


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
    dash_lengths = [2, 3, 4, 5, 6]  # TODO: CONFIG

    def on_update(self, event, signal):
        super().on_update(event, signal)
        if self.target_change is None:
            target_location = self.parent.target_facing.scale(self.dash_lengths[self.parent.charge_level])
            self.target_change = target_location
            self.start_location = self.parent.position
            self.parent.charge_level = 0
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


class StowBow(TimedState):

    def on_update(self, event: UpdateInterface, __):
        target = self.parent.position + self.parent.facing.scale(self.parent.charge_level * 1.5 + 2)
        origin = self.parent.position
        event.scene.add(Arrow(
            target=target,
            origin=origin,
            position=origin,
            facing=-self.parent.facing,
            intensity=self.parent.charge_level + 1
        ))
        self.parent.state = self.return_state


class Drawing(ChargeState):
    state_to_enter = StowBow

    def on_release_bow(self, event, signal):
        self.parent.shot_at = monotonic()
        self.exit_stance(signal)


class Neutral(State):
    speed = 3  # TODO: CONFIG
    dash_cool_down = 0.75  # TODO: CONFIG
    shot_cool_down = 1  # TODO: CONFIG
    slash_cool_down = 0.5  # TODO: CONFIG

    def on_charge_slash(self, event, signal):
        now = monotonic()
        if self.parent.slashed_at is None or self.parent.slashed_at + self.slash_cool_down <= now:
            self.parent.state = SwordCharge(self.parent, self)

    def on_charge_dash(self, event, signal):
        now = monotonic()
        if self.parent.dashed_at is None or self.parent.dashed_at + self.dash_cool_down <= now:
            self.parent.state = DashCharge(self.parent, self)

    def on_draw_bow(self, event, signal):
        now = monotonic()
        if self.parent.shot_at is None or self.parent.shot_at + self.shot_cool_down <= now:
            self.parent.state = Drawing(self.parent, self)

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
        super().on_update(event, signal)
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
            PlayerHurtBox(
                position=self.parent.position + current_offset.scale(1),
                intensity=self.parent.charge_level + 1
            )
        )


class SwordCharge(ChargeState):
    state_to_enter = Slash

    def on_slash_requested(self, _, signal):
        self.parent.slashed_at = monotonic()
        self.exit_stance(signal)
