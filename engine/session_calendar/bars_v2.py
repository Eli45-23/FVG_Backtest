"""New auditable bar inventory; never changes the V1 candidate implementation."""

import pandas as pd
from engine.zone_v2.frames import aggregate, with_atr
from engine.session_calendar.mnq_v1 import CALENDAR, BARS
from engine.canonical import digest


def build(raw, sessions):
    bars, extra = aggregate(raw, sessions)
    lookup = {s["session_date"]: s for s in sessions}
    m = raw.reset_index() if "ts_event" not in raw else raw.copy()
    idx = pd.DatetimeIndex(m.ts_event).sort_values()
    for i, b in bars.iterrows():
        s = lookup[b.session_date]
        a = idx[
            idx.searchsorted(b.timestamp) : idx.searchsorted(b.availability_timestamp)
        ]
        bars.loc[i, "actual_last_source_minute"] = str(a.max()) if len(a) else None
        bars.loc[i, "source_complete"] = b.complete
        bars.loc[i, "schedule_resolved"] = s["resolved"]
        bars.loc[i, "official_expected_minutes"] = (
            b.expected_minutes if s["resolved"] else float("nan")
        )
        bars.loc[i, "official_schedule_version"] = CALENDAR
        bars.loc[i, "bar_profile"] = BARS
        bars.loc[i, "session_id"] = s["session_id"]
        bars.loc[i, "bar_id"] = digest(
            [
                s["profile_sha256"],
                s["session_id"],
                b.timestamp,
                b.availability_timestamp,
            ]
        )
        bars.loc[i, "source_coverage_status"] = (
            "UNRESOLVED_SESSION"
            if not s["resolved"]
            else "COMPLETE" if b.complete else "SOURCE_COVERAGE_INCOMPLETE"
        )
        bars.loc[i, "exclusion_reason"] = (
            "UNRESOLVED_SESSION"
            if not s["resolved"]
            else (
                "MISSING_OR_UNEXPECTED_SOURCE_MINUTES"
                if not b.complete
                else "SHORTENED_FORMATION_INELIGIBLE" if not b.full else ""
            )
        )
        if not s["resolved"]:
            bars.loc[i, "complete"] = False
    bars = with_atr(bars)
    bars["formation_eligible"] = bars.complete & bars.full & bars.atr14.notna()
    return bars, extra
