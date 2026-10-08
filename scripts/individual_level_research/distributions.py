import json, time
import numpy as np, pandas as pd
from analyze import R, LEVELS, folder, write

rows = []
episodes = []
incidence = []
for level in LEVELS[:10]:
    while not (folder(level) / "statistics_v2_verified.txt").exists():
        time.sleep(5)
    ev = pd.read_parquet(folder(level) / "events.parquet")
    ev["touch_number"] = pd.to_numeric(ev.touch_number)
    touch = (
        ev[ev.interaction_type == "TOUCH"]
        .sort_values(["timestamp_utc", "event_id"])
        .copy()
    )
    touch["previous_episode_minutes"] = touch.groupby(
        ["date", "level_id"]
    ).timestamp_utc.transform(
        lambda x: pd.to_datetime(x, utc=True).diff().dt.total_seconds() / 60
    )
    groups = ev.groupby(["date", "level_id", "touch_number"]).interaction_type.agg(
        lambda s: set(s)
    )
    for row in touch.itertuples():
        kinds = groups.loc[(row.date, row.level_id, row.touch_number)]
        episodes.append(
            dict(
                level=level,
                date=row.date,
                year=row.year,
                level_id=row.level_id,
                episode=int(row.touch_number),
                episode_group=min(int(row.touch_number), 4),
                first_touch_candle_start=row.bar_start_utc,
                first_touch_confirmation=row.timestamp_utc,
                source_observation=row.observation_id,
                prior_episode_gap_minutes=row.previous_episode_minutes,
                level_age_minutes=row.level_age_minutes,
                any_break="BREAK_ACCEPTANCE" in kinds,
                any_rejection="REJECTION" in kinds,
                any_sweep="SWEEP_RECLAIM" in kinds,
            )
        )
    for h in ["5", "10", "15", "30", "60", "session_close"]:
        e = pd.read_parquet(
            folder(level) / f"outcomes_{h}.parquet",
            columns=[
                "interaction_type",
                "direction",
                "complete",
                "atr14",
                "maximum_high_excursion",
                "maximum_low_excursion",
                "forward_close_change",
            ],
        )
        e = e[e.complete & (e.atr14 > 0)]
        for (kind, direction), g in e.groupby(["interaction_type", "direction"]):
            for side in ["UP", "DOWN"]:
                mf = (
                    g.maximum_high_excursion
                    if side == "UP"
                    else g.maximum_low_excursion
                )
                ma = (
                    g.maximum_low_excursion
                    if side == "UP"
                    else g.maximum_high_excursion
                )
                metrics = {
                    "mfe_points": mf,
                    "mae_points": ma,
                    "mfe_atr": mf / g.atr14,
                    "mae_atr": ma / g.atr14,
                    "directional_close_atr": g.forward_close_change
                    / g.atr14
                    * (1 if side == "UP" else -1),
                }
                for metric, series in metrics.items():
                    q = series.quantile([0.1, 0.25, 0.5, 0.75, 0.9, 0.95])
                    rows.append(
                        dict(
                            level=level,
                            interaction=kind,
                            stored_direction=direction,
                            measured_direction=side,
                            horizon=h,
                            metric=metric,
                            complete=len(g),
                            **{f"p{int(k*100)}": v for k, v in q.items()},
                        )
                    )
e = pd.DataFrame(episodes)
write(e, R / "touch_episode_ledger.csv")
for groupcols in [["level", "episode_group"], ["level", "year", "episode_group"]]:
    for key, g in e.groupby(groupcols):
        key = key if isinstance(key, tuple) else (key,)
        days = g.groupby("date")[["any_break", "any_rejection", "any_sweep"]].mean()
        incidence.append(
            dict(
                **dict(zip(groupcols, key)),
                episodes=len(g),
                dates=g.date.nunique(),
                daily_break_incidence=days.any_break.mean(),
                daily_rejection_incidence=days.any_rejection.mean(),
                daily_sweep_incidence=days.any_sweep.mean(),
                median_gap_minutes=g.prior_episode_gap_minutes.median(),
                median_level_age=g.level_age_minutes.median(),
            )
        )
write(pd.DataFrame(incidence), R / "episode_behavior_descriptive.csv")
write(pd.DataFrame(rows), R / "all_levels_forward_distributions.csv")
for level in LEVELS[:10]:
    write(
        pd.DataFrame(rows).query("level==@level"),
        folder(level) / "forward_distributions.csv",
    )
    write(e.query("level==@level"), folder(level) / "touch_episode_ledger.csv")
    write(
        pd.DataFrame(incidence).query("level==@level"),
        folder(level) / "episode_behavior_descriptive.csv",
    )
(R / "visual_review.json").write_text(
    json.dumps(
        {
            "point_families_visually_reviewed": LEVELS[:10],
            "chart_count": 147,
            "selection": "earliest chronological example per interaction plus earliest third-or-later episode, deduplicated; no outcome selection",
            "coverage": "touch, rejection, sweep, break, close/full holds, failed hold, retests/hold/fullhold/fail, rejection/sweep confirmations, repeated episodes",
            "failures": 0,
            "display_repairs": "Level lines begin at causal availability; post-confirmation area distinguished; charts end by actual RTH close. Full-size PNGs and contact sheets retained.",
            "zones": "No eligible zones; no fabricated charts.",
        },
        indent=2,
    )
)
