"""Zone-boundary events on confirmed 5m bars; invalidation only on full 4h close."""

from copy import deepcopy
import pandas as pd
from engine.canonical import digest


class ZoneLifecycleV2:
    def __init__(self, expected_minutes=None):
        self.states = {}
        self.events = []
        self.expected_minutes = expected_minutes
        self.last_five = None

    def add(self, zone):
        zid = zone["zone_id"]
        if zid in self.states:
            raise ValueError("Duplicate zone registration")
        self.states[zid] = dict(
            zone=deepcopy(zone),
            active=True,
            fresh=True,
            touched=False,
            entered=False,
            mitigated=False,
            invalidated=False,
            touch_number=0,
            first_touch_timestamp=None,
            deepest_penetration=0.0,
            current_penetration=0.0,
            touching=False,
            thresholds=set(),
            rejection=None,
            rejection_emitted=False,
            last_start=None,
            coverage_uncertain=False,
            full_bars_since_available=0,
            sessions=set(),
            reclaimed=False,
        )

    def _emit(self, s, b, kind, at):
        z = s["zone"]
        side = "DOWN" if z["zone_type"] == "SUPPLY" else "UP"
        e = deepcopy(z)
        e.update(
            event_id=digest([z["zone_id"], str(at), kind]),
            event_type=kind,
            timestamp=at,
            timestamp_ny=at.tz_convert("America/New_York"),
            bar_start=b["timestamp"],
            date=str(at.tz_convert("America/New_York").date()),
            direction=side,
            price=b["close"],
            open=b["open"],
            high=b["high"],
            low=b["low"],
            close=b["close"],
            touch_number=s["touch_number"],
            penetration_percent=s["current_penetration"] * 100,
            deepest_penetration_percent=s["deepest_penetration"] * 100,
            age_minutes=(at - z["availability_timestamp"]).total_seconds() / 60,
            age_full_4h_bars=s["full_bars_since_available"],
            sessions_since_available=len(s["sessions"]),
            active=s["active"],
            fresh=s["fresh"],
            touched=s["touched"],
            entered=s["entered"],
            mitigated=s["mitigated"],
            invalidated=s["invalidated"],
            coverage_uncertain=s["coverage_uncertain"],
            event_context=deepcopy(b.get("context", {})),
        )
        self.events.append(e)
        return e

    def four_hour(self, b):
        emitted = []
        if not b["complete"] or not b["full"]:
            return emitted
        at = b["availability_timestamp"]
        for s in self.states.values():
            z = s["zone"]
            if b["timestamp"] < z["availability_timestamp"]:
                continue
            s["full_bars_since_available"] += 1
            s["sessions"].add(b["session_date"])
            sign = 1 if z["zone_type"] == "SUPPLY" else -1
            if s["active"] and sign * (b["close"] - z["distal"]) > 0:
                s.update(
                    active=False, invalidated=True, invalidated_at=at, rejection=None
                )
                emitted.append(self._emit(s, b, "ZONE_INVALIDATION", at))
        return emitted

    def five_minute(self, b):
        b = {**b, **{k: float(b[k]) for k in ("open", "high", "low", "close")}}
        at = b["timestamp"] + pd.Timedelta(minutes=5)
        result = []
        if self.last_five is not None and b["timestamp"] <= self.last_five:
            raise ValueError("Five-minute bars must be chronological")
        self.last_five = b["timestamp"]
        for s in self.states.values():
            z = s["zone"]
            if b["timestamp"] < z["availability_timestamp"]:
                continue
            complete = b.get("complete", b.get("is_complete_5m", False))
            adjacent = s["last_start"] is None or b["timestamp"] == s[
                "last_start"
            ] + pd.Timedelta(minutes=5)
            if not adjacent or not complete:
                scheduled = False
                if not adjacent and self.expected_minutes is not None:
                    a = s["last_start"] + pd.Timedelta(minutes=5)
                    end = b["timestamp"]
                    scheduled = self.expected_minutes.searchsorted(
                        a
                    ) == self.expected_minutes.searchsorted(end)
                s.update(
                    touching=False,
                    rejection=None,
                    coverage_uncertain=s["coverage_uncertain"]
                    or not scheduled
                    or not complete,
                )
            s["last_start"] = b["timestamp"]
            if not complete:
                continue
            supply = z["zone_type"] == "SUPPLY"
            sign = 1 if supply else -1
            extreme = b["high"] if supply else b["low"]
            penetration = max(0.0, sign * (extreme - z["proximal"]) / z["width"])
            contact = b["low"] <= z["top"] and b["high"] >= z["bottom"]
            s["current_penetration"] = penetration if contact else 0.0
            s["deepest_penetration"] = max(
                s["deepest_penetration"], s["current_penetration"]
            )

            def emit(kind):
                result.append(self._emit(s, b, kind, at))

            if not s["active"]:
                if not s["reclaimed"] and sign * (b["close"] - z["distal"]) < 0:
                    s["reclaimed"] = True
                    emit("ZONE_INVALIDATION_RECLAIM")
                # Retest from the broken side is strict previous close beyond distal.
                prev = s.get("previous_close")
                if (
                    contact
                    and not s["touching"]
                    and prev is not None
                    and sign * (prev - z["distal"]) > 0
                ):
                    emit("ZONE_RETEST_AFTER_INVALIDATION")
                s["touching"] = contact
                s["previous_close"] = b["close"]
                continue
            pending = s["rejection"]
            s["rejection"] = None
            if (
                pending
                and adjacent
                and sign
                * (b["close"] - (pending["low"] if supply else pending["high"]))
                < 0
            ):
                emit("ZONE_REJECTION_CONFIRMATION")
            if contact and not s["touching"]:
                s["touch_number"] += 1
                s["thresholds"] = set()
                s["rejection_emitted"] = False
                s.update(fresh=False, touched=True, mitigated=True)
                if s["first_touch_timestamp"] is None:
                    s["first_touch_timestamp"] = at
                emit(
                    "ZONE_FIRST_TOUCH"
                    if s["touch_number"] == 1
                    else (
                        "ZONE_SECOND_TOUCH"
                        if s["touch_number"] == 2
                        else "ZONE_THIRD_PLUS_TOUCH"
                    )
                )
            if contact:
                if penetration > 0 and "entry" not in s["thresholds"]:
                    s["entered"] = True
                    s["thresholds"].add("entry")
                    emit("ZONE_ENTRY")
                for value, kind in [
                    (0.25, "ZONE_25_PERCENT_PENETRATION"),
                    (0.5, "ZONE_50_PERCENT_PENETRATION"),
                    (0.75, "ZONE_75_PERCENT_PENETRATION"),
                    (1.0, "ZONE_DISTAL_TOUCH"),
                ]:
                    if penetration >= value and kind not in s["thresholds"]:
                        s["thresholds"].add(kind)
                        emit(kind)
                if (
                    b["low"] <= z["bottom"]
                    and b["high"] >= z["top"]
                    and "traversal" not in s["thresholds"]
                ):
                    s["thresholds"].add("traversal")
                    emit("ZONE_FULL_TRAVERSAL")
                if (
                    sign * (b["close"] - z["proximal"]) < 0
                    and not s["rejection_emitted"]
                ):
                    s["rejection_emitted"] = True
                    s["rejection"] = deepcopy(b)
                    emit("ZONE_REJECTION")
            s["touching"] = contact
            s["previous_close"] = b["close"]
        return result
