"""Public Strategy Research Lab SDK v1. No internal imports required."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal
import re


@dataclass(frozen=True)
class Input:
    id: str
    label: str
    type: str
    default: object
    min: float | None = None
    max: float | None = None
    step: float | None = None
    choices: tuple = ()
    description: str = ""

    def validate(self, value):
        if self.type == "bool":
            if not isinstance(value, bool):
                raise ValueError(f"{self.id}: expected boolean")
        elif self.type in ("float", "int"):
            if isinstance(value, bool):
                raise ValueError(f"{self.id}: expected number")
            try:
                n = Decimal(str(value))
            except Exception:
                raise ValueError(f"{self.id}: expected number") from None
            if not n.is_finite() or (self.type == "int" and n != int(n)):
                raise ValueError(f"{self.id}: invalid number")
            if self.min is not None and n < Decimal(str(self.min)):
                raise ValueError(f"{self.id}: below minimum")
            if self.max is not None and n > Decimal(str(self.max)):
                raise ValueError(f"{self.id}: above maximum")
            if (
                self.step is not None
                and (n - Decimal(str(self.min or 0))) % Decimal(str(self.step)) != 0
            ):
                raise ValueError(f"{self.id}: off step")
            value = int(n) if self.type == "int" else float(n)
        else:
            if not isinstance(value, str):
                raise ValueError(f"{self.id}: expected text")
            if self.type == "choice" and value not in self.choices:
                raise ValueError(f"{self.id}: invalid choice")
            if self.type == "time" and not re.fullmatch(
                r"([01]\d|2[0-3]):[0-5]\d", value
            ):
                raise ValueError(f"{self.id}: expected HH:MM")
            if self.type == "session":
                bits = value.split("-")
                if len(bits) != 2 or any(
                    not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", s) for s in bits
                ):
                    raise ValueError(f"{self.id}: expected HH:MM-HH:MM")
        return value


def Float(id, label, default, **kw):
    return Input(id, label, "float", default, **kw)


def Int(id, label, default, **kw):
    return Input(id, label, "int", default, **kw)


def Bool(id, label, default=False, **kw):
    return Input(id, label, "bool", default, **kw)


def String(id, label, default="", **kw):
    return Input(id, label, "string", default, **kw)


def Choice(id, label, default, choices, **kw):
    return Input(id, label, "choice", default, choices=tuple(choices), **kw)


def Time(id, label, default, **kw):
    return Input(id, label, "time", default, **kw)


def Session(id, label, default, **kw):
    return Input(id, label, "session", default, **kw)


@dataclass(frozen=True)
class Bar:
    timestamp: object
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int = 0

    @property
    def time(self):
        return self.timestamp.tz_convert("America/New_York").strftime("%H:%M")


@dataclass(frozen=True)
class FVG:
    id: str
    direction: str
    top: Decimal
    bottom: Decimal
    formation: object
    opening_exception: bool


@dataclass(frozen=True)
class Context:
    timestamp: object  # current confirmed bar CLOSE, UTC
    bar: Bar
    previous_bar: Bar | None
    history: tuple[Bar, ...]
    fvg: FVG | None = None
    bar1: Bar | None = None
    bar2: Bar | None = None
    instrument: str = "MNQ"
    tick_size: Decimal = Decimal(".25")
    position: None = None  # v1 is flat-only entry callbacks, one actual trade/day


@dataclass(frozen=True)
class Entry:
    direction: Literal["LONG", "SHORT"]
    stop: Decimal
    target_r: Decimal = Decimal("2")
    max_risk: Decimal | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class StopUpdate:
    """Reserved request contract. V1 rejects management hooks; no retroactive fills."""

    price: Decimal
    effective_after: object


@dataclass(frozen=True)
class MoveStop:
    """Request only. The engine controls rounding, monotonicity and activation."""

    price: Decimal
    reason: str = "Strategy stop update"
    trigger_type: str = "custom"
    trigger_value: object = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class StopChange:
    timestamp: object
    activation_timestamp: object
    previous_stop: Decimal
    effective_stop: Decimal
    reason: str


@dataclass(frozen=True)
class ManagementContext:
    timestamp: object  # observed interval CLOSE / next minute START
    event: str  # minute_close or bar_5m_close
    entry_time: object
    entry_price: Decimal
    original_stop: Decimal
    current_stop: Decimal
    target: Decimal
    direction: str
    original_risk_points: Decimal
    mfe_points: Decimal
    mae_points: Decimal
    minute: Bar
    completed_bar: Bar | None
    stop_history: tuple[StopChange, ...] = ()
    tick_size: Decimal = Decimal(".25")

    @property
    def direction_sign(self):
        return Decimal(1) if self.direction == "LONG" else Decimal(-1)

    @property
    def minutes_since_entry(self):
        return int((self.timestamp - self.entry_time).total_seconds() / 60)

    @property
    def bars_since_entry(self):
        return self.minutes_since_entry // 5

    def price_at_r(self, r):
        return (
            self.entry_price
            + self.direction_sign * self.original_risk_points * Decimal(str(r))
        )

    def touched_profit_points(self, points):
        return self.mfe_points >= Decimal(str(points))

    def reached_r(self, r):
        return self.mfe_points >= self.original_risk_points * Decimal(str(r))

    def completed_bar_holds_beyond_r(self, r):
        b = self.completed_bar
        return b is not None and (
            b.low > self.price_at_r(r)
            if self.direction == "LONG"
            else b.high < self.price_at_r(r)
        )
