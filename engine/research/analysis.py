"""Descriptive, matched ordinary-observation comparisons; never a strategy ranking."""

from collections import defaultdict
import numpy as np
from engine.research.outcomes import THRESHOLDS, directional


def volatility_bucket(atr):
    if atr is None:
        return "unavailable"
    value = float(atr)
    return (
        "<10"
        if value < 10
        else "10-25" if value < 25 else "25-50" if value < 50 else "50+"
    )


def match_key(row):
    return (
        row["year"],
        row["time_bucket"],
        row.get("volatility_bucket", "unavailable"),
    )


FILTERS = [
    "level_type",
    "interaction_type",
    "direction",
    "touch_number",
    "time_bucket",
    "year",
    "weekday",
]


def select_events(events, filters):
    for k, value in filters.items():
        if k in FILTERS and value not in (None, ""):
            if k == "touch_number" and value == "3+":
                events = [e for e in events if e[k] >= 3]
            else:
                events = [e for e in events if str(e[k]) == str(value)]
    return events


def describe(
    events,
    labels,
    baseline,
    baseline_labels,
    horizon="30",
    interpretation="continuation",
):
    matched = defaultdict(list)
    for b in baseline:
        outcome = baseline_labels.get(b["event_id"], {}).get(horizon, {})
        if outcome.get("complete"):
            matched[match_key(b)].append((b, outcome))
    pairs, mfes, maes, changes, up, down = [], [], [], [], [], []
    for e in events:
        outcome = labels.get(e["event_id"], {}).get(horizon, {})
        if not outcome.get("complete"):
            continue
        mfe, mae = directional(outcome, e["direction"], interpretation)
        if mfe is not None:
            mfes.append(mfe)
            maes.append(mae)
        changes.append(outcome["forward_close_change"])
        up.append(outcome["maximum_high_excursion"])
        down.append(outcome["maximum_low_excursion"])
        pairs.append((e, outcome, matched[match_key(e)]))
    mean = lambda x: float(np.mean(x)) if x else None
    median = lambda x: float(np.median(x)) if x else None
    baseline_stats = {
        key: {
            f"{sign}_{n}": mean(
                [int(o["thresholds"][f"{sign}_{n}"]["reached"]) for _, o in values]
            )
            for sign in ("up", "down")
            for n in THRESHOLDS
        }
        for key, values in matched.items()
    }
    baseline_excursions = {
        (key, direction): tuple(
            mean([directional(o, direction, interpretation)[i] for _, o in values])
            for i in (0, 1)
        )
        for key, values in matched.items()
        for direction in ("UP", "DOWN")
    }
    matched_mfes, matched_maes, base_mfes, base_maes = [], [], [], []
    for e, o, bs in pairs:
        if bs and e["direction"] != "UNKNOWN":
            mfe, mae = directional(o, e["direction"], interpretation)
            bm, ba = baseline_excursions[(match_key(e), e["direction"])]
            matched_mfes.append(mfe)
            matched_maes.append(mae)
            base_mfes.append(bm)
            base_maes.append(ba)
    tables = []
    for sign in ["up", "down"]:
        for threshold in THRESHOLDS:
            key = f"{sign}_{threshold}"
            event_prob = mean(
                [int(o["thresholds"][key]["reached"]) for _, o, _ in pairs]
            )
            paired = [(e, o, bs) for e, o, bs in pairs if bs]
            base_prob = mean([baseline_stats[match_key(e)][key] for e, _, _ in paired])
            matched_event_prob = mean(
                [int(o["thresholds"][key]["reached"]) for _, o, _ in paired]
            )
            times = [
                o["thresholds"][key]["minutes"]
                for _, o, _ in pairs
                if o["thresholds"][key]["reached"]
            ]
            tables.append(
                {
                    "direction": sign,
                    "points": threshold,
                    "event_probability": event_prob,
                    "baseline_probability": base_prob,
                    "matched_event_probability": matched_event_prob,
                    "difference": (
                        matched_event_prob - base_prob
                        if base_prob is not None
                        else None
                    ),
                    "matched_events": len(paired),
                    "median_minutes_to_hit": median(times),
                }
            )
    quantiles = lambda xs: (
        {str(q): float(np.percentile(xs, q)) for q in [0, 25, 50, 75, 90, 100]}
        if xs
        else {}
    )
    return {
        "events": len(events),
        "complete_outcomes": len(pairs),
        "censored_outcomes": len(events) - len(pairs),
        "directional_observations": len(mfes),
        "mean_mfe": mean(mfes),
        "median_mfe": median(mfes),
        "mean_mae": mean(maes),
        "median_mae": median(maes),
        "mean_forward_change": mean(changes),
        "matched_mean_mfe": mean(matched_mfes),
        "baseline_mean_mfe": mean(base_mfes),
        "matched_mean_mae": mean(matched_maes),
        "baseline_mean_mae": mean(base_maes),
        "mfe_distribution": quantiles(mfes),
        "mae_distribution": quantiles(maes),
        "high_excursion_distribution": quantiles(up),
        "low_excursion_distribution": quantiles(down),
        "probabilities": tables,
        "unique_matched_baseline_observations": len(
            {
                b["event_id"]
                for key in {match_key(e) for e, _, _ in pairs}
                for b, _ in matched[key]
            }
        ),
        "baseline_method": "Year + 30-minute confirmation time + causal ATR14 bucket; event-weighted ordinary observations, overlaps allowed",
    }
