"""Development-only, columnar individual-level research. No strategy execution."""

import sys, json, time, hashlib, itertools
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
import numpy as np, pandas as pd, duckdb
from engine.research.statistics import clustered, benjamini_hochberg

R = (
    Path(__file__).resolve().parents[2]
    / "work"
    / "mnq-individual-level-master-research"
)
OLD = "5cb7fab0d4e7414792a3fbe59ded4999"
LEVELS = [
    "PDH",
    "PDL",
    "PMH",
    "PML",
    "O5H",
    "O5L",
    "5m_SWING_HIGH",
    "5m_SWING_LOW",
    "4h_SWING_HIGH",
    "4h_SWING_LOW",
    "SUPPLY",
    "DEMAND",
]
DIRS = [
    "01_PDH",
    "02_PDL",
    "03_PMH",
    "04_PML",
    "05_O5H",
    "06_O5L",
    "07_5M_SWING_HIGH",
    "08_5M_SWING_LOW",
    "09_4H_RESISTANCE",
    "10_4H_SUPPORT",
    "11_SUPPLY_ZONES",
    "12_DEMAND_ZONES",
]
ATR = [0.25, 0.5, 0.75, 1, 1.5, 2, 3]
H = ["5", "10", "15", "30", "60", "session_close"]
KEY = ["year", "time_bucket", "volatility_bucket"]
K = json.loads((R / "preregistered_protocol.json").read_text())["interactions"]
K = [x.replace("BREAK_FAILED_HOLD", "BREAK_FAILED_NEXT_CANDLE_HOLD") for x in K]
REV = {
    "REJECTION",
    "SWEEP_RECLAIM",
    "BREAK_FAILED_NEXT_CANDLE_HOLD",
    "BREAK_RETEST_FAIL",
}


def folder(level):
    return R / DIRS[LEVELS.index(level)]


def write(df, p):
    df.to_csv(p, index=False, float_format="%.10g", lineterminator="\n")


def connection(id):
    root = Path("storage/event_studies") / id
    c = json.loads((root / "config.json").read_text())
    assert (c["segment"], c["start"], c["end"]) == (
        "development",
        "2020-01-01",
        "2024-01-01",
    )
    con = duckdb.connect()
    con.execute(
        "set threads=1;set memory_limit='2GB';set preserve_insertion_order=false"
    )
    for n in ["events", "observations", "outcomes"]:
        con.read_parquet(str(root / f"v2_{n}.parquet")).create_view(n)
    return con, c


def project_outcome():
    a = [
        "o.complete",
        "o.censor_reason",
        "o.forward_close_change",
        "o.maximum_high_excursion",
        "o.maximum_low_excursion",
    ]
    for side in ["up", "down"]:
        for t in ATR:
            key = f"{side}_{t:g}"
            a += [
                f"cast(json_extract(o.payload,'$.atr_thresholds.\"{key}\".reached') as double) as {side}_a{str(t).replace('.','p')}",
                f"cast(json_extract(o.payload,'$.atr_thresholds.\"{key}\".minutes') as double) as {side}_t{str(t).replace('.','p')}",
            ]
        for t in [10, 25, 50, 75, 100]:
            a += [
                f"o.{side}_{t}",
                f"cast(json_extract(o.payload,'$.thresholds.{side}_{t}.minutes') as double) as {side}_p{t}_minutes",
            ]
    return ",".join(a)


