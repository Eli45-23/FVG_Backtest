"""Opt-in position plans; Entry's legacy interface is unchanged."""

from dataclasses import dataclass
from decimal import Decimal as D
from engine.strategy import Entry, ManagementContext


@dataclass(frozen=True)
class TargetLeg:
    quantity: int
    target_r: D | None  # None is a session-close/managed runner.
    name: str = "target"


@dataclass(frozen=True)
class PositionPlan(Entry):
    legs: tuple[TargetLeg, ...] = ()
    break_even_after_tp1: bool = False


@dataclass(frozen=True)
class PositionManagementContext(ManagementContext):
    initial_quantity: int = 1
    remaining_quantity: int = 1
    partial_fills: tuple = ()
