from pytest import fixture
from pytest import mark

from ppb import events
from ppb import BaseScene
from ppb import Sprite
from ppb import Vector
from ppb.camera import Camera

from survival.systems import Collider


class CollideCounter(Sprite):
    collided_count = 0
    tagged = "default"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.collided_list = set()

    def collided_with(self, other):
        self.collided_count += 1
        if not isinstance(other, Camera):
            self.collided_list.add(other)

    def __repr__(self):
        return f"<{type(self).__name__} tagged={self.tagged}>"


class Green(CollideCounter):
    size = 4


class Blue(CollideCounter):
    size = 4


class NeedsCollisionScene(BaseScene):
    provide_collision = True


class ExplicityNoCollisionScene(BaseScene):
    provide_collision = False


class ImplicitNoCollisionScene(BaseScene):
    pass


class CollisionsTestSceneOne(NeedsCollisionScene):

    def __init__(self):
        super().__init__()
        self.expect = {}
        first = CollideCounter(position=Vector(0, 0), tagged="first")
        self.expect[first] = {}
        self.expect[first]["count"] = 2
        self.add(first)
        second = CollideCounter(position=Vector(0, .75), tagged="second")
        self.expect[second] = {}
        self.expect[second]["count"] = 1
        self.add(second)
        self.expect[first]["sprites"] = {second}
        self.expect[second]["sprites"] = {first}
        third = CollideCounter(position=Vector(2, 2), tagged="third")
        self.expect[third] = {}
        self.expect[third]["count"] = 0
        self.expect[third]["sprites"] = set()
        self.add(third)


class CollisionsTestSceneTwo(NeedsCollisionScene):
    collision_pairs = [(Green, Blue), (Blue, Blue)]

    def __init__(self):
        super().__init__()
        self.expect = {}
        g1 = Green(tagged="green1")
        g2 = Green(tagged="green2", position=Vector(3, 2))
        b1 = Blue(tagged="blue1", position=Vector(0, 2))
        b2 = Blue(tagged="blue2", position=Vector(-3, 6))

        self.expect[g1] = {
            "count": 1,
            "sprites": {b1}
        }

        self.expect[g2] = {
            "count": 1,
            "sprites": {b1}
        }

        self.expect[b1] = {
            "count": 3,
            "sprites": {g1, g2, b2}
        }

        self.expect[b2] = {
            "count": 1,
            "sprites": {b1}
        }

        self.add(g1)
        self.add(g2)
        self.add(b1)
        self.add(b2)


@fixture
def basic_collider() -> Collider:
    return Collider()


def test_instantiate():
    _ = Collider(collides=lambda x, y: True)
    assert True


@mark.parametrize("scene, expected", [
    [NeedsCollisionScene(), True],
    [ExplicityNoCollisionScene(), False],
    [ImplicitNoCollisionScene(), False]
])
def test_collider_on_scene_started(scene: BaseScene, basic_collider: Collider, expected):

    basic_collider.on_scene_started(events.SceneStarted(scene), lambda x: None)

    assert basic_collider.running == expected


@mark.parametrize("scene, expected", [
    [NeedsCollisionScene(), True],
    [ExplicityNoCollisionScene(), False],
    [ImplicitNoCollisionScene(), False]
])
def test_collider_on_scene_continued(scene: BaseScene, basic_collider: Collider, expected):

    basic_collider.on_scene_continued(events.SceneContinued(scene), lambda x:None)

    assert basic_collider.running == expected


@mark.parametrize("scene, expected", [
    [NeedsCollisionScene(), True],
    [ExplicityNoCollisionScene(), False],
    [ImplicitNoCollisionScene(), False]
])
def test_collider_on_update(basic_collider: Collider, scene: BaseScene, expected):
    basic_collider.set_running(scene)

    basic_collider.on_update(events.Update(0.15, scene), lambda x: None)
    assert basic_collider.primed == expected


@mark.parametrize("scene", [CollisionsTestSceneOne(), CollisionsTestSceneTwo()])
def test_collider_on_idle_collisions(scene: CollisionsTestSceneOne, basic_collider: Collider):
    basic_collider.running = True
    basic_collider.primed = True
    basic_collider.on_idle(events.Idle(0.01, scene), None)

    sprite: CollideCounter
    for sprite, expect in scene.expect.items():
        assert sprite.collided_count == expect["count"], repr(sprite)
        assert sprite.collided_list == expect["sprites"], repr(sprite)