def clustered_many(g, cols):
    # Equivalent to engine.research.statistics.clustered, vectorized over thresholds.
    out = {}
    good = g.dropna(subset=cols + ["b_" + c for c in cols])
    if good.empty:
        return {
            c: dict(
                events=0,
                unique_dates=0,
                event_probability=np.nan,
                baseline_probability=np.nan,
                effect=np.nan,
                ci_low=np.nan,
                ci_high=np.nan,
                p_value=np.nan,
            )
            for c in cols
        }
    d = good.groupby("date", sort=True)[cols + ["b_" + c for c in cols]].mean()
    n = len(d)
    y = d[cols].to_numpy()
    b = d[["b_" + c for c in cols]].to_numpy()
    delta = y - b
    effect = delta.mean(0)
    ix = np.random.default_rng(1729).integers(0, n, size=(2000, n))
    draws = np.empty((2000, len(cols)))
    for j in range(len(cols)):
        draws[:, j] = delta[ix, j].mean(1)
    for j, c in enumerate(cols):
        ci = np.quantile(draws[:, j], [0.025, 0.975]) if n >= 2 else [np.nan, np.nan]
        p = (
            (1 + np.sum(abs(draws[:, j] - effect[j]) >= abs(effect[j]))) / 2001
            if n >= 2
            else np.nan
        )
        out[c] = dict(
            events=len(good),
            unique_dates=n,
            event_probability=y[:, j].mean(),
            baseline_probability=b[:, j].mean(),
            effect=effect[j],
            relative_effect=effect[j] / b[:, j].mean() if b[:, j].mean() else np.nan,
            ci_low=ci[0],
            ci_high=ci[1],
            p_value=p,
        )
    return out


def describe(g, side):
    other = "down" if side == "up" else "up"
    up = side == "up"
    v = g[g.complete].copy()
    atr = v.atr14.replace(0, np.nan)
    mf = v.maximum_high_excursion if up else v.maximum_low_excursion
    ma = v.maximum_low_excursion if up else v.maximum_high_excursion
    return dict(
        total_events=len(g),
        root_observations=g.observation_id.nunique(),
        total_dates=g.date.nunique(),
        complete=int(g.complete.sum()),
        censored=int((~g.complete).sum()),
        atr_available=int((v.atr14 > 0).sum()),
        mean_forward_points=(v.forward_close_change * (1 if up else -1)).mean(),
        median_forward_points=(v.forward_close_change * (1 if up else -1)).median(),
        mean_mfe=mf.mean(),
        median_mfe=mf.median(),
        mean_mae=ma.mean(),
        median_mae=ma.median(),
        mean_mfe_atr=(mf / atr).mean(),
        median_mfe_atr=(mf / atr).median(),
        mean_mae_atr=(ma / atr).mean(),
        median_mae_atr=(ma / atr).median(),
        median_minutes_to_favorable_1atr=v[side + "_t1"].median(),
        median_minutes_to_adverse_1atr=v[other + "_t1"].median(),
    )


