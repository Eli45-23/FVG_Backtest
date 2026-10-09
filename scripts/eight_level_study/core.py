"""Causal adapters only. This module never reads forward outcomes."""

from decimal import Decimal as D
from types import SimpleNamespace
import pandas as pd
from engine.canonical import digest, clean
from engine.research.levels import Level, FIVE, NY, valid_bar

ENTRIES = [
    "BREAK_CLOSE",
    "BREAK_FIRST_FULL",
    "BREAK_NEXT_CLOSE_HOLD",
    "BREAK_NEXT_FULL_HOLD",
    "RETEST_CLOSE_HOLD",
    "RETEST_RANGE_ESCAPE",
    "REJECTION_CLOSE",
    "REJECTION_CONFIRMATION",
    "FAILED_BREAK_CLOSE",
    "FAILED_BREAK_CONFIRMATION",
]
FAMILY = {
    k: (
        "RETEST_CONTINUATION"
        if k.startswith("RETEST")
        else (
            "REJECTION"
            if k.startswith("REJECTION")
            else (
                "FAILED_BREAK_REVERSAL"
                if k.startswith("FAILED")
                else "DIRECT_BREAK_CONTINUATION"
            )
        )
    )
    for k in ENTRIES
}


class Opening15:
    def __init__(self, sessions):
        self.sessions = sessions
        self.day = None
        self.rows = []
        self.levels = []

    def update(self, row):
        at = row.timestamp_utc
        day = str(at.tz_convert(NY).date())
        if day != self.day:
            self.day = day
            self.rows = []
            self.levels = []
        session = self.sessions.get(day)
        if not session:
            return
        op = session[0]
        if op <= at < op + pd.Timedelta(minutes=15) and valid_bar(row):
            self.rows.append(row)
        if at == op + pd.Timedelta(minutes=10) and [
            r.timestamp_utc for r in self.rows
        ] == list(pd.date_range(op, periods=3, freq="5min")):
            for kind, price in [
                ("O15H", max(r.high for r in self.rows)),
                ("O15L", min(r.low for r in self.rows)),
            ]:
                available = op + pd.Timedelta(minutes=15)
                self.levels.append(
                    Level(
                        digest([kind, day, str(price), str(available)]),
                        kind,
                        D(str(price)),
                        day,
                        day,
                        available,
                        True,
                        (("opening_minutes", 15),),
                    )
                )

    def active(self, at):
        return [
            l
            for l in self.levels
            if l.availability_timestamp <= at
            and l.trading_date == str(at.tz_convert(NY).date())
        ]


class Entries:
    def __init__(self):
        self.last = None
        self.day = None
        self.direct = {}
        self.escape = {}
        self.fail = []

    def update(self, row, events, context, session):
        at = row.timestamp_utc
        now = at + FIVE
        day = str(at.tz_convert(NY).date())
        if (
            day != self.day
            or self.last is None
            or at - self.last != FIVE
            or not valid_bar(row)
            or not session
            or not session[0] <= at < session[1]
        ):
            self.direct = {}
            self.escape = {}
            self.fail = []
        self.last = at
        self.day = day
        if not valid_bar(row) or not session or not session[0] <= at < session[1]:
            return []
        out = []

        def emit(e, kind, direction, root=None):
            parent = root or e.get("root_event_id") or e["event_id"]
            v = {
                k: e.get(k)
                for k in [
                    "level_id",
                    "level_type",
                    "level_price",
                    "level_available_at",
                    "approach_side",
                    "touch_number",
                ]
            }
            v.update(
                entry_kind=kind,
                family=FAMILY[kind],
                root_id=parent,
                source_event_id=e["event_id"],
                direction=direction,
                timestamp_utc=now,
                date=day,
                year=int(day[:4]),
                price_at_event=float(row.close),
                session_close=session[1],
                **context
            )
            v["event_id"] = digest([kind, e["event_id"], str(now), direction])
            out.append(clean(v))

        def sign(e):
            return 1 if e["direction"] == "UP" else -1

        def full(e):
            return (
                float(row.low) > float(e["level_price"])
                if sign(e) == 1
                else float(row.high) < float(e["level_price"])
            )

        def touched(e):
            return float(row.low) <= float(e["level_price"]) <= float(row.high)

        # Previously armed opportunities can use only this newly confirmed bar.
        for e in self.fail:
            s = -sign(e)
            extreme = float(e["high"] if s == 1 else e["low"])
            if (
                pd.Timestamp(e["timestamp_utc"]) == at
                and (float(row.close) - extreme) * s > 0
            ):
                emit(e, "FAILED_BREAK_CONFIRMATION", "UP" if s == 1 else "DOWN")
        self.fail = []
        for key, e in list(self.direct.items()):
            if (
                touched(e)
                or (float(row.close) - float(e["level_price"])) * sign(e) <= 0
            ):
                del self.direct[key]
            elif full(e):
                emit(e, "BREAK_FIRST_FULL", e["direction"])
                del self.direct[key]
        for key, s in list(self.escape.items()):
            e = s["event"]
            sgn = sign(e)
            if (float(row.close) - float(e["level_price"])) * sgn <= 0:
                del self.escape[key]
                continue
            contact = touched(e)
            if contact:
                if s["left"]:
                    del self.escape[key]
                    continue
                s["high"] = max(s["high"], float(row.high))
                s["low"] = min(s["low"], float(row.low))
            else:
                s["left"] = True
                extreme = s["high"] if sgn == 1 else s["low"]
                if (float(row.close) - extreme) * sgn > 0:
                    emit(e, "RETEST_RANGE_ESCAPE", e["direction"])
                    del self.escape[key]
        for e in events:
            k = e["interaction_type"]
            key = e["level_id"]
            if k == "BREAK_ACCEPTANCE":
                self.direct.pop(key, None)
                self.escape.pop(key, None)
                emit(e, "BREAK_CLOSE", e["direction"])
                if full(e):
                    emit(e, "BREAK_FIRST_FULL", e["direction"])
                else:
                    self.direct[key] = e
            elif k == "BREAK_NEXT_CANDLE_CLOSE_HOLD":
                emit(e, "BREAK_NEXT_CLOSE_HOLD", e["direction"])
            elif k == "BREAK_NEXT_CANDLE_FULL_HOLD":
                emit(e, "BREAK_NEXT_FULL_HOLD", e["direction"])
            elif k == "BREAK_RETEST_HOLD":
                emit(e, "RETEST_CLOSE_HOLD", e["direction"])
                self.escape[key] = dict(
                    event=e, high=float(row.high), low=float(row.low), left=False
                )
            elif k == "REJECTION":
                emit(
                    e,
                    "REJECTION_CLOSE",
                    "UP" if e["approach_side"] == "ABOVE" else "DOWN",
                )
            elif k == "REJECTION_CONFIRMATION":
                emit(e, "REJECTION_CONFIRMATION", e["direction"])
            elif k == "BREAK_FAILED_NEXT_CANDLE_HOLD":
                emit(
                    e, "FAILED_BREAK_CLOSE", "DOWN" if e["direction"] == "UP" else "UP"
                )
                self.fail.append(e)
        return out
