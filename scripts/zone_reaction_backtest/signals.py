"""Sequential confirmed 5m rules. No future outcomes or execution data accepted."""

from decimal import Decimal as D, ROUND_FLOOR, ROUND_CEILING
import pandas as pd
from engine.canonical import digest
from engine.legacy import reference as ref
from engine.research.levels import valid_bar


class Detector:
    def __init__(self):
        self.day = None
        self.previous = None
        self.state = {}
        self.signals = []

    def reset(self):
        self.previous = None
        self.state = {}

    def update(self, row, zones, invalidated, session_open):
        """zones known at bar START; invalidations known by this bar CLOSE only."""
        start = row.timestamp_utc
        at = start + pd.Timedelta(minutes=5)
        day = str(start.tz_convert("America/New_York").date())
        if day != self.day:
            self.reset()
            self.day = day
        adjacent = (
            self.previous is not None
            and start - self.previous.timestamp_utc == pd.Timedelta(minutes=5)
        )
        if not adjacent:
            self.state = {}
        if not valid_bar(row):
            self.reset()
            return []
        origin = (
            D(str(self.previous.close))
            if adjacent
            else D(str(row.open)) if start == session_open else None
        )
        found = []
        for zid, z in zones.items():
            assert pd.Timestamp(z["availability_timestamp"]) <= start
            invalid_at = invalidated.get(zid)
            assert invalid_at is None or invalid_at <= at
            active_start = invalid_at is None or invalid_at > start
            active_close = invalid_at is None or invalid_at > at
            s = self.state.setdefault(
                zid,
                dict(
                    touching=False, count=0, armed=False, penetrated=False, pending=None
                ),
            )
            supply = z["zone_type"] == "SUPPLY"
            lo = D(str(z["bottom"]))
            hi = D(str(z["top"]))
            contact = row.low <= hi and row.high >= lo
            normal_side = origin is not None and (
                origin < lo if supply else origin > hi
            )
            outside_near = row.high < lo if supply else row.low > hi
            outside_far = row.low > hi if supply else row.high < lo

            def emit(setup, episode):
                direction = (
                    ("SHORT" if supply else "LONG")
                    if setup != "C"
                    else ("LONG" if supply else "SHORT")
                )
                record = dict(
                    setup=setup,
                    zone_id=zid,
                    zone_type=z["zone_type"],
                    zone_available_at=z["availability_timestamp"],
                    zone_top=hi,
                    zone_bottom=lo,
                    date=day,
                    year=int(day[:4]),
                    entry_time_utc=at,
                    entry_time_ny=at.tz_convert("America/New_York"),
                    trigger_start=start,
                    close=row.close,
                    direction=direction,
                    episode_id=episode["id"],
                    episode_start=episode["start"],
                    episode_number=episode["number"],
                    zone_invalidation_known_at=invalid_at,
                )
                record["signal_id"] = digest([setup, zid, episode["id"], str(at)])
                found.append(record)

            pending = s["pending"]
            s["pending"] = None
            if pending:
                allowed_invalidation = (
                    invalid_at is None or invalid_at >= pending["break_at"]
                )
                if (
                    adjacent
                    and start == pending["break_at"]
                    and outside_far
                    and allowed_invalidation
                ):
                    emit("C", pending["episode"])
            if not active_start:
                s["touching"] = contact
                s["armed"] = False
                continue
            if contact:
                if not s["touching"]:
                    s["count"] += 1
                    s["episode"] = dict(
                        id=digest([zid, day, str(start)]),
                        start=start,
                        number=s["count"],
                    )
                    s["armed"] = normal_side
                    s["penetrated"] = False
                if s["armed"]:
                    s["penetrated"] |= bool(row.high > lo if supply else row.low < hi)
            elif s["armed"]:
                if outside_near:
                    if active_close:
                        emit("A" if s["penetrated"] else "B", s["episode"])
                    s["armed"] = False
                elif outside_far:
                    s["pending"] = dict(break_at=at, episode=s["episode"])
                    s["armed"] = False
            s["touching"] = contact
        self.previous = row
        self.signals.extend(found)
        return found


def bracket(signal, ticks=1):
    sign = D(1) if signal["direction"] == "LONG" else D(-1)
    entry = ref.tick(D(str(signal["close"]))) + sign * D(".25") * ticks
    stop = (
        ref.tick(D(str(signal["zone_bottom"])) - D(".25"), ROUND_FLOOR)
        if sign == 1
        else ref.tick(D(str(signal["zone_top"])) + D(".25"), ROUND_CEILING)
    )
    risk = (entry - stop) * sign
    return dict(
        entry_price=entry,
        stop_price=stop,
        risk_points=risk,
        target_price=ref.tick(entry + sign * risk * 2),
        risk_usd=risk * 2,
    )


def selection_reason(signal, busy_until, previous_exit, close):
    if signal["entry_time_utc"] >= close:
        return "AT_SESSION_CLOSE"
    if busy_until is not None and signal["entry_time_utc"] < busy_until:
        return "POSITION_OPEN"
    if previous_exit is not None and signal["episode_start"] < previous_exit:
        return "EPISODE_BEGAN_BEFORE_PREVIOUS_EXIT"
    return None