def process(level, id):
    out = folder(level)
    out.mkdir(exist_ok=True)
    con, cfg = connection(id)
    print("begin", level, flush=True)
    ev = con.execute(
        "select * from events where level_type=? order by timestamp_utc,event_id",
        [level],
    ).df()
    assert ev.event_id.is_unique
    assert ev.date.between("2020-01-01", "2023-12-31").all()
    payload = [json.loads(x) for x in ev.payload]
    for k in [
        "observation_id",
        "level_id",
        "level_price",
        "level_available_at",
        "bar_start_utc",
        "level_source_date",
    ]:
        ev[k] = [p.get(k) for p in payload]
    ev["root_event_id"] = [p.get("root_event_id", p["event_id"]) for p in payload]
    ev["time_window"] = pd.cut(
        ev.minutes_since_rth_open,
        [-0.001, 60, 150, 270, 400],
        right=False,
        labels=["09:30–10:29", "10:30–11:59", "12:00–13:59", "14:00–close"],
    ).astype(str)
    ev["touch_group"] = (
        pd.to_numeric(ev.touch_number, errors="coerce")
        .clip(upper=4)
        .fillna(0)
        .astype(int)
        .astype(str)
        .replace({"4": "4+"})
    )
    ev["efficiency_group"] = pd.cut(
        ev.directional_efficiency,
        [-np.inf, 0.25, 0.5, np.inf],
        right=False,
        labels=["<0.25", "0.25–0.50", ">=0.50"],
    ).astype(str)
    ev["vwap_side"] = np.where(
        ev.vwap.isna(),
        "UNAVAILABLE",
        np.where(
            ev.price_at_event > ev.vwap,
            "ABOVE",
            np.where(ev.price_at_event < ev.vwap, "BELOW", "AT"),
        ),
    )
    for col, edges in [
        ("prior_day_range_atr", [-np.inf, 5, 10, np.inf]),
        ("opening_range_atr", [-np.inf, 1, 2, np.inf]),
    ]:
        ev[col + "_group"] = pd.cut(ev[col], edges, right=False).astype(str)
    ev["logical_direction"] = np.where(
        ev.interaction_type.isin(REV),
        ev.direction.map({"UP": "DOWN", "DOWN": "UP"}),
        ev.direction,
    )
    # Formation and availability are metadata, not future-derived outcomes.
    ev["level_age_minutes"] = (
        pd.to_datetime(ev.timestamp_utc, utc=True)
        - pd.to_datetime(ev.level_available_at, utc=True)
    ).dt.total_seconds() / 60
    ev["level_age_group"] = pd.cut(
        ev.level_age_minutes, [-np.inf, 30, 120, 390, np.inf], right=False
    ).astype(str)
    ev.to_parquet(out / "events.parquet", index=False)
    (out / "configuration.json").write_text(
        json.dumps(
            {
                "study_id": id,
                "logical_level_filter": level,
                "source_config": cfg,
                "numeric_filters": {},
                "saved_buckets": {},
                "protocol_sha256": (R / "protocol_sha256.txt").read_text().strip(),
            },
            indent=2,
        )
    )
    counts = (
        ev.groupby(["interaction_type", "direction"], dropna=False)
        .agg(
            events=("event_id", "size"),
            root_observations=("observation_id", "nunique"),
            unique_dates=("date", "nunique"),
        )
        .reset_index()
    )
    counts.insert(0, "level", level)
    write(counts, out / "interaction_counts.csv")
    overlap = (
        ev.groupby(["observation_id", "date"])
        .agg(
            classes=("interaction_type", lambda s: ";".join(sorted(set(s)))),
            event_records=("event_id", "size"),
        )
        .reset_index()
    )
    overlap.insert(0, "level", level)
    write(overlap, out / "overlap_audit.csv")
    import pyarrow as pa

    con.register(
        "selected",
        pa.Table.from_pandas(ev.drop(columns="payload"), preserve_index=False),
    )
    rows = []
    contexts = []
    pointrows = []
    quality = []
    for horizon in H:
        e = con.execute(
            f"select e.*, {project_outcome()} from selected e join outcomes o using(event_id) where o.kind='event' and o.horizon=? order by e.event_id",
            [horizon],
        ).df()
        assert len(e) == len(ev)
        for col in [
            f'{side}_a{str(t).replace(".","p")}' for side in ["up", "down"] for t in ATR
        ]:
            assert e.loc[e.complete & (e.atr14 > 0), col].notna().all(), col
        b = con.execute(
            f"select b.year,b.time_bucket,b.volatility_bucket,b.date,b.atr14,{project_outcome()} from observations b join outcomes o using(event_id) where o.kind='baseline' and o.horizon=?",
            [horizon],
        ).df()
        if b.empty:  # Some versions use 'observation' kind.
            b = con.execute(
                f"select b.year,b.time_bucket,b.volatility_bucket,b.date,b.atr14,{project_outcome()} from observations b join outcomes o using(event_id) where o.horizon=?",
                [horizon],
            ).df()
        acols = [f'{s}_a{str(t).replace(".","p")}' for s in ["up", "down"] for t in ATR]
        # Preserve censored labels; they cannot enter probabilities as failures.
        bc = (
            b[b.complete & (b.atr14 > 0)]
            .groupby(KEY)[acols]
            .mean()
            .add_prefix("b_")
            .reset_index()
        )
        e = e.merge(bc, on=KEY, how="left", validate="many_to_one")
        e.to_parquet(out / f"outcomes_{horizon}.parquet", index=False)
        quality.append(
            dict(
                level=level,
                study_id=id,
                horizon=horizon,
                events=len(e),
                dates=e.date.nunique(),
                complete=int(e.complete.sum()),
                censored=int((~e.complete).sum()),
                missing_atr=int((e.complete & ~(e.atr14 > 0)).sum()),
                unmatched=int((e.complete & (e.atr14 > 0) & e.b_up_a1.isna()).sum()),
                censor_reasons=json.dumps(
                    e.censor_reason.value_counts().to_dict(), sort_keys=True
                ),
            )
        )
        for (kind, direction), g in e.groupby(["interaction_type", "direction"]):
            z = g[g.complete & (g.atr14 > 0)]
            stats = clustered_many(z, acols)
            for side in ["up", "down"]:
                desc = describe(g, side)
                other = "down" if side == "up" else "up"
                for t in ATR:
                    col = f'{side}_a{str(t).replace(".","p")}'
                    opp = f'{other}_a{str(t).replace(".","p")}'
                    rows.append(
                        dict(
                            level=level,
                            study_id=id,
                            interaction=kind,
                            stored_direction=direction,
                            measured_direction=side.upper(),
                            logical_direction=g.logical_direction.iloc[0],
                            horizon=horizon,
                            atr_target=t,
                            **desc,
                            **stats[col],
                            adverse_probability=stats[opp]["event_probability"],
                            baseline_adverse_probability=stats[opp][
                                "baseline_probability"
                            ],
                            adverse_effect=stats[opp]["effect"],
                            median_minutes_to_hit=z[
                                f'{side}_t{str(t).replace(".","p")}'
                            ].median(),
                        )
                    )
                for t in [10, 25, 50, 75, 100]:
                    cc = g[g.complete]
                    prob = cc.groupby("date")[f"{side}_{t}"].mean().mean()
                    ap = cc.groupby("date")[f"{other}_{t}"].mean().mean()
                    pointrows.append(
                        dict(
                            level=level,
                            interaction=kind,
                            stored_direction=direction,
                            measured_direction=side.upper(),
                            horizon=horizon,
                            points=t,
                            total_events=len(g),
                            complete=len(cc),
                            event_probability=prob,
                            adverse_probability=ap,
                            median_minutes_to_hit=cc[f"{side}_p{t}_minutes"].median(),
                        )
                    )
        if horizon == "30":
            for dim in [
                "year",
                "time_window",
                "touch_group",
                "atr_regime",
                "volatility_bucket",
                "ema_alignment",
                "vwap_side",
                "structure_state",
                "efficiency_group",
                "prior_day_range_atr_group",
                "opening_range_atr_group",
                "level_age_group",
            ]:
                for (kind, direction, value), g in e.groupby(
                    ["interaction_type", "direction", dim], dropna=False
                ):
                    z = g[g.complete & (g.atr14 > 0)]
                    stats = clustered_many(z, ["up_a1", "down_a1"])
                    for side in ["up", "down"]:
                        contexts.append(
                            dict(
                                level=level,
                                study_id=id,
                                interaction=kind,
                                stored_direction=direction,
                                measured_direction=side.upper(),
                                logical_direction=g.logical_direction.iloc[0],
                                dimension=dim,
                                value=value,
                                horizon="30",
                                atr_target=1,
                                **describe(g, side),
                                **stats[side + "_a1"],
                                adverse_probability=stats[
                                    ("down" if side == "up" else "up") + "_a1"
                                ]["event_probability"],
                            )
                        )
        print(level, horizon, "complete", flush=True)
    write(pd.DataFrame(rows), out / "atr_outcomes.csv")
    write(pd.DataFrame(contexts), out / "context_comparisons.csv")
    write(pd.DataFrame(pointrows), out / "fixed_point_outcomes.csv")
    write(pd.DataFrame(quality), out / "data_quality.csv")
    con.close()
    (out / "statistics_v2_verified.txt").write_text(
        "Quoted decimal ATR JSON keys; full-grid completeness checked.\n"
    )


if __name__ == "__main__":
    start = time.monotonic()
    pm = json.loads((R / "premarket_study.json").read_text())["id"]
    from backend.app.event_studies import gate

    for level in LEVELS[:10]:
        id = pm if level in ["PMH", "PML"] else OLD
        if folder(level).joinpath("statistics_v2_verified.txt").exists():
            continue
        assert gate(id, outcomes=True)["status"] == "completed"
        process(level, id)
    (R / "analysis_runtime.json").write_text(
        json.dumps({"runtime_seconds": time.monotonic() - start})
    )
