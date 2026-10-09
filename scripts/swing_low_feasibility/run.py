"""Frozen Development event feasibility. No strategy registration or production changes."""

from pathlib import Path
import sys, json, hashlib, shutil
from decimal import Decimal as D, ROUND_FLOOR
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.partial_execution import execute
from engine.strategy import Entry
from engine.legacy import reference as ref
from engine.strategy import Bar
from engine.research.structure import Structure, StructureConfig
from engine.research.levels import valid_bar
from engine.canonical import dumps
from core import path_measurements, independent_fill

P = ROOT / "work/5m-swing-low-execution-feasibility-v1"
S = ROOT / "storage/event_studies/5cb7fab0d4e7414792a3fbe59ded4999"
M = ROOT / "work/mnq-individual-level-master-research"


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write(name, rows):
    (rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)).to_csv(
        P / name, index=False, float_format="%.12g", lineterminator="\n"
    )


def prepare():
    cfg = json.loads((S / "config.json").read_text())
    assert (cfg["start"], cfg["end"], cfg["segment"]) == (
        "2020-01-01",
        "2024-01-01",
        "development",
    )
    frozen = json.loads((P / "reproducibility_manifest.json").read_text())
    for path, h in frozen["source_hashes_verified"].items():
        assert sha(ROOT / path) == h
    archive = P / "preflight_before_population_amendment"
    if not archive.exists():
        archive.mkdir()
        for f in list(P.iterdir()):
            if f.is_file():
                shutil.copy2(f, archive / f.name)
    protocol = {
        "status": "DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY",
        "population": "all 5319 causal TOUCH/DOWN events on 1006 dates",
        "measurement_reference": "4816/1004 only historical statistical reference, never eligibility",
        "start": "2020-01-01",
        "end": "2024-01-01",
        "dataset": cfg["dataset_identity"],
        "entries": {
            "A": "Raw touch confirmed close",
            "B": "same-observation frozen REJECTION overlap",
            "C": "same-observation frozen SWEEP_RECLAIM overlap",
        },
        "stops": {"A": "level - 0.25", "B": "event candle low - 0.25"},
        "targets_r": [0.5, 1, 1.5],
        "slippage_ticks_each_side": [0, 1, 2],
        "primary_ticks": 1,
        "fees": {
            "commission": ".25",
            "exchange": ".35",
            "clearing": ".12",
            "NFA": ".01",
            "per_side": ".73",
            "round_trip": "1.46",
            "source": "user-supplied actual observed Webull MNQ",
        },
        "size": 1,
        "daily_limit": "NONE: independent overlapping event diagnostics, not a portfolio backtest",
        "path_scope": "stop-bounded to actual session close; target races measured before stop; full exit-minute extrema included and intraminute order flagged",
        "excursion_horizons_minutes": [15, 30, 60],
        "missing": "first required missing owned minute -> EXECUTION_DATA_UNAVAILABLE; do not reject source signal",
        "at_session_close": "retain signal; NO_POST_ENTRY_SESSION_MINUTES; no synthetic same-close round trip",
        "mae_before_hit": "lower=prior complete minute extrema; upper=including target minute; unknown low ordering explicitly marked",
        "same_minute": "adverse/stop first",
        "recommendation": "qualitative frozen gates; no target chosen by best in-sample P&L; at most one hypothesis, may be none",
    }
    (P / "frozen_execution_protocol.json").write_text(dumps(protocol))
    allrows = pq.read_table(
        S / "v2_events.parquet",
        filters=[
            ("level_type", "=", "5m_SWING_LOW"),
            ("date", ">=", "2020-01-01"),
            ("date", "<", "2024-01-01"),
        ],
    ).to_pandas()
    payload = pd.DataFrame([json.loads(x) for x in allrows.payload])
    raw = (
        payload[(payload.interaction_type == "TOUCH") & (payload.direction == "DOWN")]
        .copy()
        .sort_values(["timestamp_utc", "event_id"])
        .reset_index(drop=True)
    )
    assert (
        len(raw) == 5319
        and raw.date.nunique() == 1006
        and raw.event_id.is_unique
        and raw.observation_id.is_unique
    )
    measured = pd.read_parquet(M / "08_5M_SWING_LOW/outcomes_30.parquet")
    measured = measured[
        (measured.interaction_type == "TOUCH") & (measured.direction == "DOWN")
    ]
    assert (
        set(measured.event_id) == set(raw.event_id) and measured.complete.sum() == 4821
    )
    assert measured.censor_reason.value_counts().to_dict() == {
        "OUTSIDE_SESSION": 497,
        "MISSING_MINUTES": 1,
    }
    good = measured.dropna(subset=["up_a1", "b_up_a1", "down_a1", "b_down_a1"])
    assert len(good) == 4816 and good.date.nunique() == 1004
    assert raw.atr14.isna().sum() == 5
    for kind, col in [("REJECTION", "is_rejection"), ("SWEEP_RECLAIM", "is_sweep")]:
        other = payload[payload.interaction_type == kind].set_index("observation_id")
        raw[col] = raw.observation_id.isin(other.index)
        for r in raw[raw[col]].itertuples():
            assert other.loc[r.observation_id, "timestamp_utc"] == r.timestamp_utc
    for col in ["open", "high", "low", "close", "level_price"]:
        raw[col] = raw[col].map(D)
    raw["close_position"] = np.where(
        raw.close > raw.level_price,
        "ABOVE",
        np.where(raw.close == raw.level_price, "AT", "BELOW"),
    )
    raw["exact_level_touch"] = raw.low == raw.level_price
    raw["penetrated"] = raw.low < raw.level_price
    raw["wick_only_touch"] = (
        (raw.low <= raw.level_price)
        & (raw.open > raw.level_price)
        & (raw.close > raw.level_price)
    )
    raw["penetrate_reclaim"] = raw.penetrated & (raw.close > raw.level_price)
    raw["penetrate_close_below"] = raw.penetrated & (raw.close < raw.level_price)
    raw["touch_group"] = raw.touch_number.map(
        lambda x: "1" if x == 1 else "2" if x == 2 else "3+"
    )
    raw["year"] = raw.date.str[:4].astype(int)
    # Independently replay only Development 5m confirmed pivots to reconstruct PRE-event broken state.
    start = pd.Timestamp("2020-01-01", tz="America/New_York").tz_convert("UTC")
    end = pd.Timestamp("2024-01-01", tz="America/New_York").tz_convert("UTC")
    barsfile = ROOT / "outputs/data" / cfg["dataset_identity"]["files"]["bars"]["name"]
    bars = pq.read_table(
        barsfile,
        filters=[
            ("timestamp_utc", ">=", start),
            ("timestamp_utc", "<", end),
        ],
    ).to_pandas()
    bystart = {pd.Timestamp(r.bar_start_utc): r for r in raw.itertuples()}
    contexts = {}
    structure = Structure(
        StructureConfig(**cfg["research_settings"]["structure"]), "5m"
    )
    last = None
    for b in bars.itertuples(index=False):
        at = b.timestamp_utc
        if at in bystart:
            event = bystart[at]
            s = structure.low
            assert (
                s
                and s["id"] == event.level_id
                and D(str(s["price"])) == event.level_price
            )
            assert s["availability_timestamp"] <= at
            contexts[event.event_id] = {
                "swing_progression": s["progression"] or "UNCLASSIFIED",
                "swing_formation_timestamp": s["formation_timestamp"],
                "swing_confirmation_timestamp": s["availability_timestamp"],
                "already_broken_before_touch": s["id"] in structure.broken,
            }
        contiguous = last is not None and at - last == pd.Timedelta(minutes=5)
        last = at
        if not valid_bar(b):
            structure.window.clear()
            continue
        structure.update(
            Bar(at, b.open, b.high, b.low, b.close, int(b.volume)),
            at + pd.Timedelta(minutes=5),
            None,
            contiguous,
        )
    assert len(contexts) == 5319
    for k in next(iter(contexts.values())):
        raw[k] = raw.event_id.map(lambda x: contexts[x][k])
    raw["entry_at_session_close"] = [
        pd.Timestamp(r.timestamp_utc) == pd.Timestamp(r.session_close)
        for r in raw.itertuples()
    ]
    assert raw.entry_at_session_close.sum() == 77
    columns = [
        "event_id",
        "observation_id",
        "date",
        "year",
        "timestamp_utc",
        "bar_start_utc",
        "session_close",
        "level_id",
        "level_price",
        "level_available_at",
        "open",
        "high",
        "low",
        "close",
        "atr14",
        "touch_number",
        "touch_group",
        "close_position",
        "is_rejection",
        "is_sweep",
        "exact_level_touch",
        "penetrated",
        "wick_only_touch",
        "penetrate_reclaim",
        "penetrate_close_below",
        "structure_state",
        "swing_progression",
        "swing_formation_timestamp",
        "swing_confirmation_timestamp",
        "already_broken_before_touch",
        "entry_at_session_close",
    ]
    write("exact_touch_events.csv", raw[columns])
    write(
        "overlap_rejection_sweep.csv",
        raw[["event_id", "observation_id", "is_rejection", "is_sweep"]],
    )
    classifications = []
    for category in ["ABOVE", "AT", "BELOW"]:
        n = int(raw.close_position.eq(category).sum())
        classifications.append(
            dict(
                category="close_" + category,
                count=n,
                pct=100 * n / len(raw),
                denominator=len(raw),
            )
        )
    for col in [
        "is_rejection",
        "is_sweep",
        "exact_level_touch",
        "penetrated",
        "wick_only_touch",
        "penetrate_reclaim",
        "penetrate_close_below",
        "already_broken_before_touch",
    ]:
        n = int(raw[col].sum())
        classifications.append(
            dict(category=col, count=n, pct=100 * n / len(raw), denominator=len(raw))
        )
    for tg in ["1", "2", "3+"]:
        n = int(raw.touch_group.eq(tg).sum())
        classifications.append(
            dict(
                category="touch_" + tg,
                count=n,
                pct=100 * n / len(raw),
                denominator=len(raw),
            )
        )
    write("touch_close_classification.csv", classifications)
    minutesfile = (
        ROOT / "outputs/data" / cfg["dataset_identity"]["files"]["minutes"]["name"]
    )
    data = pq.read_table(
        minutesfile,
        columns=["ts_event", "open", "high", "low", "close", "volume"],
        filters=[("ts_event", ">=", start), ("ts_event", "<", end)],
    ).to_pandas()
    if "ts_event" not in data.columns:
        data = data.reset_index()
    assert (
        data.ts_event.is_unique
        and data.ts_event.ge(start).all()
        and data.ts_event.lt(end).all()
    )
    for c in ["open", "high", "low", "close"]:
        data[c] = data[c].map(lambda x: D(int(x)).scaleb(-9))
    groups = {
        str(day): g.set_index("ts_event", drop=False)
        for day, g in data.groupby(
            data.ts_event.dt.tz_convert("America/New_York").dt.date
        )
    }
    print(
        "Reconciled raw 5319/1006; historical 4816/1004; overlaps",
        int(raw.is_rejection.sum()),
        int(raw.is_sweep.sum()),
        flush=True,
    )
    return raw, groups, cfg


