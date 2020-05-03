from dataclasses import dataclass
from itertools import combinations
from itertools import product
from typing import Set
from typing import Tuple

from ppb import Sprite
from ppb.events import Idle
from ppb.events import SceneContinued
from ppb.events import SceneStarted
from ppb.events import Update
from ppb.systemslib import System


@dataclass
class SceneCollisionsDefinition:
    requires: Set[type]
    pairs: Set[Tuple[type, type]]


def does_collide_default(left_sprite, right_sprite):
    return False


def generate_pairs(left_group, right_group):
    if left_group is right_group:
        yield from combinations(left_group, 2)
    else:
        yield from product(left_group, right_group)


def signal_collision(left_sprite, right_sprite):
    try:
        left_sprite.collided_with(right_sprite)
    except TypeError:
        pass

    try:
        right_sprite.collided_with(left_sprite)
    except TypeError:
        pass


class Collider(System):
    running = False
    primed = False
    groups_by_scene = {}

    def __init__(self, *, collides=does_collide_default, **kwargs):
        super().__init__(collides=collides, **kwargs)
        self.collides = collides

    def set_up_definitions(self, scene):
        if scene_pairs := getattr(scene, "collision_pairs", None):
            requires = set()
            pairs = set()
            for a, b in scene_pairs:
                requires.add(a)
                requires.add(b)
                pairs.add((a, b))
        else:
            requires = {Sprite}
            pairs = {Sprite, Sprite}
        self.groups_by_scene[scene] = SceneCollisionsDefinition(requires, pairs)

    def calculate_collision(self, scene):
        if scene not in self.groups_by_scene:
            self.set_up_definitions(scene)
        definitions: SceneCollisionsDefinition = self.groups_by_scene[scene]
        sprite_groups = {t: list(scene.get(kind=t)) for t in definitions.requires}
        for a, b in definitions.pairs:
            for left, right in generate_pairs(sprite_groups[a], sprite_groups[b]):
                if self.collides(left, right):
                    signal_collision(left, right)

    def on_idle(self, idle: Idle, __):
        if self.primed:
            self.calculate_collision(idle.scene)
            self.primed = False

    def on_update(self, _, __):
        if self.running:
            self.primed = True

    def set_running(self, scene):
        self.running = getattr(scene, "provide_collision", False)

    def on_scene_started(self, scene_event: SceneStarted, _):
        self.set_running(scene_event.scene)

    def on_scene_continued(self, scene_event: SceneContinued, _):
        self.set_running(scene_event.scene)
