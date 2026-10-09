"""Development-only identity gate. No execution, signal filters or reserved-data reads."""

from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "work/mnq-individual-level-master-research"
OUT = ROOT / "work/5m-swing-low-execution-feasibility-v1"
STUDY = ROOT / "storage/event_studies/5cb7fab0d4e7414792a3fbe59ded4999"


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    config = json.loads((STUDY / "config.json").read_text())
    assert (config["segment"], config["start"], config["end"]) == (
        "development",
        "2020-01-01",
        "2024-01-01",
    )
    index = json.loads((MASTER / "EVIDENCE_INDEX.json").read_text())
    checked = {}
    for item in index["source_studies"]:
        p = Path(item["path"])
        if p.parent == STUDY:
            assert sha(p) == item["sha256"]
            checked[str(p.relative_to(ROOT))] = item["sha256"]
    filters = [
        ("level_type", "=", "5m_SWING_LOW"),
        ("interaction_type", "=", "TOUCH"),
        ("direction", "=", "DOWN"),
        ("date", ">=", "2020-01-01"),
        ("date", "<", "2024-01-01"),
    ]
    raw = (
        pq.read_table(STUDY / "v2_events.parquet", filters=filters)
        .to_pandas()
        .sort_values(["timestamp_utc", "event_id"])
    )
    level = MASTER / "08_5M_SWING_LOW"
    e = pd.read_parquet(level / "outcomes_30.parquet")
    e = e[(e.interaction_type == "TOUCH") & (e.direction == "DOWN")].copy()
    assert set(e.event_id) == set(raw.event_id) and len(e) == len(raw) == 5319
    assert raw.event_id.is_unique and raw.date.nunique() == 1006
    assert e.date.ge("2020-01-01").all() and e.date.lt("2024-01-01").all()
    measured = e.dropna(subset=["up_a1", "b_up_a1", "down_a1", "b_down_a1"])
    assert len(measured) == 4816 and measured.date.nunique() == 1004
    assert measured.complete.all() and (measured.atr14 > 0).all()
    assert measured.event_id.is_unique and measured.observation_id.is_unique
    primary = pd.read_csv(MASTER / "all_levels_primary_outcomes.csv")
    row = primary[
        (primary.level == "5m_SWING_LOW")
        & (primary.interaction == "TOUCH")
        & (primary.stored_direction == "DOWN")
        & (primary.measured_direction == "UP")
    ].iloc[0]
    dates = measured.groupby("date", sort=True)[["up_a1", "b_up_a1"]].mean()
    delta = (dates.up_a1 - dates.b_up_a1).to_numpy()
    effect = delta.mean()
    draws = delta[
        np.random.default_rng(1729).integers(0, len(delta), size=(2000, len(delta)))
    ].mean(axis=1)
    ci = np.quantile(draws, [0.025, 0.975])
    p = (1 + np.sum(abs(draws - effect) >= abs(effect))) / 2001
    reproduced = {
        "event_probability": dates.up_a1.mean(),
        "baseline_probability": dates.b_up_a1.mean(),
        "effect": effect,
        "ci_low": ci[0],
        "ci_high": ci[1],
        "p_value": p,
    }
    for key, value in reproduced.items():
        assert abs(value - row[key]) < 5e-10, (key, value, row[key])
    # Preserve the full registered family, including unavailable hypotheses.
    ps = primary.p_for_correction.to_numpy()
    order = np.argsort(ps, kind="stable")
    adjusted = np.minimum.accumulate(
        (ps[order] * len(ps) / np.arange(1, len(ps) + 1))[::-1]
    )[::-1].clip(0, 1)
    q = np.empty_like(ps)
    q[order] = adjusted
    assert np.allclose(q, primary.bh_q_value, rtol=0, atol=5e-10)
    reproduced["bh_q_value"] = float(row.bh_q_value)
    parsed = [json.loads(x) for x in raw.payload]
    flat = pd.DataFrame(parsed).sort_values(["timestamp_utc", "event_id"])
    assert flat.approach_side.eq("ABOVE").all()
    assert (
        pd.to_datetime(flat.timestamp_utc, utc=True)
        == pd.to_datetime(flat.bar_start_utc, utc=True) + pd.Timedelta(minutes=5)
    ).all()
    assert (
        pd.to_datetime(flat.level_available_at, utc=True)
        <= pd.to_datetime(flat.bar_start_utc, utc=True)
    ).all()
    measured_ids = set(measured.event_id)
    audit = e[
        ["event_id", "date", "timestamp_utc", "complete", "censor_reason", "atr14"]
    ].copy()
    audit["in_quoted_4816_measurement_subset"] = audit.event_id.isin(measured_ids)
    audit["exclusion_from_measurement"] = np.where(
        ~audit.complete,
        "30M_" + audit.censor_reason.fillna("UNKNOWN"),
        np.where(~(audit.atr14 > 0), "ATR_UNAVAILABLE", "NONE"),
    )
    audit.sort_values(["timestamp_utc", "event_id"]).to_csv(
        OUT / "population_reconciliation.csv", index=False, float_format="%.12g"
    )
    columns = [
        "event_id",
        "observation_id",
        "date",
        "timestamp_utc",
        "bar_start_utc",
        "level_id",
        "level_price",
        "level_available_at",
        "direction",
        "approach_side",
        "touch_number",
        "open",
        "high",
        "low",
        "close",
        "atr14",
    ]
    flat[columns].to_csv(
        OUT / "raw_touch_events.csv", index=False, float_format="%.12g"
    )
    quoted = flat[flat.event_id.isin(measured_ids)][columns].copy()
    quoted["population_role"] = (
        "HISTORICAL_30M_COMPLETE_ATR_MEASUREMENT_SUBSET_NOT_CAUSAL_ELIGIBILITY"
    )
    quoted.to_csv(OUT / "exact_touch_events.csv", index=False, float_format="%.12g")
    semantics = [
        (
            "pivot",
            "Strict low below both left and both right 5m candle lows; defaults frozen at left=2/right=2, zero minimum displacement.",
        ),
        (
            "timing",
            "Formation is pivot candle start. Availability is second right candle close (15 minutes after pivot start for consecutive 5m bars). Level must already be available at touch candle START.",
        ),
        (
            "level_selection",
            "Latest confirmed 5m low only, until replaced by another confirmed low. Structure operates on confirmed extended-session bars; event detection is RTH.",
        ),
        (
            "classification",
            "Low progression is HL/LL/EL or unclassified. HH/LH describe highs, not lows. No progression filter.",
        ),
        (
            "approach",
            "ABOVE means preceding adjacent valid RTH candle close > level; when no consecutive predecessor, current candle open > level. DOWN is mechanical approach direction; UP is the separately evaluated future direction.",
        ),
        (
            "touch",
            "low <= level <= high and previous processed candle for the level was not touching. One TOUCH per newly entered contiguous touching episode, not every touching candle.",
        ),
        (
            "episode_number",
            "Per-level/day counter; resets with new NY day. Gaps/incomplete bars reset touching/break state but do not silently establish uninterrupted episode continuity.",
        ),
        (
            "confirmation",
            "Touch event timestamp is candle START +5 minutes. Candle may wick or close below the level; TOUCH imposes no reclaim or rejection requirement.",
        ),
        (
            "overlap",
            "Same observation can carry TOUCH and REJECTION/SWEEP_RECLAIM/BREAK_ACCEPTANCE labels. They are overlapping classifications, not independent observations.",
        ),
        (
            "broken_swings",
            "Already-broken latest swing is not excluded by active_levels. Stored confirmed_swings.broken is as of event close and may include the current candle; it does not alone prove broken BEFORE the event.",
        ),
        (
            "duplicates",
            "5,319 unique raw event IDs; quoted 4,816 subset also has unique observation IDs. Cross-label overlaps must not be counted as independent trades.",
        ),
        (
            "gate",
            "Raw population differs from required 4,816/1,004. The quoted count reconciles only after historical outcome availability exclusions. Execution audit stopped as instructed.",
        ),
    ]
    pd.DataFrame(semantics, columns=["topic", "frozen_semantics"]).to_csv(
        OUT / "event_semantics_audit.csv", index=False
    )
    result = {
        "status": "DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY",
        "candidate_status": "DEVELOPMENT_MEASUREMENT_CANDIDATE_NOT_VALIDATED",
        "decision": "BLOCKED_POPULATION_DEFINITION",
        "execution_performed": False,
        "raw_events": 5319,
        "raw_dates": 1006,
        "measurement_events": 4816,
        "measurement_dates": 1004,
        "excluded_censored_30m": 498,
        "excluded_complete_missing_atr": 5,
        "reproduced_measurement": reproduced,
        "required_resolution": "Authorize a causal raw-event execution population, retaining 4816 as the historical measurement reference. Do not silently gate entry on future 30-minute completeness.",
    }
    (OUT / "recommendation.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    (OUT / "SWING_LOW_EXECUTION_FEASIBILITY.md").write_text(
        """# Swing-low execution feasibility: population gate blocked

Status: DEVELOPMENT_MEASUREMENT_CANDIDATE_NOT_VALIDATED. No execution diagnostics or target simulations were run.

The quoted measurement is reproduced exactly, but it is not the raw causal event population:

| Stage | Events | NY dates |
|---|---:|---:|
| Frozen TOUCH / DOWN detector events | 5,319 | 1,006 |
| Complete 30-minute outcomes | 4,821 | — |
| Complete, usable ATR and matched evidence | 4,816 | 1,004 |

There are 498 censored observations: 497 OUTSIDE_SESSION and one MISSING_MINUTES. Five additional complete outcomes lack usable ATR. No missing detector records or duplicate event IDs explain the difference.

The 4,816-event primary statistic is reproduced with the original equal-date weighting, 2,000 date-clustered bootstrap draws, seed 1729 and BH correction over the original full 672-cell family. Exact numbers are in recommendation.json. This confirms the historical measurement, not causal entry eligibility.

The user's gate explicitly requires 4,816 raw events / 1,004 dates and instructs stopping on mismatch. Using the 30-minute outcome-complete subset as entry eligibility would silently add session/outcome-availability selection; missing future source minutes cannot be known at entry. No such rule was added. A scope decision is needed before the Entry A/B/C × Stop A/B audit. The causal raw population can be evaluated with outcome censoring disclosed, while retaining the quoted subset only as historical measurement evidence.

## Frozen semantics

"""
        + "".join(f"- **{k}:** {v}\n" for k, v in semantics)
        + """
## Deliverables and boundaries

`exact_touch_events.csv` contains precisely the historical 4,816 measurement records and explicitly labels their retrospective population role. `raw_touch_events.csv` contains all 5,319 causal events. `population_reconciliation.csv` identifies every inclusion/exclusion. `event_semantics_audit.csv` documents detector semantics. Execution tables are intentionally not fabricated or reported as complete.

Only the existing Development study and Development exports were read. Original study identities were hash-verified. No market data, database, strategy, filter or production engine code was modified. Validation and OOS were not queried or revealed. Nothing was pushed.
"""
    )
    (OUT / "methodology_and_caveats.md").write_text("""# Methodology and caveats

This preflight stops at the population gate. It does not select an entry, stop, target or eligibility filter. Counts of complete forward observations are research denominators; they are not automatically executable signal counts. The historical report's 4,816/1,004 cell is preserved, not rewritten as 5,319/1,006.

The original bootstrap holds the empirical matched baseline fixed. BH retains the complete registered 672-comparison family. These checks reproduce existing Development evidence; they do not establish a tradable edge or new independent evidence. Event-close context can reflect the event candle itself; pre-event broken status requires earlier causal state, not relabeling the current close flag.

Remaining requested outputs (close classification, overlapping subsets, execution matrices, excursion sequencing, target diagnostics, yearly execution, fees and candidate recommendation) are blocked by the raw-population discrepancy. They have not been run.
""")
    manifest = {
        "source_hashes_verified": checked,
        "analysis_source_sha256": sha(Path(__file__)),
        "files": {
            p.name: sha(p)
            for p in sorted(OUT.iterdir())
            if p.is_file()
            and p.name not in ["reproducibility_manifest.json", "determinism.json"]
        },
        "execution_performed": False,
        "validation_oos_access": False,
    }
    (OUT / "reproducibility_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
