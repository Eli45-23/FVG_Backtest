"""Confirmed strict pivots and explicit close-break structure state."""

from dataclasses import dataclass
from collections import deque
from engine.canonical import digest


@dataclass(frozen=True)
class StructureConfig:
    left_bars: int = 2
    right_bars: int = 2
    min_displacement: float = 0.0
    min_displacement_atr: float = 0.0

    def __post_init__(self):
        if (
            self.left_bars < 1
            or self.right_bars < 1
            or min(self.min_displacement, self.min_displacement_atr) < 0
        ):
            raise ValueError("Invalid pivot settings")


class Structure:
    def __init__(self, config=StructureConfig(), timeframe="5m"):
        self.config = config
        self.timeframe = timeframe
        self.window = deque(maxlen=config.left_bars + config.right_bars + 1)
        self.high = None
        self.low = None
        self.state = "NEUTRAL"
        self.progression = {}
        self.broken = set()

    def update(self, bar, confirmed, atr=None, contiguous=True):
        if not contiguous:
            self.window.clear()
        events = []
        pivot_changed = False
        for kind, swing, side in [("HIGH", self.high, 1), ("LOW", self.low, -1)]:
            if (
                swing
                and swing["id"] not in self.broken
                and (float(bar.close) - swing["price"]) * side > 0
            ):
                trend = "BULLISH" if side == 1 else "BEARISH"
                cls = (
                    "BOS"
                    if self.state == trend
                    else "CHOCH" if self.state != "NEUTRAL" else "STRUCTURE_BREAK"
                )
                events.append(
                    dict(
                        event_type=trend + "_" + cls,
                        timestamp=confirmed,
                        swing_id=swing["id"],
                        price=swing["price"],
                        direction=trend,
                    )
                )
                self.broken.add(swing["id"])
                if cls == "CHOCH":
                    self.state = trend
        self.window.append(bar)
        if len(self.window) == self.window.maxlen:
            rows = list(self.window)
            pivot = rows[self.config.left_bars]
            others = rows[: self.config.left_bars] + rows[self.config.left_bars + 1 :]
            for kind in ["HIGH", "LOW"]:
                price = float(pivot.high if kind == "HIGH" else pivot.low)
                qualifies = (
                    all(price > float(x.high) for x in others)
                    if kind == "HIGH"
                    else all(price < float(x.low) for x in others)
                )
                displacement = (
                    price - min(float(x.low) for x in rows)
                    if kind == "HIGH"
                    else max(float(x.high) for x in rows) - price
                )
                if (
                    not qualifies
                    or displacement < self.config.min_displacement
                    or (
                        self.config.min_displacement_atr
                        and (
                            not atr
                            or displacement / atr < self.config.min_displacement_atr
                        )
                    )
                ):
                    continue
                old = self.high if kind == "HIGH" else self.low
                prog = (
                    None
                    if old is None
                    else (
                        (
                            "HH"
                            if price > old["price"]
                            else "LH" if price < old["price"] else "EH"
                        )
                        if kind == "HIGH"
                        else (
                            "HL"
                            if price > old["price"]
                            else "LL" if price < old["price"] else "EL"
                        )
                    )
                )
                swing = dict(
                    id=digest(
                        [self.timeframe, kind, str(pivot.timestamp), str(confirmed)]
                    ),
                    swing_type=kind,
                    price=price,
                    formation_timestamp=pivot.timestamp,
                    availability_timestamp=confirmed,
                    displacement=displacement,
                    displacement_atr=displacement / atr if atr else None,
                    source_timeframe=self.timeframe,
                    progression=prog,
                )
                if kind == "HIGH":
                    self.high = swing
                else:
                    self.low = swing
                pivot_changed = True
                self.progression[kind] = prog
                events.append(
                    dict(event_type="SWING_" + kind, **swing, timestamp=confirmed)
                )
        if (
            pivot_changed
            and self.progression.get("HIGH") == "HH"
            and self.progression.get("LOW") == "HL"
        ):
            self.state = "BULLISH"
        elif (
            pivot_changed
            and self.progression.get("HIGH") == "LH"
            and self.progression.get("LOW") == "LL"
        ):
            self.state = "BEARISH"
        return events
