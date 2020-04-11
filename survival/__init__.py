import ppb

from survival.sandbox import Sandbox
from survival.systems import Controller


def run():
    ppb.run(starting_scene=Sandbox, systems=[Controller])
