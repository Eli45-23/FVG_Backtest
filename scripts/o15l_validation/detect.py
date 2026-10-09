"""Portable frozen detector. No outcome series is accepted by generate()."""

import sys, json, hashlib
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.research.levels import LevelEngine, SessionConfig, FIVE, NY, valid_bar
from engine.research.indicators import Indicators, IndicatorConfig
from engine.research.events import EventDetector
from scripts.eight_level_study.core import Opening15, Entries
from scripts.level_combination.core import context, wait_entry
from scripts.o15l_clear_hold.run import sha

P = ROOT / "work/o15l-clear-hold-validation-v1"
SOURCE = ROOT / "work/eight-level-reaction-entry-study-v1"


def write(name, rows):
    pd.DataFrame(rows).to_csv(
        P / name, index=False, float_format="%.12g", lineterminator="\n"
    )


def save(name, x):
    (P / name).write_text(
        json.dumps(x, sort_keys=True, indent=2, default=str, allow_nan=False) + "\n"
    )


def load_bars(start, end):
    assert "2020-01-01" <= start < end <= "2025-01-01"
    identity = json.loads((SOURCE / "source_identity.json").read_text())
    path = ROOT / "outputs/data" / identity["dataset"]["files"]["bars"]["name"]
    assert sha(path) == identity["dataset"]["files"]["bars"]["sha256"]
    lo = pd.Timestamp(start, tz=NY).tz_convert("UTC")
    hi = pd.Timestamp(end, tz=NY).tz_convert("UTC")
    bars = (
        pq.read_table(
            path, filters=[("timestamp_utc", ">=", lo), ("timestamp_utc", "<", hi)]
        )
        .to_pandas()
        .sort_values("timestamp_utc")
    )
    assert (
        bars.timestamp_utc.is_unique
        and bars.timestamp_utc.between(lo, hi, inclusive="left").all()
    )
    sessions = {
        d: tuple(map(pd.Timestamp, t))
        for d, t in identity["calendar"]["sessions"].items()
        if d < end
    }
    return bars, sessions, identity


def generate(bars, sessions, start, end):
    opening = Opening15(sessions)
    levels = LevelEngine(SessionConfig("00:00", "09:30"), sessions)
    det = EventDetector(SessionConfig())
    entries = Entries()
    indicators = Indicators(IndicatorConfig())
    roots = []
    previous = None
    coverage = {}
    byday = {}
    for row in bars.itertuples(index=False):
        at = row.timestamp_utc
        now = at + FIVE
        day = str(at.tz_convert(NY).date())
        session = sessions.get(day)
        known = opening.active(at)
        opening.update(row)
        levels.update(row)
        f = indicators.update(
            row,
            at,
            complete=valid_bar(row),
            contiguous=previous is not None and at - previous == FIVE,
            session_close=session[1] if session else None,
        )
        previous = at
        events = det.update(row, known, session)
        ctx = {"atr14": f.get("atr14")}
        found = entries.update(row, events, ctx, session)
        if not start <= day < end:
            continue
        byday.setdefault(day, []).append(row)
        known_now = [*levels.active(now), *opening.active(now)]
        for l in known_now:
            coverage[(day, l.level_type)] = dict(
                date=day,
                level=l.level_type,
                price=float(l.price),
                availability=l.availability_timestamp,
                available=True,
            )
        for e in found:
            if (
                e["entry_kind"] != "BREAK_CLOSE"
                or e["level_type"] != "O15L"
                or e["direction"] != "UP"
            ):
                continue
            e.update(
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                open=float(row.open),
            )
            e.update(
                context(
                    e,
                    [
                        dict(
                            level=l.level_type,
                            price=float(l.price),
                            availability=l.availability_timestamp,
                            available=True,
                        )
                        for l in known_now
                    ],
                )
            )
            e.update(
                original_timestamp=e["timestamp_utc"],
                original_close=e["price_at_event"],
                opportunity_id=e["event_id"],
            )
            roots.append(e)
    signals = []
    opportunities = []
    for e in roots:
        if not e["obstacle_count"]:
            continue
        w, reason = wait_entry(e, byday[e["date"]])
        opportunities.append(
            dict(opportunity_id=e["event_id"], date=e["date"], reason=reason)
        )
        if w:
            e = {
                **e,
                **w,
                "policy": "WAIT_CLEAR_HOLD",
                "entry_id": e["event_id"] + ":WAIT_CLEAR_HOLD",
            }
            signals.append(e)
    signals.sort(key=lambda e: (pd.Timestamp(e["timestamp_utc"]), e["entry_id"]))
    return signals, roots, opportunities, list(coverage.values())


def reconcile_development():
    bars, sessions, _ = load_bars("2020-01-01", "2024-01-01")
    signals, roots, opps, _ = generate(bars, sessions, "2020-01-01", "2024-01-01")
    original = pd.read_csv(ROOT / "work/level-combination-study-v1/causal_signals.csv")
    original = original[
        (original.level_type == "O15L")
        & (original.direction == "UP")
        & (original.policy == "WAIT_CLEAR_HOLD")
    ].set_index("entry_id")
    assert len(signals) == len(original) == 280
    assert set(e["entry_id"] for e in signals) == set(original.index)
    audit = []
    for e in signals:
        old = original.loc[e["entry_id"]]
        for k in [
            "timestamp_utc",
            "original_timestamp",
            "level_available_at",
            "session_close",
        ]:
            assert pd.Timestamp(e[k]) == pd.Timestamp(old[k]), k
        for k in [
            "price_at_event",
            "original_close",
            "low",
            "high",
            "level_price",
            "barrier_price",
            "confirmation_low",
            "confirmation_high",
        ]:
            assert float(e[k]) == float(old[k]), k
        assert format(float(e["atr14"]), ".12g") == format(old.atr14, ".12g")
        assert e["obstacle_levels"] == old.obstacle_levels
        audit.append(
            dict(entry_id=e["entry_id"], exact_signal_match=True, causal_atr_match=True)
        )
    write("development_signal_reconciliation.csv", audit)
    save(
        "development_detection_gate.json",
        dict(
            status="PASS",
            signals=len(signals),
            obstacle_opportunities=len(opps),
            raw_roots=len(roots),
            validation_rows_read=False,
        ),
    )
    print("Development causal identities PASS", len(signals), len(opps), flush=True)


if __name__ == "__main__":
    reconcile_development()
