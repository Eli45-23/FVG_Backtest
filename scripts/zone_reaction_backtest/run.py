"""Three frozen Development backtests using immutable accepted zones and native fills."""

from pathlib import Path
import sys, json, hashlib, subprocess
from decimal import Decimal as D
import pandas as pd
import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.canonical import digest, dumps
from engine.zone_v2.provider import DisplacementBaseZoneProviderV2, ProviderConfig
from engine.zone_v2.lifecycle import ZoneLifecycleV2
from engine.zone_v2.acceptance import (
    assess_mechanical,
    require_mechanical_acceptance,
    REQUIRED,
)
from engine.session_calendar.mnq_v1 import profile
from engine.research.levels import valid_bar
from engine.legacy import reference as ref
from engine.partial_execution import execute
from engine.strategy import Entry
from scripts.zone_reaction_backtest.signals import Detector, bracket, selection_reason
from scripts.swing_low_feasibility.core import independent_fill
from scripts.pml_feasibility.core import short_fill
from dataclasses import asdict

P = ROOT / "work/four-hour-zone-reaction-backtest-v1/results"
F = ROOT / "work/zone-v2-calendar-foundation"
NY = "America/New_York"


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def save(name, rows):
    (rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)).to_csv(
        P / name, index=False, float_format="%.12g", lineterminator="\n"
    )


