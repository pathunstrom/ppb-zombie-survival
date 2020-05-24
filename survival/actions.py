from dataclasses import dataclass
from time import perf_counter
from typing import Any
from typing import cast

import behavior_tree as bt
from ppb import BaseScene
from ppb import Sprite

from survival import events
from survival import utils
from survival.systems import Controls


__all__ = ['ControlsMove', 'ChangeFacing', 'BuildCharge']


@dataclass
class UpdateEvent:
    time_delta: float
    controls: Controls
    scene: BaseScene


class CheckButtonControl(bt.Node):

    def __init__(self, control_name):
        self.control_name = control_name

    def visit(self, actor: Any, context: bt.Context) -> bt.State:
        event = cast(UpdateEvent, context.event)
        if getattr(event.controls, self.control_name):
            return bt.State.SUCCESS
        else:
            return bt.State.FAILED


class ChangeFacing(bt.Node):

    def __init__(self, percentage=10):
        self.calculate_rotation = utils.asymptotic_average_builder(percentage)

    def visit(self, actor: Any, context: bt.Context) -> bt.State:
        if actor.target_facing is not None:
            actor.facing = self.calculate_rotation(
                actor.facing, actor.target_facing
            ).normalize()
        return bt.State.SUCCESS


class ControlsMove(bt.Node):

    def visit(self, actor: Any, context: bt.Context) -> bt.State:
        event: UpdateEvent = cast(UpdateEvent, context.event)
        if event.controls.walk:
            actor.position += event.controls.walk.scale(actor.speed * event.time_delta)
        return bt.State.SUCCESS


class SlashHurtBoxArc(bt.Node):

    def __init__(self, start_time_attribute, hurtbox):
        self.initial_rotation = 60
        self.change_in_rotation = -80
        self.run_time = .192
        self.start_time_attribute = start_time_attribute
        self.distance_offset = 1
        self.size = 1
        self.hurtbox = hurtbox

    def visit(self, actor: Any, context: bt.Context) -> bt.State:
        run_time = perf_counter() - getattr(actor, self.start_time_attribute)
        offset = actor.facing.rotate(
            utils.quadratic_ease_in(
                run_time,
                self.initial_rotation,
                self.change_in_rotation,
                self.run_time
            )
        ).scale_to(self.distance_offset)
        context.scene.add(self.hurtbox(position=actor.position + offset, intensity=actor.slash_charge))
        if run_time >= self.run_time:
            return bt.State.SUCCESS
        return bt.State.RUNNING


def Slash(hurtbox) -> bt.Node:
    start_time_attribute = "slash_start_time"
    charge_name = "slash_charge"

    def end_charge_level_params(actor):
        yield actor
        yield getattr(actor, charge_name, 0)

    return bt.Sequence(
        bt.Inverter(CheckButtonControl("slash")),
        bt.ThrowEventOnSuccess(bt.CheckValue("slash_charge_start_time"), event_type=events.ChargeEnded, get_event_params=end_charge_level_params),
        bt.SetCurrentTime(start_time_attribute),
        SlashHurtBoxArc(start_time_attribute, hurtbox),
        bt.SetValue("slash_charge_start_time", None),
        bt.SetValue(charge_name, 0)
    )


def BuildCharge(action_name, levels) -> bt.Node:
    """

    :param action_name: Should match the name of the control verb.
    :param levels: an array of time values in ascending order.
    :return: bt.Node
    """
    charge_start_name = f"{action_name}_charge_start_time"
    charge_name = f"{action_name}_charge"

    def increase_charge_level_params(actor):
        yield actor
        yield getattr(actor, charge_name, 0)

    return bt.Sequence(
        bt.ThrowEventOnSuccess(
            bt.SetCurrentTime(charge_start_name),
            event_type=events.ChargeStarted,
            get_event_params=lambda a: [a]
        ),
        bt.Wait(charge_start_name, levels[0]),
        bt.ThrowEventOnSuccess(
            bt.IncreaseValue(charge_name),
            event_type=events.IncreasedChargeLevel,
            get_event_params=increase_charge_level_params
        ),
        bt.Wait(charge_start_name, levels[1]),
        bt.ThrowEventOnSuccess(
            bt.IncreaseValue(charge_name),
            event_type=events.IncreasedChargeLevel,
            get_event_params=increase_charge_level_params
        ),
        bt.Wait(charge_start_name, levels[2]),
        bt.ThrowEventOnSuccess(
            bt.IncreaseValue(charge_name),
            event_type=events.IncreasedChargeLevel,
            get_event_params=increase_charge_level_params
        ),
        bt.Wait(charge_start_name, levels[3]),
        bt.ThrowEventOnSuccess(
            bt.IncreaseValue(charge_name),
            event_type=events.IncreasedChargeLevel,
            get_event_params=increase_charge_level_params
        )
    )
