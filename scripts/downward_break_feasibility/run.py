"""Frozen eight-level downside audit; every diagnostic uses unchanged native fills."""

from pathlib import Path
import sys, json, hashlib
from decimal import Decimal as D, ROUND_CEILING

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from engine.partial_execution import execute
from engine.strategy import Entry
from engine.legacy import reference as ref
from scripts.pml_feasibility.core import short_path, short_fill

P = ROOT / "work/downward-break-execution-feasibility-v1"
SOURCE = ROOT / "work/eight-level-reaction-entry-study-v1"
NY = "America/New_York"
COUNTS = dict(
    PDH=886, PDL=917, PMH=1162, PML=1485, O5H=1636, O5L=2010, O15H=1470, O15L=1798
)
STOPS = ["LEVEL_RECLAIM", "BREAK_CANDLE_HIGH"]


def sha(p):
    with open(p, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write(name, rows):
    (rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)).to_csv(
        P / name, index=False, float_format="%.12g", lineterminator="\n"
    )


def prices(close, level, high, stop_name, ticks, target_r):
    entry = ref.tick(D(str(close))) - D(".25") * ticks
    value = level if stop_name == "LEVEL_RECLAIM" else high
    stop = ref.tick(D(str(value)) + D(".25"), ROUND_CEILING)
    risk = stop - entry
    target = ref.tick(entry - risk * D(str(target_r)))
    return entry, stop, risk, target


def prepare():
    protocol = json.loads((P / "protocol.json").read_text())
    assert (
        sha(ROOT / "docs/DOWNWARD_BREAK_EXECUTION_FEASIBILITY_V1.md")
        == protocol["specification_sha256"]
    )
    manifest = json.loads((SOURCE / "reproducibility_manifest.json").read_text())
    assert manifest["status"] == "PASS" and manifest["segment"] == "development"
    hashes = {str((P / "protocol.json").relative_to(ROOT)): sha(P / "protocol.json")}
    for name in [
        "entry_events.parquet",
        "source_events.parquet",
        "primary_evidence.csv",
        "source_identity.json",
        "protocol.json",
    ]:
        path = SOURCE / name
        assert sha(path) == manifest["artifacts"][name]["sha256"]
        hashes[str(path.relative_to(ROOT))] = sha(path)
    ev = pd.read_parquet(SOURCE / "entry_events.parquet")
    raw = (
        ev[(ev.entry_kind == "BREAK_CLOSE") & (ev.direction == "DOWN")]
        .copy()
        .sort_values(["timestamp_utc", "level_type", "event_id"])
        .reset_index(drop=True)
    )
    assert len(raw) == 11364 and raw.date.nunique() == 970 and raw.event_id.is_unique
    assert raw.groupby("level_type").size().to_dict() == COUNTS
    assert raw.date.between("2020-01-01", "2023-12-31").all()
    src = pd.read_parquet(SOURCE / "source_events.parquet")
    relevant = src[
        (src.interaction_type == "BREAK_ACCEPTANCE") & (src.direction == "DOWN")
    ]
    assert (
        set(raw.source_event_id) == set(relevant.event_id)
        and raw.source_event_id.is_unique
    )
    r = raw.merge(
        src[["event_id", "open", "high", "low", "close", "interaction_type"]],
        left_on="source_event_id",
        right_on="event_id",
        suffixes=("", "_source"),
        validate="one_to_one",
    )
    for col in ["open", "high", "low", "close", "level_price"]:
        r[col] = r[col].astype(float)
    assert (r.close < r.level_price).all() and (r.close == r.price_at_event).all()
    r["timestamp_utc"] = pd.to_datetime(r.timestamp_utc, utc=True)
    assert (
        pd.to_datetime(r.level_available_at, utc=True)
        <= r.timestamp_utc - pd.Timedelta(minutes=5)
    ).all()
    r["touch_group"] = np.where(
        r.touch_number == 1,
        "FIRST",
        np.where(r.touch_number == 2, "SECOND", "THIRD_PLUS"),
    )
    write("exact_raw_events.csv", r)
    evidence = pd.read_csv(SOURCE / "primary_evidence.csv")
    evidence = evidence[
        (evidence.entry_kind == "BREAK_CLOSE") & (evidence.direction == "DOWN")
    ]
    assert evidence.set_index("level_type").events.to_dict() == COUNTS
    write("source_reconciliation.csv", evidence)
    identity = json.loads((SOURCE / "source_identity.json").read_text())
    for name, h in identity["source_hashes"].items():
        assert sha(ROOT / name) == h
        hashes[name] = h
    start = pd.Timestamp("2020-01-01", tz=NY).tz_convert("UTC")
    end = pd.Timestamp("2024-01-01", tz=NY).tz_convert("UTC")
    info = identity["dataset"]["files"]["minutes"]
    minutes = pq.read_table(
        ROOT / "outputs/data" / info["name"],
        filters=[("ts_event", ">=", start), ("ts_event", "<", end)],
    ).to_pandas()
    if "ts_event" not in minutes:
        minutes = minutes.reset_index()
    assert (
        minutes.ts_event.is_unique
        and minutes.ts_event.min() >= start
        and minutes.ts_event.max() < end
    )
    for col in ["open", "high", "low", "close"]:
        minutes[col] = minutes[col].map(lambda v: D(int(v)).scaleb(-9))
    minutes["date"] = minutes.ts_event.dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
    wanted = set(r.date)
    days = {}
    for date, g in minutes.groupby("date"):
        if date not in wanted:
            continue
        g = g.set_index("ts_event").sort_index()
        g.index = g.index.as_unit("ns")
        values = g[["open", "high", "low", "close"]].to_numpy(dtype=float)
        assert (
            np.isfinite(values).all()
            and (values[:, 1] >= values[:, [0, 2, 3]].max(axis=1)).all()
            and (values[:, 2] <= values[:, [0, 3]].min(axis=1)).all()
        )
        days[date] = (g, g.index.asi8, values)
    print(
        "Exact reconciliation: 11,364 events / 970 dates / eight levels; no outcome eligibility.",
        flush=True,
    )
    return r, days, hashes, len(minutes)


