import behavior_tree as bt
from ppb import Sprite
from ppb import Vector
from ppb.assets import Square

from survival import actions
from survival import events
from survival import utils
from survival.assets import player

calculate_rotation = utils.asymptotic_average_builder(12)


SLASH_LEVEL_1_TIME = 0.4
SLASH_LEVEL_2_TIME = 0.8
SLASH_LEVEL_3_TIME = 1.2
SLASH_LEVEL_4_TIME = 1.6
SLASH_COOL_DOWN = 0.5

SHOOT_LEVEL_1_TIME = 0.4
SHOOT_LEVEL_2_TIME = 0.8
SHOOT_LEVEL_3_TIME = 1.2
SHOOT_LEVEL_4_TIME = 1.6
SHOOT_COOL_DOWN = 1

DASH_LEVEL_1_TIME = 0.4
DASH_LEVEL_2_TIME = 0.8
DASH_LEVEL_3_TIME = 1.2
DASH_LEVEL_4_TIME = 1.6
DASH_COOL_DOWN = 0.75

FACING_NEW_PART_PERCENT = 12

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
        SHOOT_LEVEL_1_TIME,
        SHOOT_LEVEL_2_TIME,
        SHOOT_LEVEL_3_TIME,
        SHOOT_LEVEL_4_TIME
    ]
    shoot_charge = 0
    dash_charge_levels = [
        DASH_LEVEL_1_TIME,
        DASH_LEVEL_2_TIME,
        DASH_LEVEL_3_TIME,
        DASH_LEVEL_4_TIME
    ]
    dash_charge = 0
    behavior_tree = bt.Priority(
        bt.Debounce(
            bt.Priority(
                actions.TakeChargeAction("dash", actions.Dash),
                bt.Concurrent(
                    actions.CheckButtonControl("dash"),
                    actions.BuildCharge("dash", dash_charge_levels)
                )
            ),
            cool_down=DASH_COOL_DOWN
        ),
        bt.Debounce(
            bt.Priority(
                actions.TakeChargeAction("slash", actions.SlashHurtBoxArc),
                bt.Concurrent(  # Build a slash charge
                    actions.CheckButtonControl("slash"),
                    actions.BuildCharge("slash", slash_charge_levels)
                ),
            ),
            cool_down=SLASH_COOL_DOWN
        ),
        bt.Debounce(
            bt.Priority(
                actions.TakeChargeAction("shoot", actions.ReleaseArrow),
                bt.Concurrent(
                    actions.CheckButtonControl("shoot"),
                    actions.CheckButtonControl("shoot"),
                    actions.BuildCharge("shoot", shoot_charge_levels)
                ),
            ),
            cool_down=SHOOT_COOL_DOWN
        ),
        bt.Sequence(
            actions.ControlsMove(),
            actions.ChangeFacing(FACING_NEW_PART_PERCENT),
        )
    )

    def on_mouse_motion(self, event, signal):
        self.target_facing = (
                event.position - self.position
        ).normalize()


class ChargeBox(Sprite):
    """Temporary debug item."""
    parent: 'Player'
    value: int = 4
    idle_image = None
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
