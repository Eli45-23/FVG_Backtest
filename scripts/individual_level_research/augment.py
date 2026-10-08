"""Secondary descriptive supplements; same unfiltered events and complete outcomes."""

import json, time
import pandas as pd, numpy as np
from analyze import R, LEVELS, folder, connection, KEY, write, clustered_many, OLD
from engine.research.study2 import source
from engine.timeframes import aggregate, FrameConfig
from engine.research.study import read_bars

C = json.loads(open(f"storage/event_studies/{OLD}/config.json").read())
catalog = pd.read_parquet(R / "swing_catalog.parquet").set_index("id")
revisits = pd.read_parquet(R / "level_revisits.parquet")
allrows = []
sensitivity = []
broken = []
swchecks = []
frames = {
    "5m": read_bars(C),
    "4h": aggregate(
        source(C, True), "4h", FrameConfig(**C["research_settings"]["frame"])
    ),
}
for tf, frame in frames.items():
    frame = frame.set_index("timestamp_utc")
    frame.to_parquet(R / f"audit_source_{tf}.parquet")
    for sid, s in catalog[catalog.observed_timeframe == tf].iterrows():
        at = pd.Timestamp(s.formation_timestamp)
        delta = pd.Timedelta(minutes=5 if tf == "5m" else 240)
        idx = pd.date_range(at - 2 * delta, at + 2 * delta, freq=delta)
        g = frame.reindex(idx)
        expected = float(frame.loc[at, "high" if s.swing_type == "HIGH" else "low"])
        other = g.drop(index=at)
        ok = (
            len(g) == 5
            and g.is_complete_5m.fillna(False).all()
            and (expected > other.high.astype(float)).all()
            if s.swing_type == "HIGH"
            else len(g) == 5
            and g.is_complete_5m.fillna(False).all()
            and (expected < other.low.astype(float)).all()
        )
        ok = bool(
            ok
            and expected == float(s.price)
            and pd.Timestamp(s.availability_timestamp) == at + 3 * delta
        )
        swchecks.append(dict(id=sid, timeframe=tf, correct=ok))
write(pd.DataFrame(swchecks), R / "independent_swing_confirmation_audit.csv")
con, _ = connection(OLD)
baseline = {}
for h in ["5", "10", "15", "30", "60", "session_close"]:
    b = con.execute(
        "select b.year,b.time_bucket,b.volatility_bucket,b.date,b.atr14,o.forward_close_change,o.maximum_high_excursion,o.maximum_low_excursion from observations b join outcomes o using(event_id) where o.horizon=? and o.complete and b.atr14>0",
        [h],
    ).df()
    for col in [
        "forward_close_change",
        "maximum_high_excursion",
        "maximum_low_excursion",
    ]:
        b[col + "_atr"] = b[col] / b.atr14
    b["up_a1"] = (b.maximum_high_excursion >= b.atr14).astype(float)
    b["down_a1"] = (b.maximum_low_excursion >= b.atr14).astype(float)
    metric = [
        "forward_close_change",
        "maximum_high_excursion",
        "maximum_low_excursion",
        "forward_close_change_atr",
        "maximum_high_excursion_atr",
        "maximum_low_excursion_atr",
    ]
    baseline[h] = (
        b.groupby(KEY)[metric].mean().add_prefix("b_").reset_index(),
        b.groupby(KEY + ["date"])[["up_a1", "down_a1"]]
        .mean()
        .add_prefix("daily_")
        .reset_index(),
    )
