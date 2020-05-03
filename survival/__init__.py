import ppb

from survival.sandbox import Sandbox
from survival.systems import Controller
from survival.systems import Collider


def run():
    ppb.run(starting_scene=Sandbox, systems=[Controller, Collider])