def run():
    raw, days, cfg = prepare()
    paths = []
    targets = []
    checks = 0
    for ix, r in enumerate(raw.itertuples()):
        at = pd.Timestamp(r.timestamp_utc)
        end = pd.Timestamp(r.session_close)
        expected = int((end - at).total_seconds() / 60)
        assert (
            at == pd.Timestamp(r.bar_start_utc) + pd.Timedelta(minutes=5)
            and expected >= 0
        )
        day = days[r.date]
        window = day.loc[(day.index >= at) & (day.index < end)]
        wanted = (
            pd.date_range(at, end, freq="min", inclusive="left")
            if expected
            else pd.DatetimeIndex([], tz="UTC")
        )
        missing = wanted.difference(window.index)
        gap = missing[0] if len(missing) else None
        prefix = window.loc[window.index < gap] if gap is not None else window
        arr = prefix[["open", "high", "low", "close"]].to_numpy(dtype=float)
        atr = float(r.atr14) if pd.notna(r.atr14) and r.atr14 > 0 else None
        shared = {
            k: getattr(r, k)
            for k in [
                "event_id",
                "date",
                "year",
                "is_rejection",
                "is_sweep",
                "touch_group",
                "swing_progression",
                "structure_state",
                "already_broken_before_touch",
            ]
        }
        for ticks in [0, 1, 2]:
            entry = ref.tick(r.close) + D(".25") * ticks
            for stopname, value in [("A", r.level_price), ("B", r.low)]:
                stop = ref.tick(value - D(".25"), ROUND_FLOOR)
                assert entry % D(".25") == 0 and stop % D(".25") == 0
                risk = entry - stop
                base = {
                    **shared,
                    "ticks": ticks,
                    "stop": stopname,
                    "entry_time_utc": at,
                    "entry_price": entry,
                    "stop_price": stop,
                    "risk_points": risk,
                    "risk_usd": risk * 2,
                    "signal_candle_crossed_future_stop": r.low <= stop,
                    "risk_atr": float(risk) / atr if atr else None,
                    "atr14": atr,
                    "expected_session_minutes": expected,
                    "first_missing_minute": gap,
                }
                status = (
                    "NON_POSITIVE_RISK"
                    if risk <= 0
                    else "NO_POST_ENTRY_SESSION_MINUTES" if expected == 0 else "VALID"
                )
                if status != "VALID":
                    paths.append({**base, "eligibility_status": status})
                    for target in [0.5, 1, 1.5]:
                        targets.append(
                            {**base, "target_r": target, "execution_status": status}
                        )
                    continue
                path = path_measurements(
                    arr, float(entry), float(stop), float(risk), atr, expected, gap
                )
                paths.append({**base, "eligibility_status": "VALID", **path})
                for target in [0.5, 1, 1.5]:
                    tp = ref.tick(entry + risk * D(str(target)))
                    signal = {
                        "direction": "LONG",
                        "entry_price": entry,
                        "risk_points": risk,
                        "stop_price": stop,
                        "target_price": tp,
                        "entry_time_utc": at,
                        "entry_time_ny": at.tz_convert("America/New_York"),
                        "signal_id": r.event_id,
                    }
                    independent = independent_fill(
                        arr, float(entry), float(stop), float(tp), ticks, expected
                    )
                    try:
                        trade, _ = execute(
                            signal,
                            day,
                            ref.Config(D(".73"), ticks),
                            1,
                            Entry("LONG", stop, D(str(target))),
                            None,
                            {},
                            {},
                            end,
                        )
                    except ValueError as error:
                        assert "Missing execution minute" in str(error), str(error)
                        assert gap is not None and independent is None
                        targets.append(
                            {
                                **base,
                                "target_r": target,
                                "target_price": tp,
                                "execution_status": "EXECUTION_DATA_UNAVAILABLE",
                                "missing_owned_minute": gap,
                            }
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
                    assert trade["net_pnl_usd"] == (D(str(price)) - entry) * 2 - D(
                        "1.46"
                    )
                    assert trade["mfe_points"] == max(
                        D(0), D(str(arr[: minute + 1, 1].max())) - entry
                    )
                    assert trade["mae_points"] == max(
                        D(0), entry - D(str(arr[: minute + 1, 2].min()))
                    )
                    assert (
                        trade["management_event_count"] == 0
                        and trade["final_stop_price"] == stop
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
                    targets.append(
                        {
                            **base,
                            "target_r": target,
                            "target_price": tp,
                            "execution_status": "COMPLETED",
                            **{k: trade[k] for k in keys},
                        }
                    )
                    checks += 1
        if ix % 500 == 0:
            print("Events", ix, "native checks", checks, flush=True)
    write("all_event_paths.csv", paths)
    write("all_target_executions.csv", targets)
    (P / "execution_verification.json").write_text(
        dumps(
            {
                "raw_events": len(raw),
                "raw_dates": raw.date.nunique(),
                "native_executor_vs_independent_checks": checks,
                "no_signal_filters": True,
                "reserved_outcomes_read": False,
                "data_hashes_after": {
                    k: sha(ROOT / "outputs/data" / v["name"])
                    for k, v in cfg["dataset_identity"]["files"].items()
                },
            }
        )
    )
    for k, v in cfg["dataset_identity"]["files"].items():
        assert sha(ROOT / "outputs/data" / v["name"]) == v["sha256"]
    print("Execution complete", len(paths), len(targets), checks, flush=True)


if __name__ == "__main__":
    run()