def run():
    P.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(
        (
            ROOT / "storage/event_studies/78c96aa0e91147ba9913e365f33ed2f9/config.json"
        ).read_text()
    )
    assert (cfg["start"], cfg["end"], cfg["segment"]) == (
        "2020-01-01",
        "2024-01-01",
        "development",
    )
    read = json.loads((F / "human_ground_truth_readiness.json").read_text())
    foundation = json.loads((F / "foundation_summary.json").read_text())
    assert (
        read["status"] == "READY_FOR_HUMAN_GROUND_TRUTH"
        and read["unresolved_sessions_excluded"] == 104
    )
    frames = pd.read_parquet(F / "four_hour_bar_inventory.parquet")
    assert digest(frames.to_dict("records")) == read["bars_sha256"]
    assert profile()["profile_sha256"] == read["profile_sha256"]
    provider = DisplacementBaseZoneProviderV2(frame_identity=read["profile_sha256"])
    for f in frames.to_dict("records"):
        provider.update(f)
    zones = sorted(
        provider.zones, key=lambda z: (z["availability_timestamp"], z["zone_id"])
    )
    saved = []
    for side in ["supply", "demand"]:
        saved.extend(
            json.loads(x)
            for x in pd.read_parquet(F / f"detected_{side}_zones.parquet").payload
        )
    saved = sorted(
        saved, key=lambda z: (pd.Timestamp(z["availability_timestamp"]), z["zone_id"])
    )
    assert digest(zones) == digest(saved) and len(zones) == 320
    source_hashes = {
        str(f.relative_to(ROOT)): sha(f)
        for f in [
            F / "human_ground_truth_readiness.json",
            F / "four_hour_bar_inventory.parquet",
            F / "detected_supply_zones.parquet",
            F / "detected_demand_zones.parquet",
            F / "zone_lifecycle_audit.csv",
            F / "frozen_calendar_profile.json",
        ]
    }
    for v in cfg["dataset_identity"]["files"].values():
        f = ROOT / "outputs/data" / v["name"]
        assert sha(f) == v["sha256"]
        source_hashes[str(f.relative_to(ROOT))] = v["sha256"]
    settings = dict(
        status="DEVELOPMENT_ONLY_NOT_VALIDATED",
        provider=asdict(ProviderConfig()),
        calendar=read["profile_sha256"],
        bars=read["bars_sha256"],
        dataset=cfg["dataset_identity"],
        segment="development",
        start="2020-01-01",
        end_exclusive="2024-01-01",
        setups=["A", "B", "C"],
        quantity=1,
        fee_per_side=".73",
        slippage_ticks_each_side=1,
        target_r=2,
        stop_buffer_ticks=1,
        one_position_per_setup=True,
        reentry="new episode after previous exit",
        exclusion_dates=foundation["unresolved_session_dates"],
        specification_sha256=sha(ROOT / "docs/FOUR_HOUR_ZONE_REACTION_BACKTEST_V1.md"),
    )
    provider_proof = json.loads((F / "provider_summary.json").read_text())
    chart_proof = pd.read_csv(F / "chart_audit.csv")
    test_files = [
        "tests/test_zone_reaction_backtest.py",
        "tests/test_zone_v2.py",
        "tests/test_mnq_historical_calendar.py",
        "tests/test_extended_execution.py",
        "tests/test_management.py",
    ]
    tested = subprocess.run(
        [sys.executable, "-m", "pytest", *test_files, "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if tested.returncode:
        raise RuntimeError(tested.stdout + tested.stderr)
    (P / "synthetic_test_results.txt").write_text(tested.stdout)
    # Evidence is checked independently, not supplied by a user approval flag.
    checks = dict(
        calendar_approved=read["engineering_status"] == "PASSED_FOR_ACCEPTED_SUBSET",
        source_reconciled=foundation["reconciliation_all"] is True,
        atr_initialized=foundation["first_atr"] is not None,
        synthetic_tests_pass=tested.returncode == 0,
        causal_audit_pass=provider_proof["causal"] is True,
        visual_audit_pass=len(chart_proof) == 17
        and bool(chart_proof.mechanical_pass.all()),
        nonzero_both_sides=all(
            any(z["zone_type"] == side for z in zones) for side in ["SUPPLY", "DEMAND"]
        ),
        deterministic=provider_proof["formation_deterministic"] is True
        and digest(zones) == digest(saved),
        legacy_preserved=all(
            sha(ROOT / path) == h for path, h in source_hashes.items()
        ),
    )
    assert set(checks) == set(REQUIRED)
    impl = sha(ROOT / "engine/zone_v2/provider.py")
    gate = assess_mechanical(checks, settings, impl)
    require_mechanical_acceptance(gate, settings, impl, "development")
    (P / "mechanical_research_authorization.json").write_text(dumps(gate))
    (P / "frozen_run_configuration.json").write_text(dumps(settings))
    start = pd.Timestamp("2020-01-01", tz=NY).tz_convert("UTC")
    end = pd.Timestamp("2024-01-01", tz=NY).tz_convert("UTC")
    bars = (
        pq.read_table(
            ROOT / "outputs/data" / cfg["dataset_identity"]["files"]["bars"]["name"],
            filters=[("timestamp_utc", ">=", start), ("timestamp_utc", "<", end)],
        )
        .to_pandas()
        .sort_values("timestamp_utc")
    )
    assert (
        bars.timestamp_utc.is_unique
        and bars.timestamp_utc.min() >= start
        and bars.timestamp_utc.max() < end
    )
    sessions = {
        d: tuple(map(pd.Timestamp, v))
        for d, v in cfg["calendar"]["sessions"].items()
        if "2020-01-01" <= d < "2024-01-01"
    }
    excluded = set(foundation["unresolved_session_dates"])
    eligible = {
        d: v
        for d, v in sessions.items()
        if d not in excluded and (v[1] - v[0]) == pd.Timedelta(hours=6, minutes=30)
    }
    save(
        "session_eligibility.csv",
        [
            dict(
                date=d,
                open=v[0],
                close=v[1],
                eligible=d in eligible,
                reason=(
                    "UNRESOLVED_CALENDAR"
                    if d in excluded
                    else "HALF_DAY" if d not in eligible else "FULL_SESSION"
                ),
            )
            for d, v in sessions.items()
        ],
    )
    # Merge frame confirmations and newly available zones into a causal clock.
    timeline = [
        (f["availability_timestamp"], 0, f) for f in frames.to_dict("records")
    ] + [(pd.Timestamp(z["availability_timestamp"]), 1, z) for z in zones]
    timeline.sort(key=lambda x: (x[0], x[1]))
    life = ZoneLifecycleV2()
    index = 0
    invalidated = {}
    available = {}

    def advance(at):
        nonlocal index
        while index < len(timeline) and timeline[index][0] <= at:
            timestamp, kind, item = timeline[index]
            index += 1
            if kind == 0:
                for e in life.four_hour(item):
                    invalidated[e["zone_id"]] = timestamp
                life.events = []
            else:
                life.add(item)
                available[item["zone_id"]] = item

    det = Detector()
    signals = []
    invalid_bars = 0
    for row in bars.itertuples(index=False):
        a = row.timestamp_utc
        day = str(a.tz_convert(NY).date())
        advance(a)
        session = eligible.get(day)
        if session is None or not session[0] <= a < session[1]:
            det.reset()
            continue
        known = dict(available)
        advance(a + pd.Timedelta(minutes=5))
        if not valid_bar(row):
            invalid_bars += 1
        signals.extend(det.update(row, known, invalidated, session[0]))
    advance(end)
    old = pd.read_csv(F / "zone_lifecycle_audit.csv").set_index("zone_id")
    for zid, s in life.states.items():
        old_at = old.loc[zid, "invalidated_at"]
        now = invalidated.get(zid)
        assert (pd.isna(old_at) and now is None) or pd.Timestamp(old_at) == now
    signals.sort(
        key=lambda s: (
            s["entry_time_utc"],
            pd.Timestamp(s["zone_available_at"]),
            s["zone_id"],
            s["setup"],
        )
    )
    assert len({s["signal_id"] for s in signals}) == len(signals)
    save("all_signals.csv", signals)
    print(
        "Accepted zones",
        len(zones),
        "eligible sessions",
        len(eligible),
        "signals",
        pd.Series([s["setup"] for s in signals]).value_counts().to_dict(),
        flush=True,
    )
    raw = pq.read_table(
        ROOT / "outputs/data" / cfg["dataset_identity"]["files"]["minutes"]["name"],
        filters=[("ts_event", ">=", start), ("ts_event", "<", end)],
    ).to_pandas()
    if "ts_event" not in raw:
        raw = raw.reset_index()
    assert (
        raw.ts_event.is_unique
        and raw.ts_event.min() >= start
        and raw.ts_event.max() < end
    )
    for k in ["open", "high", "low", "close"]:
        raw[k] = raw[k].map(lambda x: D(int(x)).scaleb(-9))
    raw["date"] = raw.ts_event.dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
    dates = {s["date"] for s in signals}
    days = {
        d: g.set_index("ts_event").sort_index()
        for d, g in raw.groupby("date")
        if d in dates
    }
    trades = []
    audit = []
    checks_count = 0
    for setup in ["A", "B", "C"]:
        busy_until = None
        previous_exit = None
        for signal in [s for s in signals if s["setup"] == setup]:
            close = eligible[signal["date"]][1]
            reason = selection_reason(signal, busy_until, previous_exit, close)
            economics = bracket(signal)
            if reason is None and economics["risk_points"] <= 0:
                reason = "NON_POSITIVE_RISK"
            record = {**signal, **economics, "quantity": 1}
            if reason:
                audit.append({**record, "selection_status": reason})
                continue
            day = days[signal["date"]]
            at = signal["entry_time_utc"]
            expected = int((close - at).total_seconds() / 60)
            idx = pd.date_range(at, close, freq="min", inclusive="left")
            missing = idx.difference(day.index)
            cutoff = missing[0] if len(missing) else close
            arr = day.loc[
                (day.index >= at) & (day.index < cutoff),
                ["open", "high", "low", "close"],
            ].to_numpy(dtype=float)
            independent = (
                independent_fill if signal["direction"] == "LONG" else short_fill
            )(
                arr,
                float(economics["entry_price"]),
                float(economics["stop_price"]),
                float(economics["target_price"]),
                1,
                expected,
            )
            try:
                trade, _ = execute(
                    record,
                    day,
                    ref.Config(D(".73"), 1),
                    1,
                    Entry(signal["direction"], economics["stop_price"], D(2)),
                    None,
                    {},
                    {},
                    close,
                )
            except ValueError as error:
                if "Missing execution minute" not in str(error):
                    raise
                assert independent is None
                audit.append(
                    {
                        **record,
                        "selection_status": "EXECUTION_DATA_UNAVAILABLE",
                        "first_missing_owned_minute": cutoff,
                    }
                )
                # An unresolved held position cannot license further entries in this session.
                busy_until = previous_exit = close
                continue
            assert independent is not None
            minute, exit_reason, price, conflict = independent
            assert (
                trade["exit_reason"] == exit_reason
                and float(trade["exit_price"]) == price
                and trade["same_minute_stop_target_conflict"] == conflict
            )
            assert trade["exit_time_utc"] == at + pd.Timedelta(minutes=minute + 1)
            sign = D(1) if signal["direction"] == "LONG" else D(-1)
            assert trade["net_pnl_usd"] == (
                D(str(price)) - economics["entry_price"]
            ) * sign * 2 - D("1.46")
            assert (
                trade["final_stop_price"] == economics["stop_price"]
                and trade["management_event_count"] == 0
            )
            owned = arr[: minute + 1]
            peak = max(float(economics["entry_price"]), float(owned[:, 1].max()))
            trough = min(float(economics["entry_price"]), float(owned[:, 2].min()))
            expected_mfe = (
                peak - float(economics["entry_price"])
                if sign == 1
                else float(economics["entry_price"]) - trough
            )
            expected_mae = (
                float(economics["entry_price"]) - trough
                if sign == 1
                else peak - float(economics["entry_price"])
            )
            assert (
                float(trade["mfe_points"]) == expected_mfe
                and float(trade["mae_points"]) == expected_mae
            )
            assert previous_exit is None or signal["episode_start"] >= previous_exit
            busy_until = previous_exit = trade["exit_time_utc"]
            keys = [
                "trade_id",
                "exit_time_utc",
                "exit_time_ny",
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
            trades.append({**record, **{k: trade.get(k) for k in keys}})
            audit.append({**record, "selection_status": "ENTERED"})
            checks_count += 1
        print(setup, "completed", sum(t["setup"] == setup for t in trades), flush=True)
    save("signal_selection_audit.csv", audit)
    for setup in ["A", "B", "C"]:
        rows = [t for t in trades if t["setup"] == setup]
        save(f"{setup}_trades.csv", rows)
    save("all_trades.csv", trades)
    for path, h in source_hashes.items():
        assert sha(ROOT / path) == h
    (P / "execution_verification.json").write_text(
        dumps(
            dict(
                source_hashes=source_hashes,
                zones=len(zones),
                supply=168,
                demand=152,
                calendar_unresolved_dates=len(excluded),
                eligible_full_sessions=len(eligible),
                incomplete_rth_bars=invalid_bars,
                signals=len(signals),
                completed_trades=len(trades),
                independently_checked_fills=checks_count,
                reserved_outcomes_read=False,
                source_lifecycle_invalidations_exact=True,
            )
        )
    )


if __name__ == "__main__":
    run()
