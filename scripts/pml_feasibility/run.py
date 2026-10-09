"""Reconcile frozen PML events, then audit ONLY Development with native fills."""

from pathlib import Path
import sys, json, hashlib
from decimal import Decimal as D, ROUND_CEILING
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.canonical import dumps
from engine.partial_execution import execute
from engine.strategy import Entry, Bar
from engine.legacy import reference as ref
from engine.research.levels import valid_bar, LevelEngine, SessionConfig
from engine.research.events import EventDetector
from engine.research.sequences import Sequences
from engine.research.structure import Structure, StructureConfig
from scripts.pml_feasibility.core import short_path, short_fill

P = ROOT / "work/pml-failed-break-execution-feasibility-v1"
M = ROOT / "work/mnq-individual-level-master-research"
S = ROOT / "storage/event_studies/78c96aa0e91147ba9913e365f33ed2f9"
NY = "America/New_York"


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write(name, rows):
    (rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)).to_csv(
        P / name, index=False, float_format="%.12g", lineterminator="\n"
    )


def prepare():
    P.mkdir(exist_ok=True)
    cfg = json.loads((S / "config.json").read_text())
    assert (cfg["start"], cfg["end"], cfg["segment"]) == (
        "2020-01-01",
        "2024-01-01",
        "development",
    )
    assert (cfg["session"]["premarket_start"], cfg["session"]["premarket_end"]) == (
        "00:00",
        "09:30",
    )
    hashes = {
        str(p.relative_to(ROOT)): sha(p)
        for p in [
            S / "config.json",
            S / "v2_events.parquet",
            M / "04_PML/outcomes_30.parquet",
            M / "all_levels_primary_outcomes.csv",
        ]
    }
    for v in cfg["dataset_identity"]["files"].values():
        path = ROOT / "outputs/data" / v["name"]
        assert sha(path) == v["sha256"]
        hashes[str(path.relative_to(ROOT))] = v["sha256"]
    protocol = dict(
        status="DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY",
        study_id=S.name,
        dataset=cfg["dataset_identity"],
        start="2020-01-01",
        end_exclusive="2024-01-01",
        session=cfg["session"],
        population="All causal PML BREAK_FAILED_NEXT_CANDLE_HOLD/DOWN events",
        evaluated_direction="SHORT / DOWN",
        entry="failure confirmed close, adverse slippage",
        stops={
            "A": "max(root.high,failure.high)+0.25",
            "B": "failure.high+0.25",
            "C": "root.high+0.25",
        },
        targets_r=[0.5, 1, 1.5],
        threshold_r=[0.5, 1, 1.25, 1.5, 2],
        threshold_atr=[0.5, 1, 1.5],
        horizons=[15, 30, 60],
        slippage_ticks_each_side=[0, 1, 2],
        primary_ticks=1,
        quantity=1,
        point_value=2,
        fees={
            "commission": 0.25,
            "exchange": 0.35,
            "clearing": 0.12,
            "NFA": 0.01,
            "per_side": 0.73,
            "round_trip": 1.46,
            "source": "user actual Webull",
        },
        ownership="minute starting confirmation, through actual XNYS close",
        missing="first missing owned minute -> EXECUTION_DATA_UNAVAILABLE, never a signal filter",
        at_close="retain event; NO_POST_ENTRY_SESSION_MINUTES, no synthetic trade",
        ordering="STOP before TARGET; adverse before favorable in same minute",
        path="stop-bounded to session close, inclusive exit-minute extrema are upper bounds",
        daily_limit="none; overlapping independent event diagnostics, not investable portfolio",
        recommendation="frozen qualitative user gates; no target selection or optimization",
    )
    (P / "frozen_execution_protocol.json").write_text(dumps(protocol))
    allrows = pq.read_table(
        S / "v2_events.parquet",
        filters=[
            ("level_type", "=", "PML"),
            ("date", ">=", "2020-01-01"),
            ("date", "<", "2024-01-01"),
        ],
    ).to_pandas()
    payload = pd.DataFrame([json.loads(x) for x in allrows.payload])
    raw = (
        payload[
            (payload.interaction_type == "BREAK_FAILED_NEXT_CANDLE_HOLD")
            & (payload.direction == "DOWN")
        ]
        .copy()
        .sort_values(["timestamp_utc", "event_id"])
        .reset_index(drop=True)
    )
    assert (
        len(raw) == 407
        and raw.date.nunique() == 286
        and raw.event_id.is_unique
        and raw.root_event_id.is_unique
    )
    measured = pd.read_parquet(M / "04_PML/outcomes_30.parquet")
    measured = measured[measured.event_id.isin(raw.event_id)]
    assert set(raw.event_id) == set(measured.event_id)
    good = measured[measured.complete].dropna(subset=["down_a1", "b_down_a1"])
    assert len(good) == 387 and good.date.nunique() == 274
    assert measured.censor_reason.value_counts().to_dict() == {"OUTSIDE_SESSION": 20}
    assert raw.atr14.notna().all() and (raw.atr14 > 0).all()
    primary = pd.read_csv(M / "all_levels_primary_outcomes.csv")
    row = primary[
        (primary.level == "PML")
        & (primary.interaction == "BREAK_FAILED_NEXT_CANDLE_HOLD")
        & (primary.stored_direction == "DOWN")
        & (primary.measured_direction == "DOWN")
    ].iloc[0]
    dates = good.groupby("date")[["down_a1", "b_down_a1"]].mean()
    delta = (dates.down_a1 - dates.b_down_a1).to_numpy(dtype=float)
    draws = delta[
        np.random.default_rng(1729).integers(0, len(delta), size=(2000, len(delta)))
    ].mean(axis=1)
    values = dict(
        event_probability=dates.down_a1.mean(),
        baseline_probability=dates.b_down_a1.mean(),
        effect=delta.mean(),
        ci_low=np.quantile(draws, 0.025),
        ci_high=np.quantile(draws, 0.975),
        p_value=(1 + sum(abs(draws - delta.mean()) >= abs(delta.mean()))) / 2001,
    )
    for k, v in values.items():
        assert abs(v - row[k]) < 5e-10, (k, v, row[k])
    ps = primary.p_for_correction.to_numpy()
    order = np.argsort(ps)
    q = np.empty(len(ps))
    q[order] = np.minimum.accumulate(
        (ps[order] * len(ps) / np.arange(1, len(ps) + 1))[::-1]
    )[::-1].clip(0, 1)
    assert abs(q[row.name] - row.bh_q_value) < 5e-10
    values.update(
        raw_events=407,
        raw_dates=286,
        measurement_events=387,
        measurement_dates=274,
        bh_q_value=float(row.bh_q_value),
        full_family_hypotheses=len(primary),
    )
    (P / "registered_finding_reproduction.json").write_text(dumps(values))
    rec = measured[["event_id", "date", "complete", "censor_reason", "atr14"]].copy()
    rec["raw_execution_eligible"] = True
    rec["measurement_reference"] = rec.complete & rec.atr14.notna()
    write("measurement_population_reconciliation.csv", rec)
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
    assert bars.timestamp_utc.min() >= start and bars.timestamp_utc.max() < end
    bytime = {b.timestamp_utc: b for b in bars.itertuples(index=False)}
    bars["ny_date"] = bars.timestamp_utc.dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
    groups = dict(tuple(bars.groupby("ny_date")))
    quality = []
    pm = {}
    for date, session in sorted(cfg["calendar"]["sessions"].items()):
        if not "2020-01-01" <= date < "2024-01-01":
            continue
        a = pd.Timestamp(date, tz=NY).tz_convert("UTC")
        z = pd.Timestamp(date + " 09:30", tz=NY).tz_convert("UTC")
        expected = pd.date_range(a, z, freq="5min", inclusive="left")
        actual = groups.get(date, bars.iloc[:0])
        actual = actual[(actual.timestamp_utc >= a) & (actual.timestamp_utc < z)]
        valid = actual[[valid_bar(b) for b in actual.itertuples(index=False)]]
        ok = valid.timestamp_utc.tolist() == expected.tolist()
        low = min(valid.low) if ok else None
        pm[date] = (ok, low, z)
        quality.append(
            dict(
                date=date,
                expected_bars=len(expected),
                observed_bars=len(actual),
                valid_complete_bars=len(valid),
                complete_pm=ok,
                pml=low,
                available_at=z if ok else None,
                causal_events=int(raw.date.eq(date).sum()),
                stale_fallback=False,
            )
        )
    write("pml_data_quality_audit.csv", quality)
    roots = payload.set_index("event_id")
    audits = []
    root_high = []
    for r in raw.itertuples():
        root = roots.loc[r.root_event_id]
        at = pd.Timestamp(r.timestamp_utc)
        bs = pd.Timestamp(r.bar_start_utc)
        rs = pd.Timestamp(root.bar_start_utc)
        b = bytime[rs]
        f = bytime[bs]
        ok, low, available = pm[r.date]
        assert (
            ok
            and D(str(r.level_price)) == low
            and pd.Timestamp(r.level_available_at) == available
        )
        assert (
            root.interaction_type == "BREAK_ACCEPTANCE"
            and root.approach_side == "ABOVE"
            and root.direction == "DOWN"
        )
        assert (
            valid_bar(b)
            and valid_bar(f)
            and bs == rs + pd.Timedelta(minutes=5)
            and at == bs + pd.Timedelta(minutes=5)
        )
        assert (
            b.close < D(r.level_price) < f.close and root.touch_number == r.touch_number
        )
        assert (
            pd.Timestamp(root.timestamp_utc) == bs
            and pd.Timestamp(r.break_confirmation_timestamp) == bs
        )
        assert available <= rs and r.level_source_date == r.date
        for key in ["open", "high", "low", "close"]:
            assert D(str(getattr(r, key))) == getattr(f, key) and D(
                str(root[key])
            ) == getattr(b, key)
        # Independently check origin: adjacent valid RTH prior close, otherwise bar open.
        previous = bytime.get(rs - pd.Timedelta(minutes=5))
        session_open = pd.Timestamp(cfg["calendar"]["sessions"][r.date][0])
        origin = (
            previous.close
            if previous is not None
            and valid_bar(previous)
            and previous.timestamp_utc >= session_open
            else b.open
        )
        assert origin > D(r.level_price)
        root_high.append(b.high)
        audits.append(
            dict(
                event_id=r.event_id,
                root_event_id=r.root_event_id,
                date=r.date,
                root_start=rs,
                failure_start=bs,
                confirmation=at,
                availability=available,
                root_touch_number=root.touch_number,
                compound_touch_number=r.touch_number,
                root_high=b.high,
                root_close=b.close,
                failure_close=f.close,
                origin=origin,
                pml=low,
                adjacent_complete=True,
                pm_complete=True,
                no_future_confirmation=True,
            )
        )
    write("event_semantics_audit.csv", audits)
    for col in ["open", "high", "low", "close", "level_price"]:
        raw[col] = raw[col].map(D)
    raw["measurement_complete_30m"] = raw.event_id.map(
        measured.set_index("event_id").complete
    )
    raw["measurement_down_1atr_30m"] = raw.event_id.map(
        measured.set_index("event_id").down_a1
    )
    raw["root_high"] = root_high
    raw["touch_group"] = raw.touch_number.map(lambda x: str(x) if x < 3 else "3+")
    raw["year"] = raw.date.str[:4].astype(int)
    # Causal structure replay provides BOS/CHoCH history omitted from saved event payload.
    structure = Structure(
        StructureConfig(**cfg["research_settings"]["structure"]), "5m"
    )
    last = None
    last_event = "NONE"
    context = {}
    wanted = set(pd.to_datetime(raw.bar_start_utc))
    sessions = {
        d: tuple(map(pd.Timestamp, v))
        for d, v in cfg["calendar"]["sessions"].items()
        if "2020-01-01" <= d < "2024-01-01"
    }
    levels = LevelEngine(SessionConfig(**cfg["session"]), sessions)
    detector = EventDetector(levels.config)
    sequences = Sequences()
    replayed = []
    for b in bars.itertuples(index=False):
        at = b.timestamp_utc
        contiguous = last is not None and at - last == pd.Timedelta(minutes=5)
        last = at
        levels.update(b)
        events = detector.update(
            b,
            [l for l in levels.levels if l.level_type == "PML"],
            sessions.get(b.ny_date),
        )
        for e in sequences.update(b, events):
            if (
                e["interaction_type"] == "BREAK_FAILED_NEXT_CANDLE_HOLD"
                and e["direction"] == "DOWN"
                and b.ny_date in sessions
                and sessions[b.ny_date][0] <= at < sessions[b.ny_date][1]
            ):
                replayed.append(e)
        if not valid_bar(b):
            structure.window.clear()
            continue
        ev = structure.update(
            Bar(at, b.open, b.high, b.low, b.close, int(b.volume)),
            at + pd.Timedelta(minutes=5),
            None,
            contiguous,
        )
        breaks = [e for e in ev if not e["event_type"].startswith("SWING_")]
        if breaks:
            last_event = breaks[-1]["event_type"]
        if at in wanted:
            context[at] = (
                last_event,
                "|".join(x["event_type"] for x in breaks) or "NONE",
            )
    print(
        "Independent causal replay", len(replayed), "exact frozen event IDs", flush=True
    )
    assert set(e["event_id"] for e in replayed) == set(raw.event_id) and len(
        replayed
    ) == len(raw)
    replay_map = {e["event_id"]: e for e in replayed}
    for r in raw.itertuples():
        assert replay_map[r.event_id]["touch_number"] == r.touch_number
    raw["latest_structure_break"] = raw.bar_start_utc.map(
        lambda x: context[pd.Timestamp(x)][0]
    )
    raw["confirmation_structure_break"] = raw.bar_start_utc.map(
        lambda x: context[pd.Timestamp(x)][1]
    )
    # Recompute distance from confirmation close to nearest currently known lower level.
    raw["room_below_confirmation_atr"] = [
        min(
            [
                float(r.close) - float(x["price"])
                for x in r.chart_context["levels"]
                if float(x["price"]) < float(r.close)
                and pd.Timestamp(x["available_at"]) <= pd.Timestamp(r.timestamp_utc)
            ],
            default=np.nan,
        )
        / r.atr14
        for r in raw.itertuples()
    ]
    raw["open_minus_pml_atr"] = (
        raw.rth_open.astype(float) - raw.level_price.astype(float)
    ) / raw.atr14
    export = raw.drop(
        columns=[
            c for c in raw if raw[c].map(lambda x: isinstance(x, (list, dict))).any()
        ]
    )
    write("exact_raw_events.csv", export)
    minutes = pq.read_table(
        ROOT / "outputs/data" / cfg["dataset_identity"]["files"]["minutes"]["name"],
        filters=[("ts_event", ">=", start), ("ts_event", "<", end)],
    ).to_pandas()
    if "ts_event" not in minutes:
        minutes = minutes.reset_index()
    assert (
        minutes.ts_event.min() >= start
        and minutes.ts_event.max() < end
        and minutes.ts_event.is_unique
    )
    for col in ["open", "high", "low", "close"]:
        minutes[col] = minutes[col].map(lambda x: D(int(x)).scaleb(-9))
    minutes["date"] = minutes.ts_event.dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
    days = {
        k: v.set_index("ts_event").sort_index()
        for k, v in minutes.groupby("date")
        if k in set(raw.date)
    }
    print(
        "Reconciled 407/286 raw; 387/274 measurement; 20 session censored; 0 missing/ATR unavailable",
        flush=True,
    )
    return raw, days, cfg, hashes


