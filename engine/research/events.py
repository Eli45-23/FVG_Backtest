"""Causal event detector. No forward labeler or future-series dependency."""

from dataclasses import asdict
from decimal import Decimal as D
import pandas as pd
from engine.canonical import clean, digest
from engine.research.levels import FIVE, NY, valid_bar


class EventDetector:
    def __init__(self, config):
        self.config = config
        self.state = {}
        self.previous = None
        self.day = None
        self.last_timestamp = None

    def update(self, row, levels, session, context=None):
        at = pd.Timestamp(row.timestamp_utc)
        if self.last_timestamp is not None and at <= self.last_timestamp:
            raise ValueError("Events require strictly chronological candles")
        self.last_timestamp = at
        day = str(at.tz_convert(NY).date())
        if day != self.day:
            self.state = {}
            self.previous = None
            self.day = day
        if self.previous is not None and at <= self.previous.timestamp_utc:
            raise ValueError("Events require chronological candles")
        prev = self.previous
        consecutive = prev is not None and at - prev.timestamp_utc == FIVE
        if not valid_bar(row) or session is None or not session[0] <= at < session[1]:
            self.previous = None
            for s in self.state.values():
                s["touching"] = False
                s["broken"] = 0
            return []
        if not consecutive:
            for s in self.state.values():
                s["touching"] = False
                s["broken"] = 0
        self.previous = row
        available = [
            l
            for l in levels
            if l.active and l.trading_date == day and l.availability_timestamp <= at
        ]
        events = []
        for level in available:
            p = level.price
            s = self.state.setdefault(
                level.id, {"count": 0, "touching": False, "broken": 0}
            )
            origin = D(str(prev.close if consecutive else row.open))
            side = 1 if origin > p else -1 if origin < p else 0
            direction = -side
            touching = row.low <= p <= row.high
            new_touch = touching and not s["touching"]
            if new_touch:
                s["count"] += 1
            s["touching"] = touching
            close_side = 1 if row.close > p else -1 if row.close < p else 0
            penetration = (
                max(D(0), p - D(str(row.low)))
                if side == 1
                else max(D(0), D(str(row.high)) - p) if side == -1 else D(0)
            )
            kinds = []
            if new_touch:
                kinds.append("TOUCH")
                if s["broken"] and side == s["broken"]:
                    kinds.append("RETEST")
                if penetration > 0 and side and close_side == side:
                    kinds.append("SWEEP_RECLAIM")
                if (
                    side
                    and close_side == side
                    and penetration >= D(str(self.config.rejection_penetration))
                    and abs(D(str(row.close)) - p)
                    >= D(str(self.config.rejection_clearance))
                ):
                    kinds.append("REJECTION")
            if side and close_side == -side:
                kinds.append("BREAK_ACCEPTANCE")
                s["broken"] = close_side
            if not kinds:
                continue
            above = [
                l.price - D(str(row.close))
                for l in available
                if l.id != level.id and l.price > row.close
            ]
            below = [
                D(str(row.close)) - l.price
                for l in available
                if l.id != level.id and l.price < row.close
            ]
            width = D(str(row.high)) - D(str(row.low))
            common = dict(
                date=day,
                timestamp_utc=at + FIVE,
                timestamp_ny=(at + FIVE).tz_convert(NY),
                bar_start_utc=at,
                level_id=level.id,
                level_type=level.level_type,
                level_price=p,
                level_source_date=level.source_date,
                level_available_at=level.availability_timestamp,
                direction=(
                    "UP" if direction == 1 else "DOWN" if direction == -1 else "UNKNOWN"
                ),
                approach_side=(
                    "ABOVE" if side == 1 else "BELOW" if side == -1 else "ON_LEVEL"
                ),
                touch_number=s["count"],
                price_at_event=row.close,
                distance_through_level=penetration,
                open=row.open,
                high=row.high,
                low=row.low,
                close=row.close,
                body_ratio=(
                    abs(D(str(row.close)) - D(str(row.open))) / width if width else None
                ),
                minutes_since_rth_open=(at + FIVE - session[0]).total_seconds() / 60,
                weekday=(at + FIVE).tz_convert(NY).day_name(),
                year=int(day[:4]),
                time_bucket=(at + FIVE).tz_convert(NY).strftime("%H:")
                + ("00" if (at + FIVE).tz_convert(NY).minute < 30 else "30"),
                nearest_level_above=min(above) if above else None,
                nearest_level_below=min(below) if below else None,
                room_points=(
                    (min(above) if above else None)
                    if direction == 1
                    else (min(below) if below else None) if direction == -1 else None
                ),
                session_close=session[1],
                continuity_known=consecutive,
                **(context or {})
            )
            observation = digest([level.id, str(at)])
            for kind in kinds:
                events.append(
                    clean(
                        {
                            **common,
                            "observation_id": observation,
                            "interaction_type": kind,
                            "event_id": digest([observation, kind]),
                        }
                    )
                )
        return events
