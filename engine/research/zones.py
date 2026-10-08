"""Explicit displacement/base zone detector; no subjective pattern recognition."""

from dataclasses import dataclass, asdict
from collections import deque
from engine.canonical import digest


@dataclass(frozen=True)
class ZoneConfig:
    base_min: int = 1
    base_max: int = 3
    max_body_ratio: float = 0.5
    max_range_atr: float = 1.0
    departure_bars: int = 3
    min_displacement_atr: float = 1.5
    min_displacement_points: float = 0.0
    bounds: str = "full_base"

    def __post_init__(self):
        if (
            not 1 <= self.base_min <= self.base_max <= 10
            or self.departure_bars < 1
            or not 0 <= self.max_body_ratio <= 1
            or self.max_range_atr <= 0
            or min(self.min_displacement_atr, self.min_displacement_points) < 0
            or self.bounds not in ("full_base", "body_proximal_wick_distal")
        ):
            raise ValueError("Invalid mechanical zone configuration")


class DisplacementBaseZoneDetectorV1:
    def __init__(self, config=ZoneConfig(), timeframe="4h"):
        self.config = config
        self.timeframe = timeframe
        self.base = deque(maxlen=config.base_max)
        self.candidates = []
        self.zones = []
        self.sequence = 0

    def update(self, bar, at, atr, structure=None, contiguous=True):
        self.sequence += 1
        created = []
        if not contiguous:
            self.base.clear()
            self.candidates = []
        for z in self.zones:
            if z["status"] != "active" or z["availability_timestamp"] == at:
                continue
            touched = float(bar.low) <= z["top"] and float(bar.high) >= z["bottom"]
            if touched and not z.get("_touching", False):
                z["touch_count"] += 1
                z["mitigation_state"] = "touched"
            z["_touching"] = touched
            invalid = (
                float(bar.close) < z["bottom"]
                if z["zone_type"] == "DEMAND"
                else float(bar.close) > z["top"]
            )
            if invalid:
                z["status"] = "invalidated"
                z["invalidated_at"] = at
        for base, idx, known_atr in self.candidates:
            if self.sequence - idx > self.config.departure_bars:
                continue
            hi = max(float(b.high) for b in base)
            lo = min(float(b.low) for b in base)
            sign = 1 if float(bar.close) > hi else -1 if float(bar.close) < lo else 0
            dist = float(bar.close) - hi if sign == 1 else lo - float(bar.close)
            if not sign or dist < self.config.min_displacement_atr * known_atr:
                continue
            swing = (
                structure.high
                if sign == 1 and structure
                else structure.low if structure else None
            )
            swing_break = (
                swing is not None and (float(bar.close) - swing["price"]) * sign > 0
            )
            if not swing_break and dist < self.config.min_displacement_points:
                continue
            top, bottom = hi, lo
            if self.config.bounds == "body_proximal_wick_distal":
                if sign == 1:
                    top = max(float(max(b.open, b.close)) for b in base)
                else:
                    bottom = min(float(min(b.open, b.close)) for b in base)
            id = digest(
                [
                    self.timeframe,
                    str(base[0].timestamp),
                    str(base[-1].timestamp),
                    sign,
                    asdict(self.config),
                ]
            )
            if any(z["zone_id"] == id for z in self.zones):
                continue
            z = dict(
                zone_id=id,
                zone_type="DEMAND" if sign == 1 else "SUPPLY",
                top=top,
                bottom=bottom,
                formation_timestamp=base[0].timestamp,
                availability_timestamp=at,
                source_timeframe=self.timeframe,
                detector_version="DisplacementBaseZoneDetectorV1",
                settings=asdict(self.config),
                status="active",
                touch_count=0,
                mitigation_state="untouched",
                departure_displacement=dist,
                departure_atr=known_atr,
            )
            self.zones.append(z)
            created.append(z.copy())
        width = float(bar.high - bar.low)
        ratio = abs(float(bar.close - bar.open)) / width if width else 0
        if (
            atr
            and ratio <= self.config.max_body_ratio
            and width / atr <= self.config.max_range_atr
        ):
            self.base.append(bar)
            if (
                len(self.base) >= self.config.base_min
                and (
                    max(float(b.high) for b in self.base)
                    - min(float(b.low) for b in self.base)
                )
                / atr
                <= self.config.max_range_atr
            ):
                self.candidates.append((tuple(self.base), self.sequence, atr))
        else:
            self.base.clear()
        self.candidates = [
            x
            for x in self.candidates
            if self.sequence - x[1] < self.config.departure_bars
        ]
        return created
