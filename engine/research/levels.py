"""Sequential-only price levels and generic zones for research or ordinary strategies."""

from dataclasses import dataclass, asdict
from decimal import Decimal as D
from collections import deque
import pandas as pd
import exchange_calendars as xc
from engine.canonical import digest

NY = "America/New_York"
FIVE = pd.Timedelta(minutes=5)


@dataclass(frozen=True)
class SessionConfig:
    premarket_start: str | None = None
    premarket_end: str | None = None
    rejection_penetration: float = 0.0
    rejection_clearance: float = 0.25

    def __post_init__(self):
        if (self.premarket_start is None) != (self.premarket_end is None):
            raise ValueError("Provide both explicit premarket endpoints or disable PM")
        if self.premarket_start:
            from datetime import time

            for t in (self.premarket_start, self.premarket_end):
                value = time.fromisoformat(t)
                if value.second or value.minute % 5 or len(t) != 5:
                    raise ValueError(
                        "Premarket endpoints require HH:MM, aligned to 5 minutes"
                    )
            if not "00:00" <= self.premarket_start < self.premarket_end <= "09:30":
                raise ValueError("Premarket must be a same-date window ending by 09:30")
        import math

        if any(
            not math.isfinite(v) or v < 0
            for v in (self.rejection_penetration, self.rejection_clearance)
        ):
            raise ValueError("Rejection distances must be finite and nonnegative")


@dataclass(frozen=True)
class Level:
    id: str
    level_type: str
    price: D
    trading_date: str
    source_date: str
    availability_timestamp: pd.Timestamp
    active: bool
    configuration: tuple


@dataclass(frozen=True)
class Zone:
    zone_id: str
    zone_type: str
    top: D
    bottom: D
    formation_timestamp: pd.Timestamp
    availability_timestamp: pd.Timestamp
    source_timeframe: str
    status: str = "active"

    def __post_init__(self):
        if (
            self.top <= self.bottom
            or not self.top.is_finite()
            or not self.bottom.is_finite()
        ):
            raise ValueError("Zone bounds must be finite and top > bottom")
        if (
            self.formation_timestamp.tzinfo is None
            or self.availability_timestamp.tzinfo is None
        ):
            raise ValueError("Zone timestamps must be aware")
        if self.availability_timestamp < self.formation_timestamp:
            raise ValueError("Zone cannot be available before formation")
        if self.status not in ("active", "invalidated"):
            raise ValueError("Invalid zone status")


def schedule(start="2019-12-01", end="2026-10-07"):
    cal = xc.get_calendar("XNYS", start=start, end=end)
    return {
        str(i.date()): (pd.Timestamp(r.open), pd.Timestamp(r.close))
        for i, r in cal.schedule.iterrows()
    }


def valid_bar(row):
    return (
        bool(row.is_complete_5m)
        and all(
            D(str(getattr(row, k))).is_finite()
            for k in ("open", "high", "low", "close")
        )
        and row.high >= max(row.open, row.close, row.low)
        and row.low <= min(row.open, row.close)
    )


class LevelEngine:
    """Feed each closed bar exactly once. update never receives future candles."""

    def __init__(self, config=SessionConfig(), sessions=None):
        self.config = config
        self.sessions = schedule() if sessions is None else sessions
        self.previous_session = dict(
            zip(list(self.sessions)[1:], list(self.sessions)[:-1])
        )
        self.last = None
        self.day = None
        self.completed = {}
        self.levels = []
        self.rth = []
        self.pm = []
        self.tr = deque(maxlen=14)
        self.prior_close = None
        self.atr = None
        self.opening_range = None
        self.premarket_range = None

    def on_bar(self, confirmed_bar):
        """SDK adapter: ordinary strategy ctx.bar is already a complete confirmed Bar."""
        from types import SimpleNamespace

        self.update(
            SimpleNamespace(
                timestamp_utc=confirmed_bar.timestamp,
                open=confirmed_bar.open,
                high=confirmed_bar.high,
                low=confirmed_bar.low,
                close=confirmed_bar.close,
                is_complete_5m=True,
            )
        )
        return self.active(confirmed_bar.timestamp + FIVE)

    def _add(self, kind, price, source, available):
        cfg = tuple(sorted(asdict(self.config).items()))
        self.levels.append(
            Level(
                digest([kind, self.day, source, str(price), str(available), cfg]),
                kind,
                D(str(price)),
                self.day,
                source,
                available,
                True,
                cfg,
            )
        )

    def active(self, at):
        return tuple(
            l for l in self.levels if l.active and l.availability_timestamp <= at
        )

    def update(self, row):
        at = pd.Timestamp(row.timestamp_utc)
        if at.tzinfo is None or (self.last is not None and at <= self.last):
            raise ValueError("Bars must be aware, unique and strictly chronological")
        contiguous = self.last is not None and at - self.last == FIVE
        if not contiguous or not valid_bar(row):
            self.tr.clear()
            self.prior_close = None
            self.atr = None
        self.last = at
        day = str(at.tz_convert(NY).date())
        if day != self.day:
            self.day = day
            self.levels = []
            self.rth = []
            self.pm = []
            self.opening_range = self.premarket_range = None
            prev = self.previous_session.get(day)
            if day in self.sessions and prev in self.completed:
                high, low, available = self.completed[prev]
                self._add("PDH", high, prev, available)
                self._add("PDL", low, prev, available)
        if not valid_bar(row):
            return
        high, low, close = map(lambda x: D(str(x)), (row.high, row.low, row.close))
        tr = (
            high - low
            if self.prior_close is None
            else max(
                high - low, abs(high - self.prior_close), abs(low - self.prior_close)
            )
        )
        self.tr.append(tr)
        self.prior_close = close
        self.atr = sum(self.tr) / 14 if len(self.tr) == 14 else None
        clock = at.tz_convert(NY).strftime("%H:%M")
        if (
            self.config.premarket_start
            and self.config.premarket_start <= clock < self.config.premarket_end
        ):
            self.pm.append(row)
            end = pd.Timestamp(f"{day} {self.config.premarket_end}", tz=NY).tz_convert(
                "UTC"
            )
            start = pd.Timestamp(
                f"{day} {self.config.premarket_start}", tz=NY
            ).tz_convert("UTC")
            if at + FIVE == end and self._complete(self.pm, start, end):
                h, l = max(x.high for x in self.pm), min(x.low for x in self.pm)
                self._add("PMH", h, day, end)
                self._add("PML", l, day, end)
                self.premarket_range = D(str(h)) - D(str(l))
        if day not in self.sessions:
            return
        op, end = self.sessions[day]
        if op <= at < end:
            self.rth.append(row)
            if at == op:
                self._add("O5H", high, day, at + FIVE)
                self._add("O5L", low, day, at + FIVE)
                self.opening_range = high - low
            if at + FIVE == end and self._complete(self.rth, op, end):
                self.completed[day] = (
                    max(x.high for x in self.rth),
                    min(x.low for x in self.rth),
                    end,
                )
                # Only the last completed session can be needed by a future date.
                self.completed = {day: self.completed[day]}

    @staticmethod
    def _complete(rows, start, end):
        return [pd.Timestamp(r.timestamp_utc) for r in rows] == list(
            pd.date_range(start, end, freq="5min", inclusive="left")
        )
