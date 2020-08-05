from dataclasses import dataclass
from time import perf_counter
from typing import Any
from typing import cast

import misbehave as bt
import ppb_misbehave as bt_ppb
from ppb import BaseScene

from survival import events
from survival import hitbox
from survival import utils
from survival.systems import Controls


__all__ = ['ControlsMove', 'ChangeFacing', 'BuildCharge', 'CheckButtonControl']


@dataclass
class UpdateEvent:
    time_delta: float
    controls: Controls
    scene: BaseScene


class CheckButtonControl(bt.common.BaseNode):

    def __init__(self, control_name):
        self.control_name = control_name

    def __call__(self, actor: Any, context: bt_ppb.Context) -> bt.common.State:
        event = cast(UpdateEvent, context.event)
        if getattr(event.controls, self.control_name):
            return bt.common.State.SUCCESS
        else:
            return bt.common.State.FAILED


class ChangeFacing(bt.common.BaseNode):

    def __init__(self, percentage=10):
        self.calculate_rotation = utils.asymptotic_average_builder(percentage)

    def __call__(self, actor: Any, context: bt_ppb.Context) -> bt.common.State:
        if actor.target_facing is not None:
            actor.facing = self.calculate_rotation(
                actor.facing, actor.target_facing
            ).normalize()
        return bt.common.State.SUCCESS


class ControlsMove(bt.common.BaseNode):

    def __call__(self, actor: Any, context: bt_ppb.Context) -> bt.common.State:
        event: UpdateEvent = cast(UpdateEvent, context.event)
        if event.controls.walk:
            actor.position += event.controls.walk.scale(actor.speed * event.time_delta)
        return bt.common.State.SUCCESS


class PrepareDash(bt.common.BaseNode):
    dash_lengths = [3, 4.5, 6.75, 10, 14]

    def __call__(self, actor: Any, context: bt_ppb.Context) -> bt.common.State:
        actor.position_change = actor.target_facing.normalize() * self.dash_lengths[actor.dash_charge]
        actor.dash_start_position = actor.position
        print(f"Change: {actor.position_change.length}")
        return bt.common.State.SUCCESS


class DashMove(bt.common.BaseNode):
    duration = 0.25

    def __init__(self, start_time_attribute):
        self.start_time_attribute = start_time_attribute

    def __call__(self, actor: Any, context: bt_ppb.Context) -> bt.common.State:
        run_time = perf_counter() - getattr(actor, self.start_time_attribute)
        if run_time >= self.duration:
            actor.position = actor.dash_start_position + actor.position_change
            return bt.common.State.SUCCESS
        else:
            actor.position = utils.quadratic_ease_out(
                run_time,
                actor.dash_start_position,
                actor.position_change,
                self.duration
            )
            return bt.common.State.RUNNING


def Dash(start_time_attribute):
    return bt.selector.Sequence(
        PrepareDash(),
        DashMove(start_time_attribute)
    )


class SlashHurtBoxArc(bt.common.BaseNode):

    def __init__(self, start_time_attribute):
        self.initial_rotation = 60
        self.change_in_rotation = -80
        self.run_time = .192
        self.start_time_attribute = start_time_attribute
        self.distance_offset = 1
        self.size = 1

    def __call__(self, actor: Any, context: bt_ppb.Context) -> bt.common.State:
        run_time = perf_counter() - getattr(actor, self.start_time_attribute)
        offset = actor.facing.rotate(
            utils.quadratic_ease_in(
                run_time,
                self.initial_rotation,
                self.change_in_rotation,
                self.run_time
            )
        ).scale_to(self.distance_offset)
        context.scene.add(hitbox.PlayerHurtBox(position=actor.position + offset, intensity=actor.slash_charge))
        if run_time >= self.run_time:
            return bt.common.State.SUCCESS
        return bt.common.State.RUNNING


class ReleaseArrow(bt.common.BaseNode):

    def __init__(self, start_time_attribute):
        super().__init__()

    def __call__(self, actor: Any, context: bt_ppb.Context) -> bt.common.State:
        target = actor.position + actor.facing.scale(actor.shoot_charge * 1.5 + 2)
        origin = actor.position
        context.scene.add(hitbox.Arrow(
            target=target,
            origin=origin,
            position=origin,
            facing=-actor.facing,
            intensity=actor.shoot_charge + 1
        ))
        return bt.common.State.SUCCESS


def TakeChargeAction(name, action, recovery_time=.016):
    start_time_attribute = f"{name}_start_time"
    charge_name_attr = f"{name}_charge"
    charge_time_start_attr = f"{name}_charge_start_time"

    def end_charge_level_params(actor):
        yield actor
        yield getattr(actor, charge_name_attr, 0)

    return bt.selector.Sequence(
        bt.decorator.Inverter(CheckButtonControl(name)),
        bt_ppb.ThrowEventOnSuccess(
            bt.action.CheckValue(charge_time_start_attr),
            event_type=events.ChargeEnded,
            get_event_params=end_charge_level_params
        ),
        bt.action.SetCurrentTime(start_time_attribute),
        action(start_time_attribute),
        bt.action.SetValue(charge_time_start_attr, None),
        bt.action.SetValue(charge_name_attr, 0),
        bt.action.SetCurrentTime("charge_action_recovery"),
        bt.action.Wait("charge_action_recovery", recovery_time)
    )


def BuildCharge(action_name, levels) -> bt.common.BaseNode:
    """

    :param action_name: Should match the name of the control verb.
    :param levels: an array of time values in ascending order.
    :return: bt.common.BaseNode
    """
    charge_start_name = f"{action_name}_charge_start_time"
    charge_name = f"{action_name}_charge"

    def increase_charge_level_params(actor):
        yield actor
        yield getattr(actor, charge_name, 0)

    return bt.selector.Sequence(
        bt_ppb.ThrowEventOnSuccess(
            bt.action.SetCurrentTime(charge_start_name),
            event_type=events.ChargeStarted,
            get_event_params=lambda a: [a]
        ),
        bt.action.Wait(charge_start_name, levels[0]),
        bt_ppb.ThrowEventOnSuccess(
            bt.action.IncreaseValue(charge_name),
            event_type=events.IncreasedChargeLevel,
            get_event_params=increase_charge_level_params
        ),
        bt.action.Wait(charge_start_name, levels[1]),
        bt_ppb.ThrowEventOnSuccess(
            bt.action.IncreaseValue(charge_name),
            event_type=events.IncreasedChargeLevel,
            get_event_params=increase_charge_level_params
        ),
        bt.action.Wait(charge_start_name, levels[2]),
        bt_ppb.ThrowEventOnSuccess(
            bt.action.IncreaseValue(charge_name),
            event_type=events.IncreasedChargeLevel,
            get_event_params=increase_charge_level_params
        ),
        bt.action.Wait(charge_start_name, levels[3]),
        bt_ppb.ThrowEventOnSuccess(
            bt.action.IncreaseValue(charge_name),
            event_type=events.IncreasedChargeLevel,
            get_event_params=increase_charge_level_params
        ),
        bt.action.Idle()
    )
