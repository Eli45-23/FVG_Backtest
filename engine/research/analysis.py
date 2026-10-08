"""Descriptive, matched ordinary-observation comparisons; never a strategy ranking."""

from collections import defaultdict
import numpy as np
from engine.research.outcomes import THRESHOLDS, directional

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
            matched[(b["year"], b["time_bucket"])].append((b, outcome))
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
        pairs.append((e, outcome, matched[(e["year"], e["time_bucket"])]))
    mean = lambda x: float(np.mean(x)) if x else None
    median = lambda x: float(np.median(x)) if x else None
    tables = []
    for sign in ["up", "down"]:
        for threshold in THRESHOLDS:
            key = f"{sign}_{threshold}"
            event_prob = mean(
                [int(o["thresholds"][key]["reached"]) for _, o, _ in pairs]
            )
            paired = [(e, o, bs) for e, o, bs in pairs if bs]
            base_prob = mean(
                [
                    mean([int(b["thresholds"][key]["reached"]) for _, b in bs])
                    for _, _, bs in paired
                ]
            )
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
        "mfe_distribution": quantiles(mfes),
        "mae_distribution": quantiles(maes),
        "high_excursion_distribution": quantiles(up),
        "low_excursion_distribution": quantiles(down),
        "probabilities": tables,
        "unique_matched_baseline_observations": len(
            {b["event_id"] for _, _, bs in pairs for b, _ in bs}
        ),
        "baseline_method": "Year + 30-minute confirmation-time bucket; event-weighted ordinary observations, overlaps allowed",
    }
