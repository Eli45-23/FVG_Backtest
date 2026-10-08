"""Confirmed multi-timeframe feature snapshots for research and strategy callbacks."""

from dataclasses import dataclass, field
from types import MappingProxyType
from decimal import Decimal as D
import pandas as pd
import heapq
from engine.research.indicators import Indicators, IndicatorConfig
from engine.research.structure import Structure, StructureConfig
from engine.research.zones import DisplacementBaseZoneDetectorV1, ZoneConfig
from engine.research.levels import LevelEngine, SessionConfig, Level, NY, valid_bar
from engine.strategy import Bar
from engine.timeframes import MINUTES


def frozen(value):
    if isinstance(value, dict):
        return MappingProxyType({k: frozen(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(frozen(v) for v in value)
    return value


class FeatureHub:
    def __init__(self, frames, session=SessionConfig(), settings=None):
        settings = settings or {}

        def confirmed_rows(tf, frame):
            for row in frame.itertuples(index=False):
                yield (row.timestamp_utc + pd.Timedelta(minutes=MINUTES[tf]), tf, row)

        self.rows = heapq.merge(
            *(confirmed_rows(tf, frame) for tf, frame in frames.items()),
            key=lambda x: (x[0], MINUTES[x[1]])
        )
        self.pending = next(self.rows, None)
        self.latest = {}
        self.values = {}
        self.last = {}
        self.annotations = []
        self.indicators = {
            tf: Indicators(IndicatorConfig(**settings.get("indicators", {})))
            for tf in frames
        }
        self.structures = {
            tf: Structure(StructureConfig(**settings.get("structure", {})), tf)
            for tf in frames
        }
        self.zones = {
            tf: DisplacementBaseZoneDetectorV1(
                ZoneConfig(**settings.get("zones", {})), tf
            )
            for tf in frames
        }
        self.levels = LevelEngine(session)
        self.prior_close = {}
        self.rth_open = {}
        self.last_rth_close = None
        self.previous_day = None

    def advance(self, at):
        while self.pending is not None and self.pending[0] <= at:
            confirmed, tf, r = self.pending
            self.pending = next(self.rows, None)
            delta = pd.Timedelta(minutes=MINUTES[tf])
            continuous = (
                self.last.get(tf) is not None
                and r.timestamp_utc - self.last[tf] == delta
            )
            self.last[tf] = r.timestamp_utc
            if tf == "5m":
                self.levels.update(r)
            if not valid_bar(r):
                self.indicators[tf].update(r, r.timestamp_utc, False, False)
                self.structures[tf].window.clear()
                self.zones[tf].base.clear()
                self.zones[tf].candidates.clear()
                continue
            b = Bar(r.timestamp_utc, r.open, r.high, r.low, r.close, int(r.volume))
            self.latest[tf] = b
            day = str(r.timestamp_utc.tz_convert(NY).date())
            session = self.levels.sessions.get(day)
            values = self.indicators[tf].update(
                b,
                b.timestamp,
                contiguous=continuous,
                session_close=session[1] if session else None,
            )
            events = self.structures[tf].update(
                b, confirmed, values.get("atr14"), continuous
            )
            created = self.zones[tf].update(
                b, confirmed, values.get("atr14"), self.structures[tf], continuous
            )
            values["structure_state"] = self.structures[tf].state
            values["structure_events"] = events
            values["new_zones"] = created
            if tf == "5m":
                levels = {l.level_type: l.price for l in self.levels.active(confirmed)}
                if session and b.timestamp == session[0]:
                    self.rth_open[day] = float(b.open)
                if session and confirmed == session[1] and day in self.levels.completed:
                    self.prior_close[day] = float(b.close)
                prev = self.levels.previous_session.get(day)
                previous_close = self.prior_close.get(prev)
                op = self.rth_open.get(day)
                pdh = levels.get("PDH")
                pdl = levels.get("PDL")
                atr = values.get("atr14")
                norm = lambda x: float(x) / atr if x is not None and atr else None
                prior_range = (
                    float(pdh - pdl) if pdh is not None and pdl is not None else None
                )
                gap = (
                    op - previous_close
                    if op is not None and previous_close is not None
                    else None
                )
                values.update(
                    rth_open=op,
                    previous_rth_close=previous_close,
                    prior_day_range=prior_range,
                    prior_day_range_atr=norm(prior_range),
                    overnight_gap=gap,
                    overnight_gap_atr=norm(gap),
                    opening_location=(
                        (op - float(pdl)) / prior_range
                        if op is not None and prior_range
                        else None
                    ),
                    distance_to_pdh=float(pdh - b.close) if pdh is not None else None,
                    distance_to_pdl=float(b.close - pdl) if pdl is not None else None,
                    opening_range_size=self.levels.opening_range,
                    opening_range_atr=norm(self.levels.opening_range),
                    premarket_range_size=self.levels.premarket_range,
                    premarket_range_atr=norm(self.levels.premarket_range),
                )
            self.values[tf] = values
        return self

    def snapshots(self):
        return frozen(self.latest), frozen(self.values)

    def active_levels(self, at):
        day = str(at.tz_convert(NY).date())
        out = list(self.levels.active(at))
        for tf, structure in self.structures.items():
            if tf not in ("5m", "4h"):
                continue
            for swing in (structure.high, structure.low):
                if swing and swing["availability_timestamp"] <= at:
                    out.append(
                        Level(
                            swing["id"],
                            tf + "_SWING_" + swing["swing_type"],
                            D(str(swing["price"])),
                            day,
                            str(swing["formation_timestamp"].date()),
                            swing["availability_timestamp"],
                            True,
                            (),
                        )
                    )
        for z in self.zones.get("4h", self.zones.get("5m")).zones:
            if z["status"] == "active" and z["availability_timestamp"] <= at:
                price = z["top"] if z["zone_type"] == "DEMAND" else z["bottom"]
                out.append(
                    Level(
                        z["zone_id"],
                        z["zone_type"],
                        D(str(price)),
                        day,
                        str(z["formation_timestamp"].date()),
                        z["availability_timestamp"],
                        True,
                        (),
                    )
                )
        return tuple(out)