for level in LEVELS[:10]:
    while not (folder(level) / "statistics_v2_verified.txt").exists():
        time.sleep(5)
    for h in baseline:
        e = pd.read_parquet(folder(level) / f"outcomes_{h}.parquet")
        g = (
            e[e.complete & (e.atr14 > 0)]
            .merge(baseline[h][0], on=KEY, validate="many_to_one")
            .merge(
                revisits[revisits.level == level].drop(columns="level"),
                on="event_id",
                validate="one_to_one",
            )
        )
        horizon_minutes = (
            (
                pd.to_datetime(g.session_close, utc=True)
                - pd.to_datetime(g.timestamp_utc, utc=True)
            ).dt.total_seconds()
            / 60
            if h == "session_close"
            else float(h)
        )
        g["revisited"] = (
            g.first_post_confirmation_level_revisit_minutes <= horizon_minutes
        ).astype(float)
        for (kind, direction), v in g.groupby(["interaction_type", "direction"]):
            for side in ["UP", "DOWN"]:
                sign = 1 if side == "UP" else -1
                mf = "maximum_high_excursion" if sign == 1 else "maximum_low_excursion"
                ma = "maximum_low_excursion" if sign == 1 else "maximum_high_excursion"
                day = v.groupby("date")[
                    [
                        mf,
                        ma,
                        "b_" + mf,
                        "b_" + ma,
                        "forward_close_change",
                        "b_forward_close_change",
                        "revisited",
                    ]
                ].mean()
                allrows.append(
                    dict(
                        level=level,
                        interaction=kind,
                        stored_direction=direction,
                        measured_direction=side,
                        horizon=h,
                        complete=len(v),
                        dates=v.date.nunique(),
                        event_mean_favorable=day[mf].mean(),
                        baseline_mean_favorable=day["b_" + mf].mean(),
                        event_mean_adverse=day[ma].mean(),
                        baseline_mean_adverse=day["b_" + ma].mean(),
                        event_mean_directional_close=sign
                        * day.forward_close_change.mean(),
                        baseline_mean_directional_close=sign
                        * day.b_forward_close_change.mean(),
                        revisit_probability=day.revisited.mean(),
                        median_minutes_to_revisit=v.loc[
                            v.revisited == 1,
                            "first_post_confirmation_level_revisit_minutes",
                        ].median(),
                    )
                )
        if h == "30":
            # Exploratory robustness check includes same-date controls so baseline-date variability is paired.
            z = g.merge(
                baseline[h][1], on=KEY + ["date"], how="left", validate="many_to_one"
            )
            z["b_up_a1"] = z.daily_up_a1
            z["b_down_a1"] = z.daily_down_a1
            for (kind, direction), v in z.groupby(["interaction_type", "direction"]):
                stats = clustered_many(v, ["up_a1", "down_a1"])
                for side in ["UP", "DOWN"]:
                    sensitivity.append(
                        dict(
                            level=level,
                            interaction=kind,
                            stored_direction=direction,
                            measured_direction=side,
                            **stats[side.lower() + "_a1"],
                        )
                    )
            if "SWING" in level:
                z["previously_broken"] = [
                    bool(
                        pd.notna(catalog.loc[sid, "first_broken_at"])
                        and pd.Timestamp(catalog.loc[sid, "first_broken_at"])
                        <= pd.Timestamp(bs)
                    )
                    for sid, bs in zip(z.level_id, z.bar_start_utc)
                ]
                for (kind, direction, state), v in z.groupby(
                    ["interaction_type", "direction", "previously_broken"]
                ):
                    stats = clustered_many(v, ["up_a1", "down_a1"])
                    for side in ["UP", "DOWN"]:
                        broken.append(
                            dict(
                                level=level,
                                interaction=kind,
                                stored_direction=direction,
                                measured_direction=side,
                                previously_broken=state,
                                **stats[side.lower() + "_a1"],
                            )
                        )
    print(level, "supplemented", flush=True)
write(pd.DataFrame(allrows), R / "all_levels_excursion_baselines_and_revisits.csv")
write(pd.DataFrame(sensitivity), R / "same_date_baseline_sensitivity.csv")
write(pd.DataFrame(broken), R / "swing_previously_broken_exploratory.csv")
for l in LEVELS[:10]:
    write(
        pd.DataFrame(allrows).query("level==@l"),
        folder(l) / "excursion_baselines_and_revisits.csv",
    )
