"""Development-only combinations. Native fills, independent verification, no DB writes."""

from pathlib import Path
import sys, json, hashlib
from decimal import Decimal as D

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
from engine.partial_execution import execute
from engine.strategy import Entry
from engine.legacy import reference as ref
from scripts.swing_low_feasibility.core import independent_fill
from scripts.pml_feasibility.core import short_fill
from scripts.level_combination.core import context, wait_entry

P = ROOT / "work/level-combination-study-v1"
SOURCE = ROOT / "work/eight-level-reaction-entry-study-v1"
NY = "America/New_York"


def sha(p):
    with open(p, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write(name, data):
    pd.DataFrame(data).to_csv(
        P / name, index=False, float_format="%.12g", lineterminator="\n"
    )


def main():
    protocol = json.loads((P / "protocol.json").read_text())
    assert (
        sha(ROOT / "docs/LEVEL_COMBINATION_STUDY_V1.md")
        == protocol["specification_sha256"]
    )
    manifest = json.loads((SOURCE / "reproducibility_manifest.json").read_text())
    assert manifest["status"] == "PASS" and manifest["segment"] == "development"
    hashes = {}
    for name in [
        "entry_events.parquet",
        "source_events.parquet",
        "level_coverage.csv",
        "source_identity.json",
    ]:
        path = SOURCE / name
        assert sha(path) == manifest["artifacts"][name]["sha256"]
        hashes[str(path.relative_to(ROOT))] = sha(path)
    identity = json.loads((SOURCE / "source_identity.json").read_text())
    for name, h in identity["source_hashes"].items():
        assert sha(ROOT / name) == h
        hashes[name] = h
    ev = pd.read_parquet(SOURCE / "entry_events.parquet")
    raw = ev[ev.entry_kind.isin(["BREAK_CLOSE", "REJECTION_CLOSE"])].copy()
    src = pd.read_parquet(SOURCE / "source_events.parquet")
    raw = raw.merge(
        src[["event_id", "high", "low", "close"]],
        left_on="source_event_id",
        right_on="event_id",
        suffixes=("", "_src"),
        validate="many_to_one",
    )
    raw = raw.sort_values(
        ["timestamp_utc", "level_type", "entry_kind", "event_id"]
    ).reset_index(drop=True)
    assert raw.event_id.is_unique and raw.date.between("2020-01-01", "2023-12-31").all()
    assert (raw.price_at_event.astype(float) == raw.close.astype(float)).all()
    raw["timestamp_utc"] = pd.to_datetime(raw.timestamp_utc, utc=True)
    coverage = pd.read_csv(SOURCE / "level_coverage.csv")
    assert coverage.date.between("2020-01-01", "2023-12-31").all()
    levels = {d: g.to_dict("records") for d, g in coverage.groupby("date")}
    start = pd.Timestamp("2020-01-01", tz=NY).tz_convert("UTC")
    end = pd.Timestamp("2024-01-01", tz=NY).tz_convert("UTC")
    files = identity["dataset"]["files"]
    bars = (
        pq.read_table(
            ROOT / "outputs/data" / files["bars"]["name"],
            filters=[("timestamp_utc", ">=", start), ("timestamp_utc", "<", end)],
        )
        .to_pandas()
        .sort_values("timestamp_utc")
    )
    assert bars.timestamp_utc.between(start, end, inclusive="left").all()
    bars["date"] = bars.timestamp_utc.dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
    bar_days = {d: list(g.itertuples(index=False)) for d, g in bars.groupby("date")}
    indexed = bars.set_index("timestamp_utc")
    for r in raw.itertuples(index=False):
        b = indexed.loc[r.timestamp_utc - pd.Timedelta(minutes=5)]
        assert bool(b.is_complete_5m)
        assert all(
            float(getattr(r, c)) == float(b[c]) for c in ["high", "low", "close"]
        )
        assert pd.Timestamp(r.level_available_at) <= r.timestamp_utc - pd.Timedelta(
            minutes=5
        )
    signals = []
    audits = []
    for e in raw.to_dict("records"):
        e.update(context(e, levels[e["date"]]))
        e["original_timestamp"] = e["timestamp_utc"]
        e["original_close"] = e["price_at_event"]
        e["policy"] = "IMMEDIATE" if e["entry_kind"] == "BREAK_CLOSE" else "REJECTION"
        e["opportunity_id"] = e["event_id"]
        e["entry_id"] = e["event_id"] + ":" + e["policy"]
        signals.append(e.copy())
        if e["entry_kind"] == "BREAK_CLOSE" and e["obstacle_count"]:
            w, reason = wait_entry(e, bar_days[e["date"]])
            audits.append(
                dict(
                    opportunity_id=e["event_id"],
                    date=e["date"],
                    year=e["year"],
                    level_type=e["level_type"],
                    direction=e["direction"],
                    reason=reason,
                    wait_entered=w is not None,
                    original_timestamp=e["timestamp_utc"],
                    wait_timestamp=w["timestamp_utc"] if w else None,
                )
            )
            if w:
                e.update(w)
                e["policy"] = "WAIT_CLEAR_HOLD"
                e["entry_id"] = e["event_id"] + ":WAIT_CLEAR_HOLD"
                signals.append(e.copy())
    signals = pd.DataFrame(signals).sort_values(["timestamp_utc", "entry_id"])
    write("causal_signals.csv", signals)
    write("waiting_opportunities.csv", audits)
    write(
        "raw_reconciliation.csv",
        raw.groupby(["level_type", "entry_kind", "direction"])
        .agg(events=("event_id", "size"), dates=("date", "nunique"))
        .reset_index(),
    )
    print(
        "Causal detection",
        len(raw),
        "raw",
        len(signals),
        "entries",
        len(audits),
        "waiting opportunities",
        flush=True,
    )
    mins = pq.read_table(
        ROOT / "outputs/data" / files["minutes"]["name"],
        filters=[("ts_event", ">=", start), ("ts_event", "<", end)],
    ).to_pandas()
    if "ts_event" not in mins:
        mins = mins.reset_index()
    assert (
        mins.ts_event.is_unique
        and mins.ts_event.between(start, end, inclusive="left").all()
    )
    for c in ["open", "high", "low", "close"]:
        mins[c] = mins[c].map(lambda v: D(int(v)).scaleb(-9))
    mins["date"] = mins.ts_event.dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
    days = {}
    for d, g in mins.groupby("date"):
        if d not in levels:
            continue
        g = g.set_index("ts_event").sort_index()
        g.index = g.index.as_unit("ns")
        days[d] = (
            g,
            g.index.asi8,
            g[["open", "high", "low", "close"]].to_numpy(dtype=float),
        )
    results = []
    checks = 0
    for ix, r in enumerate(signals.to_dict("records")):
        at = pd.Timestamp(r["timestamp_utc"])
        end = pd.Timestamp(r["session_close"])
        expected = int((end - at).total_seconds() / 60)
        assert expected >= 0 and at >= pd.Timestamp(r["original_timestamp"])
        day, times, values = days[r["date"]]
        left = np.searchsorted(times, at.value)
        right = np.searchsorted(times, end.value)
        actual = times[left:right]
        wanted = at.value + np.arange(expected, dtype=np.int64) * 60_000_000_000
        bad = np.flatnonzero(actual != wanted[: len(actual)])
        prefix = int(bad[0]) if len(bad) else len(actual)
        arr = values[left : left + prefix]
        s = 1 if r["direction"] == "UP" else -1
        direction = "LONG" if s == 1 else "SHORT"
        stop = ref.tick(
            D(str(r["low"])) - D(".25") if s == 1 else D(str(r["high"])) + D(".25")
        )
        for ticks in [0, 1, 2]:
            entry = ref.tick(D(str(r["price_at_event"]))) + D(".25") * ticks * s
            risk = (entry - stop) * s
            for target_r in [1, 2]:
                target = ref.tick(entry + s * risk * target_r)
                b = {
                    k: r[k]
                    for k in [
                        "entry_id",
                        "opportunity_id",
                        "date",
                        "year",
                        "level_type",
                        "direction",
                        "policy",
                        "cluster_group",
                        "obstacle_count",
                        "known_level_count",
                        "full_level_coverage",
                        "room_atr",
                        "atr14",
                        "time_bucket",
                        "volatility_bucket",
                    ]
                }
                b.update(
                    ticks=ticks,
                    target_r=target_r,
                    entry_time_utc=at,
                    entry_time_ny=at.tz_convert(NY),
                    entry_price=entry,
                    stop_price=stop,
                    target_price=target,
                    risk_points=risk,
                    risk_usd=risk * 2,
                    wait_minutes=(
                        at - pd.Timestamp(r["original_timestamp"])
                    ).total_seconds()
                    / 60,
                )
                assert stop % D(".25") == 0 and entry % D(".25") == 0
                if risk <= 0 or expected == 0:
                    results.append(
                        dict(
                            **b,
                            execution_status=(
                                "NON_POSITIVE_RISK"
                                if risk <= 0
                                else "NO_POST_ENTRY_SESSION_MINUTES"
                            ),
                        )
                    )
                    continue
                independent = (independent_fill if s == 1 else short_fill)(
                    arr, float(entry), float(stop), float(target), ticks, expected
                )
                sig = dict(
                    direction=direction,
                    entry_price=entry,
                    risk_points=risk,
                    stop_price=stop,
                    target_price=target,
                    entry_time_utc=at,
                    entry_time_ny=at.tz_convert(NY),
                    signal_id=r["entry_id"],
                )
                try:
                    t, _ = execute(
                        sig,
                        day,
                        ref.Config(D(".73"), ticks),
                        1,
                        Entry(direction, stop, D(target_r)),
                        None,
                        {},
                        {},
                        end,
                    )
                except ValueError as error:
                    assert (
                        "Missing execution minute" in str(error) and independent is None
                    )
                    results.append(
                        dict(**b, execution_status="EXECUTION_DATA_UNAVAILABLE")
                    )
                    continue
                assert independent is not None
                minute, reason, price, conflict = independent
                assert (
                    t["exit_reason"] == reason
                    and float(t["exit_price"]) == price
                    and t["same_minute_stop_target_conflict"] == conflict
                )
                assert t["exit_time_utc"] == at + pd.Timedelta(minutes=minute + 1)
                assert t["net_pnl_usd"] == (D(str(price)) - entry) * 2 * s - D("1.46")
                assert (
                    t["final_stop_price"] == stop and t["management_event_count"] == 0
                )
                keys = [
                    "exit_time_utc",
                    "exit_reason",
                    "exit_price",
                    "gross_pnl_usd",
                    "commission_usd",
                    "net_pnl_usd",
                    "result_r",
                    "duration_minutes",
                    "mfe_points",
                    "mae_points",
                    "mfe_r",
                    "mae_r",
                    "same_minute_stop_target_conflict",
                ]
                results.append(
                    dict(**b, execution_status="COMPLETED", **{k: t[k] for k in keys})
                )
                checks += 1
        if ix % 2000 == 0:
            print("Entries", ix, "independent fill checks", checks, flush=True)
    write("all_executions.csv", results)
    for name, h in hashes.items():
        assert sha(ROOT / name) == h, name
    summary = dict(
        raw_events=len(raw),
        raw_dates=raw.date.nunique(),
        entry_records=len(signals),
        waiting_opportunities=len(audits),
        native_independent_checks=checks,
        source_minutes=len(mins),
        source_hashes=hashes,
        validation_oos_outcomes_read=False,
        production_execution_changed=False,
    )
    (P / "execution_verification.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    print(summary["raw_events"], summary["entry_records"], checks, flush=True)


if __name__ == "__main__":
    main()
