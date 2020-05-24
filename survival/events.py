from dataclasses import dataclass
from typing import Any


@dataclass
class ChargeStarted:
    actor: Any


@dataclass
class ChargeEnded:
    actor: Any
    level: int


@dataclass
class IncreasedChargeLevel:
    actor: Any
    level: int
