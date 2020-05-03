from pytest import fixture
from pytest import mark

from ppb import events
from ppb import BaseScene

from survival.systems import Collider


class NeedsCollisionScene(BaseScene):
    provide_collision = True


class ExplicityNoCollisionScene(BaseScene):
    provide_collision = False


class ImplicitNoCollisionScene(BaseScene):
    pass


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