def main():
    raw, days, hashes, minute_count = prepare()
    paths = []
    trades = []
    checks = 0
    for ix, r in enumerate(raw.itertuples()):
        at = pd.Timestamp(r.timestamp_utc)
        end = pd.Timestamp(r.session_close)
        expected = int((end - at).total_seconds() / 60)
        assert expected >= 0
        day, times, values = days[r.date]
        left = np.searchsorted(times, at.value)
        right = np.searchsorted(times, end.value)
        actual = times[left:right]
        wanted = at.value + np.arange(expected, dtype=np.int64) * 60_000_000_000
        bad = np.flatnonzero(actual != wanted[: len(actual)])
        prefix = int(bad[0]) if len(bad) else len(actual)
        gap = pd.Timestamp(int(wanted[prefix]), tz="UTC") if prefix < expected else None
        arr = values[left : left + prefix]
        atr = float(r.atr14) if pd.notna(r.atr14) and r.atr14 > 0 else None
        shared = {
            k: getattr(r, k)
            for k in [
                "event_id",
                "source_event_id",
                "root_id",
                "level_id",
                "level_type",
                "level_price",
                "date",
                "year",
                "touch_number",
                "touch_group",
                "time_bucket",
                "volatility_bucket",
            ]
        }
        for ticks in [0, 1, 2]:
            for stop_name in STOPS:
                entry, stop, risk, _ = prices(
                    r.close, r.level_price, r.high, stop_name, ticks, 1
                )
                assert entry % D(".25") == 0 and stop % D(".25") == 0
                base = dict(
                    **shared,
                    ticks=ticks,
                    stop=stop_name,
                    entry_time_utc=at,
                    entry_time_ny=at.tz_convert(NY),
                    entry_price=entry,
                    stop_price=stop,
                    risk_points=risk,
                    risk_usd=risk * 2,
                    risk_atr=float(risk) / atr if atr else None,
                    atr14=atr,
                    expected_session_minutes=expected,
                    first_missing_minute=gap,
                    quantity=1,
                )
                status = (
                    "NON_POSITIVE_RISK"
                    if risk <= 0
                    else "NO_POST_ENTRY_SESSION_MINUTES" if expected == 0 else "VALID"
                )
                if status != "VALID":
                    paths.append(dict(**base, eligibility_status=status))
                    trades.extend(
                        dict(**base, target_r=t, execution_status=status)
                        for t in [1, 2]
                    )
                    continue
                path = short_path(
                    arr, float(entry), float(stop), float(risk), atr, expected, gap
                )
                paths.append(dict(**base, eligibility_status=status, **path))
                for t in [1, 2]:
                    tp = ref.tick(entry - risk * D(t))
                    s = dict(
                        direction="SHORT",
                        entry_price=entry,
                        risk_points=risk,
                        stop_price=stop,
                        target_price=tp,
                        entry_time_utc=at,
                        entry_time_ny=at.tz_convert(NY),
                        signal_id=r.event_id,
                    )
                    independent = short_fill(
                        arr, float(entry), float(stop), float(tp), ticks, expected
                    )
                    try:
                        trade, _ = execute(
                            s,
                            day,
                            ref.Config(D(".73"), ticks),
                            1,
                            Entry("SHORT", stop, D(t)),
                            None,
                            {},
                            {},
                            end,
                        )
                    except ValueError as error:
                        assert (
                            "Missing execution minute" in str(error)
                            and independent is None
                        )
                        trades.append(
                            dict(
                                **base,
                                target_r=t,
                                target_price=tp,
                                execution_status="EXECUTION_DATA_UNAVAILABLE",
                            )
                        )
                        checks += 1
                        continue
                    assert independent is not None
                    minute, reason, price, conflict = independent
                    assert (
                        trade["exit_reason"] == reason
                        and float(trade["exit_price"]) == price
                        and trade["same_minute_stop_target_conflict"] == conflict
                    )
                    assert trade["exit_time_utc"] == at + pd.Timedelta(
                        minutes=minute + 1
                    )
                    assert trade["net_pnl_usd"] == (entry - D(str(price))) * 2 - D(
                        "1.46"
                    )
                    assert float(trade["mfe_points"]) == max(
                        0, float(entry) - arr[: minute + 1, 2].min()
                    )
                    assert float(trade["mae_points"]) == max(
                        0, arr[: minute + 1, 1].max() - float(entry)
                    )
                    assert (
                        trade["management_event_count"] == 0
                        and trade["final_stop_price"] == stop
                    )
                    keys = [
                        "exit_time_utc",
                        "exit_time_ny",
                        "exit_reason",
                        "exit_price",
                        "gross_pnl_usd",
                        "commission_usd",
                        "net_pnl_usd",
                        "result_r",
                        "gross_result_r",
                        "duration_minutes",
                        "mfe_points",
                        "mae_points",
                        "mfe_r",
                        "mae_r",
                        "same_minute_stop_target_conflict",
                    ]
                    trades.append(
                        dict(
                            **base,
                            target_r=t,
                            target_price=tp,
                            execution_status="COMPLETED",
                            adverse_stop_gap=reason == "STOP"
                            and arr[minute, 0] > float(stop),
                            **{k: trade[k] for k in keys},
                        )
                    )
                    checks += 1
        if ix % 500 == 0:
            print("Events", ix, "native independent checks", checks, flush=True)
    write("all_event_paths.csv", paths)
    write("all_target_executions.csv", trades)
    for name, h in hashes.items():
        assert sha(ROOT / name) == h, name
    (P / "execution_verification.json").write_text(
        json.dumps(
            dict(
                raw_events=len(raw),
                raw_dates=raw.date.nunique(),
                source_minutes=minute_count,
                native_independent_checks=checks,
                source_hashes_verified=hashes,
                production_execution_changed=False,
                validation_oos_outcomes_read=False,
            ),
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    print(
        "Execution complete",
        len(paths),
        "paths",
        len(trades),
        "target diagnostics",
        checks,
        "native comparisons",
        flush=True,
    )


if __name__ == "__main__":
    main()
