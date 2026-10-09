"""Explicit session schedule -> exact raw-minute four-hour bars.

A schedule is input, never inferred from gaps in prices. CMES is a candidate
calendar, not an assertion that its historical holiday times match MNQ.
"""

from collections import deque
from dataclasses import dataclass, asdict
import exchange_calendars as xc
import numpy as np
import pandas as pd
from engine.canonical import digest

NY = "America/New_York"


@dataclass(frozen=True)
class SessionPreset:
    name: str = "CME_GLOBEX_4H_SESSION_ANCHORED_V1"
    timezone: str = NY
    anchor: str = "18:00"
    close: str = "17:00"
    historical_pause_end_date: str = "2021-06-28"
    calendar: str = "CMES"
    atr_length: int = 14
    atr_method: str = "SMA_TRUE_RANGE_FULL_BARS"
    shortened_policy: str = "preserve_atr_clear_formation_sequence"


def session_schedule(start, end):
    """Candidate dated schedule, frozen by caller with its hash before replay.

    CMES supplies holidays/early closes; regular closes are capped at 17 NY.
    Date endpoints are session labels inclusive. Actual source disagreements
    are surfaced by aggregate(), never repaired by learning closures from data.
    """
    c = xc.get_calendar("CMES", start=start, end=end)
    rows = []
    for day, r in c.schedule.loc[start:end].iterrows():
        label = str(day.date())
        close = min(r["close"], pd.Timestamp(label + " 17:00", tz=NY).tz_convert("UTC"))
        rows.append(
            dict(
                session_date=label,
                open=r["open"],
                close=close,
                pause_start=(
                    pd.Timestamp(label + " 16:15", tz=NY).tz_convert("UTC")
                    if label < "2021-06-28"
                    else None
                ),
                pause_end=(
                    pd.Timestamp(label + " 16:30", tz=NY).tz_convert("UTC")
                    if label < "2021-06-28"
                    else None
                ),
            )
        )
    return rows


def aggregate(raw, sessions):
    """Integer aggregation before scaling. Return bars and out-of-session rows.

    Empty expected buckets are audit records, never synthetic candles. Duplicate,
    off-grid, invalid and absent minutes disable the entire expected bucket.
    """
    m = raw.reset_index() if "ts_event" not in raw else raw.copy()
    m = m.sort_values("ts_event").set_index("ts_event")
    if (
        m.index.tz is None
        or m.index.has_duplicates
        or not (m.index == m.index.floor("min")).all()
    ):
        raise ValueError("Source minutes must be unique, aware, and minute aligned")
    covered = np.zeros(len(m), dtype=bool)
    rows = []
    for session in sessions:
        op, cl = pd.Timestamp(session["open"]), pd.Timestamp(session["close"])
        at = op
        while at < cl:
            stop = min(at + pd.Timedelta(hours=4), cl)
            expected = pd.date_range(at, stop, freq="min", inclusive="left").as_unit(
                "ns"
            )
            ps, pe = session.get("pause_start"), session.get("pause_end")
            if ps is not None and not pd.isna(ps):
                expected = expected[(expected < ps) | (expected >= pe)]
            a, b = m.index.searchsorted(at), m.index.searchsorted(stop)
            piece = m.iloc[a:b]
            covered[a:b] = True
            absent = expected.difference(piece.index)
            extra = piece.index.difference(expected)
            valid = (
                len(piece) > 0
                and np.isfinite(
                    piece[["open", "high", "low", "close"]].to_numpy()
                ).all()
                and (piece.high >= piece[["open", "close", "low"]].max(axis=1)).all()
                and (piece.low <= piece[["open", "close"]].min(axis=1)).all()
                and (piece[["open", "high", "low", "close"]] % 250_000_000 == 0)
                .all()
                .all()
            )
            complete = bool(not len(absent) and not len(extra) and valid)
            row = dict(
                timestamp=at,
                availability_timestamp=stop,
                session_date=session["session_date"],
                expected_minutes=len(expected),
                minute_count=len(piece),
                missing_minutes=len(absent),
                unexpected_minutes=len(extra),
                complete=complete,
                full=stop - at == pd.Timedelta(hours=4),
                first_missing=str(absent[0]) if len(absent) else None,
            )
            for k in ["open", "high", "low", "close"]:
                v = (
                    None
                    if piece.empty
                    else (
                        piece[k].iloc[0]
                        if k == "open"
                        else (
                            piece[k].iloc[-1]
                            if k == "close"
                            else piece[k].max() if k == "high" else piece[k].min()
                        )
                    )
                )
                row[k] = float(v / 1e9) if v is not None else np.nan
            row["volume"] = int(piece.volume.sum()) if not piece.empty else 0
            rows.append(row)
            at = stop
    return pd.DataFrame(rows), m.iloc[np.flatnonzero(~covered)].reset_index()


def with_atr(bars):
    """ATR across scheduled closures; reset on any unverified bucket.

    Shortened bars do not enter ATR but must have complete source coverage.
    True range compares against the previous eligible full close. Thus session
    gaps are included in TR without inserting a shortened candle into ATR14.
    """
    tr = deque(maxlen=14)
    previous = None
    result = []
    for row in bars.to_dict("records"):
        if not row["complete"]:
            tr.clear()
            previous = None
        elif row["full"]:
            value = row["high"] - row["low"]
            if previous is not None:
                value = max(
                    value, abs(row["high"] - previous), abs(row["low"] - previous)
                )
            tr.append(value)
            previous = row["close"]
        row.update(
            atr14=float(np.mean(tr)) if len(tr) == 14 else None,
            atr_count=len(tr),
            continuity_reset=not row["complete"],
        )
        result.append(row)
    return pd.DataFrame(result)


def identity(sessions):
    return dict(
        preset=asdict(SessionPreset()),
        calendar_library=xc.__version__,
        sessions=sessions,
        schedule_sha256=digest(sessions),
    )
