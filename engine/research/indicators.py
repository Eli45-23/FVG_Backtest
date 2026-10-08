"""Streaming, confirmed-bar EMA/ATR/VWAP and descriptive regime context."""

from collections import deque
from dataclasses import dataclass
from datetime import time
from engine.research.levels import NY
import numpy as np


@dataclass(frozen=True)
class IndicatorConfig:
    atr_length: int = 14
    regime_lookback: int = 252
    efficiency_lookback: int = 20
    vwap_start: str = "09:30"
    vwap_end: str = "16:00"

    def __post_init__(self):
        if min(self.atr_length, self.regime_lookback, self.efficiency_lookback) < 2:
            raise ValueError("Indicator lookbacks >=2")
        if not time.fromisoformat(self.vwap_start) < time.fromisoformat(self.vwap_end):
            raise ValueError("Explicit same-date VWAP window required")


class Indicators:
    def __init__(self, config=IndicatorConfig()):
        self.config = config
        self.prev = None
        self.ema9 = None
        self.ema20 = None
        self.tr = deque(maxlen=config.atr_length)
        self.atrs = deque(maxlen=config.regime_lookback)
        self.closes = deque(maxlen=config.efficiency_lookback + 1)
        self.ranges = deque(maxlen=config.efficiency_lookback)
        self.day = None
        self.pv = 0.0
        self.volume = 0.0
        self.vwap = None
        self.cross_at = None
        self.vwap_cross_at = None
        self.vwap_side = 0
        self.cross_count = 0
        self.vwap_invalid_days = set()
        self.vwap_started_days = set()

    def update(self, bar, at, complete=True, contiguous=True, session_close=None):
        day = str(at.tz_convert(NY).date())
        clock = at.tz_convert(NY).strftime("%H:%M")
        in_window = self.config.vwap_start <= clock < self.config.vwap_end and (
            session_close is None or at < session_close
        )
        if in_window:
            if day not in self.vwap_started_days:
                self.vwap_started_days.add(day)
                if clock != self.config.vwap_start:
                    self.vwap_invalid_days.add(day)
            if not complete or (not contiguous and clock != self.config.vwap_start):
                self.vwap_invalid_days.add(day)
        if not complete or not contiguous:
            self.cross_at = None
            self.prev = None
            self.ema9 = self.ema20 = None
            self.tr.clear()
            self.closes.clear()
            self.ranges.clear()
            if not complete:
                return {}
        op, hi, lo, cl = map(float, (bar.open, bar.high, bar.low, bar.close))
        day = str(at.tz_convert(NY).date())
        clock = at.tz_convert(NY).strftime("%H:%M")
        if day != self.day:
            self.day = day
            self.pv = self.volume = 0.0
            self.vwap = None
            self.vwap_side = 0
            self.vwap_cross_at = None
            self.cross_count = 0
        tr = (
            hi - lo
            if self.prev is None
            else max(hi - lo, abs(hi - self.prev), abs(lo - self.prev))
        )
        self.tr.append(tr)
        atr = (
            sum(self.tr) / len(self.tr)
            if len(self.tr) == self.config.atr_length
            else None
        )
        percentile = (
            (sum(x <= atr for x in self.atrs) / len(self.atrs))
            if atr and len(self.atrs) == self.config.regime_lookback
            else None
        )
        if atr is not None:
            self.atrs.append(atr)
        old9, old20 = self.ema9, self.ema20
        self.ema9 = cl if old9 is None else old9 + (cl - old9) * 2 / 10
        self.ema20 = cl if old20 is None else old20 + (cl - old20) * 2 / 21
        cross = None
        if old9 is not None and old20 is not None:
            if old9 <= old20 and self.ema9 > self.ema20:
                cross = "BULLISH"
            elif old9 >= old20 and self.ema9 < self.ema20:
                cross = "BEARISH"
        if cross:
            self.cross_at = at
        old_vwap = self.vwap
        # Input timestamp is candle start; final session candle contributes when confirmed.
        if self.config.vwap_start <= clock < self.config.vwap_end and (
            session_close is None or at < session_close
        ):
            volume = float(bar.volume)
            self.pv += (hi + lo + cl) / 3 * volume
            self.volume += volume
            self.vwap = self.pv / self.volume if self.volume else None
        if day in self.vwap_invalid_days:
            self.vwap = None
        vwap_side = (
            0
            if self.vwap is None
            else 1 if cl > self.vwap else -1 if cl < self.vwap else 0
        )
        if vwap_side and self.vwap_side and vwap_side != self.vwap_side:
            self.vwap_cross_at = at
            self.cross_count += 1
        if vwap_side:
            self.vwap_side = vwap_side
        self.closes.append(cl)
        self.ranges.append((hi, lo))
        path = sum(abs(b - a) for a, b in zip(self.closes, list(self.closes)[1:]))
        efficiency = (
            abs(cl - self.closes[0]) / path
            if len(self.closes) == self.closes.maxlen and path
            else None
        )
        self.prev = cl
        norm = lambda x: x / atr if x is not None and atr and atr > 0 else None
        sep = self.ema9 - self.ema20
        vd = cl - self.vwap if self.vwap is not None else None
        return dict(
            atr14=atr,
            atr_percentile=percentile,
            atr_regime=(
                "UNAVAILABLE"
                if percentile is None
                else (
                    "LOW"
                    if percentile < 1 / 3
                    else "HIGH" if percentile >= 2 / 3 else "MIDDLE"
                )
            ),
            ema9=self.ema9,
            ema20=self.ema20,
            ema_separation=sep,
            ema_absolute_separation=abs(sep),
            ema_separation_atr=norm(sep),
            ema9_slope=self.ema9 - old9 if old9 is not None else None,
            ema20_slope=self.ema20 - old20 if old20 is not None else None,
            ema_cross=cross,
            minutes_since_ema_cross=(
                (at - self.cross_at).total_seconds() / 60
                if self.cross_at is not None
                else None
            ),
            above_ema9=cl > self.ema9,
            above_ema20=cl > self.ema20,
            ema_alignment="BULLISH" if sep > 0 else "BEARISH" if sep < 0 else "NEUTRAL",
            vwap=self.vwap,
            vwap_complete=day not in self.vwap_invalid_days,
            vwap_distance=vd,
            vwap_distance_atr=norm(vd),
            vwap_slope=(
                self.vwap - old_vwap
                if self.vwap is not None and old_vwap is not None
                else None
            ),
            ema9_vwap=self.ema9 - self.vwap if self.vwap is not None else None,
            ema20_vwap=self.ema20 - self.vwap if self.vwap is not None else None,
            above_vwap=vwap_side == 1 if self.vwap is not None else None,
            vwap_alignment=(
                "UNAVAILABLE"
                if self.vwap is None
                else (
                    "BULLISH"
                    if cl > self.ema9 > self.ema20 > self.vwap
                    else (
                        "BEARISH"
                        if cl < self.ema9 < self.ema20 < self.vwap
                        else "MIXED"
                    )
                )
            ),
            vwap_cross_frequency=self.cross_count,
            minutes_since_vwap_cross=(
                (at - self.vwap_cross_at).total_seconds() / 60
                if self.vwap_cross_at is not None
                else None
            ),
            directional_efficiency=efficiency,
            rolling_range_atr=norm(
                max(x[0] for x in self.ranges) - min(x[1] for x in self.ranges)
            ),
        )
