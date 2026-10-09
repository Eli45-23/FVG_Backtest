"""Causal, opt-in base-only zones; V1 remains untouched."""

from collections import deque
from dataclasses import dataclass, asdict
from copy import deepcopy
import math
import pandas as pd
from engine.canonical import digest

VERSION = "DisplacementBaseZoneProviderV2"


@dataclass(frozen=True)
class ProviderConfig:
    provider: str = VERSION
    base_max: int = 3
    max_base_body_ratio: float = 0.50
    max_base_range_atr: float = 1.25
    departure_max: int = 2
    min_departure_body_ratio: float = 0.60
    min_displacement_atr: float = 1.00
    tick: float = 0.25
    overlap: str = "positive_common_wick_range"
    incoming: str = "immediately_pre_base_candle_close_minus_open"
    atr_reference: str = "last_base_confirmed_full_bar_atr14"

    def __post_init__(self):
        # V2 is frozen, not an optimization surface.
        expected = (
            VERSION,
            3,
            0.5,
            1.25,
            2,
            0.6,
            1.0,
            0.25,
            "positive_common_wick_range",
            "immediately_pre_base_candle_close_minus_open",
            "last_base_confirmed_full_bar_atr14",
        )
        if tuple(asdict(self).values()) != expected:
            raise ValueError(
                "V2 conventions are frozen; changes require a new provider version"
            )


def ratio(b):
    width = b["high"] - b["low"]
    return abs(b["close"] - b["open"]) / width if width > 0 else 0.0


class DisplacementBaseZoneProviderV2:
    def __init__(self, config=ProviderConfig(), frame_identity=None):
        self.config = config
        self.frame_identity = deepcopy(frame_identity)
        self.history = deque(maxlen=4)
        self.pending = []
        self.zones = []
        self.seen = set()
        self.last_at = None

    def _base(self):
        if not self.history:
            return None
        history = list(self.history)
        atr = history[-1].get("atr14")
        if atr is None or not math.isfinite(atr) or atr <= 0:
            return None
        selected = []
        for b in reversed(history):
            if len(selected) == 3:
                break
            test = [b] + selected
            if (
                ratio(b) > 0.5
                or max(x["high"] for x in test) - min(x["low"] for x in test)
                > 1.25 * atr
            ):
                break
            if selected and min(x["high"] for x in test) <= max(x["low"] for x in test):
                break
            selected = test
        if not selected:
            return None
        prior = history[-len(selected) - 1] if len(history) > len(selected) else None
        delta = prior["close"] - prior["open"] if prior else 0
        incoming = "RALLY" if delta > 0 else "DROP" if delta < 0 else "UNKNOWN"
        return dict(base=deepcopy(selected), atr=atr, incoming=incoming, departures=[])

    def update(self, bar):
        """One closed scheduled bucket. No future frame is accepted by the API."""
        b = deepcopy(bar)
        at = pd.Timestamp(b["availability_timestamp"])
        start = pd.Timestamp(b["timestamp"])
        if at.tz is None or start.tz is None or at <= start:
            raise ValueError("Aware confirmed interval required")
        if self.last_at is not None and at <= self.last_at:
            raise ValueError("Bars must be strictly chronological")
        if self.last_at is not None and start != self.last_at:
            self.history.clear()
            self.pending = []
        self.last_at = at
        if not b["complete"] or not b["full"]:
            self.history.clear()
            self.pending = []
            return []
        for k in ("open", "high", "low", "close"):
            if not math.isfinite(b[k]) or b[k] / 0.25 != round(b[k] / 0.25):
                raise ValueError("Invalid tick price")
        candidate = self._base()
        if candidate:
            self.pending.append(candidate)
        created = []
        remaining = []
        for c in self.pending:
            c["departures"].append(b)
            base = c["base"]
            deps = c["departures"]
            hi = max(x["high"] for x in base)
            lo = min(x["low"] for x in base)
            sign = 1 if b["close"] > hi else -1 if b["close"] < lo else 0
            proximal = (
                max(max(x["open"], x["close"]) for x in base)
                if sign == 1
                else min(min(x["open"], x["close"]) for x in base)
            )
            distal = lo if sign == 1 else hi
            displacement = (b["close"] - proximal) * sign
            qualifies = (
                sign != 0
                and max(map(ratio, deps)) >= 0.6
                and displacement >= c["atr"]
                and abs(distal - proximal) > 0
            )
            if qualifies:
                zid = digest(
                    [
                        VERSION,
                        self.frame_identity,
                        asdict(self.config),
                        [x["timestamp"] for x in base],
                        sign,
                    ]
                )
                if zid not in self.seen:
                    # Three consecutive full candles ending at confirmation; gap
                    # clearing prevents FVG claims across shortened/missing bars.
                    sequence = (base + deps)[-3:]
                    fvg = len(sequence) == 3 and (
                        sequence[2]["low"] > sequence[0]["high"]
                        if sign == 1
                        else sequence[2]["high"] < sequence[0]["low"]
                    )
                    z = dict(
                        zone_id=zid,
                        provider_version=VERSION,
                        configuration=asdict(self.config),
                        frame_identity=self.frame_identity,
                        zone_type="DEMAND" if sign == 1 else "SUPPLY",
                        pattern_type=c["incoming"]
                        + ("_BASE_RALLY" if sign == 1 else "_BASE_DROP"),
                        top=max(proximal, distal),
                        bottom=min(proximal, distal),
                        proximal=proximal,
                        distal=distal,
                        midpoint=(proximal + distal) / 2,
                        width=abs(proximal - distal),
                        width_atr=abs(proximal - distal) / c["atr"],
                        formation_timestamp=base[0]["timestamp"],
                        availability_timestamp=at,
                        base_timestamps=[x["timestamp"] for x in base],
                        base_count=len(base),
                        base_high=hi,
                        base_low=lo,
                        base_body_low=min(min(x["open"], x["close"]) for x in base),
                        base_body_high=max(max(x["open"], x["close"]) for x in base),
                        base_range=hi - lo,
                        base_range_atr=(hi - lo) / c["atr"],
                        base_body_ratios=list(map(ratio, base)),
                        common_overlap=min(x["high"] for x in base)
                        - max(x["low"] for x in base),
                        departure_timestamps=[x["timestamp"] for x in deps],
                        departure_count=len(deps),
                        departure_displacement=displacement,
                        departure_displacement_atr=displacement / c["atr"],
                        atr14=c["atr"],
                        departure_body_ratios=list(map(ratio, deps)),
                        departure_range_atr=[
                            (x["high"] - x["low"]) / c["atr"] for x in deps
                        ],
                        departure_volume=sum(x.get("volume", 0) for x in deps),
                        fvg=fvg,
                        bos=(
                            any(x["bos"] for x in deps)
                            if all("bos" in x for x in deps)
                            else None
                        ),
                        choch=(
                            any(x["choch"] for x in deps)
                            if all("choch" in x for x in deps)
                            else None
                        ),
                        context=deepcopy(b.get("context", {})),
                    )
                    self.seen.add(zid)
                    self.zones.append(z)
                    created.append(deepcopy(z))
            elif len(deps) < 2:
                remaining.append(c)
        self.pending = remaining
        self.history.append(b)
        return created

    def available(self, at):
        return [deepcopy(z) for z in self.zones if z["availability_timestamp"] <= at]
