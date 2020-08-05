from dataclasses import dataclass
from typing import Any, Callable

import misbehave
import ppb
from misbehave.common import BaseNode as Node
from misbehave.common import State
from misbehave.decorator import Decorator


__all__ = ['Context', 'ThrowEventOnSuccess', 'BehaviorMixin', 'misbehave']


@dataclass
class Context:
    scene: ppb.BaseScene
    event: ppb.events.Update  # TODO: Figure out if this is the right type hint
    signal: Callable[[Any], None]


class ThrowEventOnSuccess(misbehave.decorator.Decorator):

    def __init__(self, child, *, event_type, get_event_params):
        super().__init__(child)
        self.event_type = event_type
        self.get_event_params = get_event_params

    def __call__(self, actor: 'BehaviorMixin', context: Context) -> State:
        result = self.child(actor, context)
        if result is State.SUCCESS:
            context.signal(self.event_type(*self.get_event_params(actor)))
        return result


class BehaviorMixin(ppb.sprites.BaseSprite):
    behavior_tree: Node

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_update(self, event: ppb.events.Update, signal: Callable[[Any], None]):
        self.behavior_tree(self, Context(event.scene, event, signal))