def run():
    raw, days, cfg, hashes = prepare()
    paths = []
    targets = []
    checks = 0
    for ix, r in enumerate(raw.itertuples()):
        at = pd.Timestamp(r.timestamp_utc)
        end = pd.Timestamp(r.session_close)
        expected = int((end - at).total_seconds() / 60)
        assert expected >= 0
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
        assert bool(r.measurement_complete_30m) == (
            expected >= 30 and len(prefix) >= 30
        )
        if r.measurement_complete_30m:
            assert bool(r.measurement_down_1atr_30m) == (
                float(r.close) - arr[:30, 2].min() >= atr
            )
        shared = {
            k: getattr(r, k)
            for k in [
                "event_id",
                "root_event_id",
                "date",
                "year",
                "touch_group",
                "structure_state",
                "atr_regime",
                "latest_structure_break",
                "confirmation_structure_break",
                "open_minus_pml_atr",
                "room_below_confirmation_atr",
            ]
        }
        for ticks in [0, 1, 2]:
            entry = ref.tick(r.close) - D(".25") * ticks
            for name, value in [
                ("A", max(r.root_high, r.high)),
                ("B", r.high),
                ("C", r.root_high),
            ]:
                stop = ref.tick(value + D(".25"), ROUND_CEILING)
                risk = stop - entry
                assert stop % D(".25") == 0 and entry % D(".25") == 0
                base = dict(
                    **shared,
                    ticks=ticks,
                    stop=name,
                    entry_time_utc=at,
                    entry_price=entry,
                    stop_price=stop,
                    risk_points=risk,
                    risk_usd=risk * 2,
                    risk_atr=float(risk) / atr if atr else None,
                    atr14=atr,
                    expected_session_minutes=expected,
                    first_missing_minute=gap,
                    signal_candle_crossed_future_stop=r.high >= stop
                )
                status = (
                    "NON_POSITIVE_RISK"
                    if risk <= 0
                    else "NO_POST_ENTRY_SESSION_MINUTES" if expected == 0 else "VALID"
                )
                if status != "VALID":
                    paths.append(dict(**base, eligibility_status=status))
                    targets.extend(
                        dict(**base, target_r=t, execution_status=status)
                        for t in [0.5, 1, 1.5]
                    )
                    continue
                path = short_path(
                    arr, float(entry), float(stop), float(risk), atr, expected, gap
                )
                paths.append(dict(**base, eligibility_status=status, **path))
                for t in [0.5, 1, 1.5]:
                    tp = ref.tick(entry - risk * D(str(t)))
                    signal = dict(
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
                            signal,
                            day,
                            ref.Config(D(".73"), ticks),
                            1,
                            Entry("SHORT", stop, D(str(t))),
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
                        targets.append(
                            dict(
                                **base,
                                target_r=t,
                                target_price=tp,
                                execution_status="EXECUTION_DATA_UNAVAILABLE"
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
                    assert trade["mfe_points"] == max(
                        D(0), entry - D(str(arr[: minute + 1, 2].min()))
                    )
                    assert trade["mae_points"] == max(
                        D(0), D(str(arr[: minute + 1, 1].max())) - entry
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
                        dict(
                            **base,
                            target_r=t,
                            target_price=tp,
                            execution_status="COMPLETED",
                            adverse_stop_gap=reason == "STOP"
                            and arr[minute, 0] > float(stop),
                            **{k: trade[k] for k in keys}
                        )
                    )
                    checks += 1
        if ix % 100 == 0:
            print("Events", ix, "native independent checks", checks, flush=True)
    write("all_event_paths.csv", paths)
    write("all_target_executions.csv", targets)
    for name, h in hashes.items():
        assert sha(ROOT / name) == h
    (P / "execution_verification.json").write_text(
        dumps(
            dict(
                raw_events=len(raw),
                raw_dates=raw.date.nunique(),
                native_independent_checks=checks,
                source_hashes_verified=hashes,
                reserved_outcomes_read=False,
            )
        )
    )
    print("Completed", len(paths), len(targets), checks, flush=True)


if __name__ == "__main__":
    run()
