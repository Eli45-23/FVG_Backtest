"""Create deterministic sample or export immutable human-label snapshot. No outcomes."""

import argparse, json
from pathlib import Path
from collections import Counter
import pandas as pd
from engine.canonical import clean, digest
from engine.zone_ground_truth.collection import OUT, freeze, sha


def export(initial=False):
    from backend.app import zone_ground_truth_v2 as z

    bars, ident, zones, b = z.foundation()
    labels = z.records()
    metrics = z.comparison()
    payload = clean(
        dict(
            annotations=labels,
            metrics=metrics,
            protocol_sha256=b["protocol"]["protocol_sha256"],
        )
    )
    dest = OUT if initial else OUT / "exports" / digest(payload)
    dest.mkdir(parents=True, exist_ok=True)

    def write(name, value):
        text = (
            value
            if isinstance(value, str)
            else json.dumps(clean(value), indent=2, sort_keys=True) + "\n"
        )
        p = dest / name
        if p.exists() and p.read_text() != text:
            raise ValueError("Immutable export exists with different content: " + name)
        p.write_text(text)

    write("human_annotations.json", labels)
    write("agreement_metrics.json", metrics)

    def csv(name, rows, cols):
        df = pd.DataFrame(
            [
                {
                    k: (
                        json.dumps(clean(v), sort_keys=True)
                        if isinstance(v, (dict, list))
                        else v
                    )
                    for k, v in r.items()
                }
                for r in rows
            ]
        )
        if not len(df):
            df = pd.DataFrame(columns=cols)
        write(name, df.to_csv(index=False))

    current = z.latest()
    rows = metrics["rows"]
    csv(
        "blind_ground_truth.csv",
        [r for r in current if r["mode"] == "BLIND"],
        ["annotation_id", "sample_id", "sample_kind", "label", "human"],
    )
    csv(
        "provider_review_labels.csv",
        [r for r in current if r["mode"] == "PROVIDER_REVIEW"],
        ["annotation_id", "sample_id", "label", "human", "provider"],
    )
    for name, items in [
        ("provider_comparison", rows),
        (
            "false_positives",
            [r for r in rows if r["outcome"] in ("REJECT_NOT_A_ZONE", "PROVIDER_ONLY")],
        ),
        ("false_negatives", [r for r in rows if r["outcome"] == "FN"]),
        (
            "base_boundary_disagreements",
            [
                r
                for r in rows
                if r.get("ZONE_CONCEPT_MATCH")
                and (not r.get("EXACT_BASE_MATCH") or not r.get("EXACT_BOUNDARY_MATCH"))
            ],
        ),
    ]:
        csv(
            name + ".csv",
            items,
            ["sample_id", "annotation_id", "zone_id", "mode", "outcome", "reason"],
        )
    write(
        "known_limitations.md",
        """# Collection limitations

Human labeling is pending. Empty label/comparison CSVs are intentional; null
metrics mean unavailable, not zero agreement. No agent-generated labels count.

These are reviewed-sample measurements, never population precision/recall.
Blind matching uses the exact cutoff and same last-base candle. Availability
agreement is conditional on that opportunity, not independent timing accuracy.
Base/boundary/time denominators pool matched primary-sample rows; mode and side
breakdowns remain separate. Overlap is not independent evidence. Unmatched human
zones have no provider pattern classification.

Unknown sessions, shortened and incomplete bars are excluded. Chart context may
therefore have gaps or few bars; selection cannot bridge a missing/shortened bar.
Near misses are diagnostic strata, not pre-established negative human labels;
no-overlap examples may violate more than one criterion. Do not inspect private
proposal/near-miss CSVs until blind collection is complete. Past research exposure
cannot be undone. Provider review exposure freezes blind corrections.

The collection pipeline keeps the provider provisional and does not access
forward outcomes or Validation/OOS outcomes. The broader legacy test invocation
violated the task scope; see isolation-incident/INCIDENT_REPORT.md. No thresholds
were tuned. V3 need cannot be assessed until genuine human judgments are collected.
""",
    )
    report = f"""# Accepted-calendar ground-truth collection

Status: **{metrics['status']}**. Collection infrastructure is ready; genuine human
labeling and comparison are not completed. Provider remains provisional.

## Frozen scope

Calendar: {ident['calendar']} (`{ident['calendar_sha256']}`).
Bar profile: {ident['bar_profile']} (`{ident['bar_profile_sha256']}`).
Dataset hash: `{ident['dataset_sha256']}`.
Excluded session-list hash: `{ident['exclusion_sha256']}` (104 dates).
Provider configuration hash: `{ident['provider_configuration_sha256']}`.
Protocol hash: `{b['protocol']['protocol_sha256']}`. Seed: {b['protocol']['seed']}.

80 blind windows (20 in each of 2020–2023), 50 provider proposals (25 supply,
25 demand), 24 near misses. Selection does not inspect subsequent responses.
Provider dates/proposals and diagnostic near-miss reasons are hidden during blind
collection. Exact dataset and bar identities are recorded with every annotation.

## Collection progress

Reviewed blind windows: {metrics['reviewed_blind_windows']} / 80.
Provider proposals reviewed: {metrics['provider_proposals_reviewed']} / 50.
Near-miss windows completed: {metrics['near_miss_windows_completed']} / 24.
Human annotations: {metrics['total_human_annotations']}.
Precision, recall and agreement: unavailable until required human review finishes.
False-positive/false-negative reasons and V3 recommendations: not established.

Use the Lab's Zone Labeler → Accepted-calendar Ground Truth. Choose a human
judgment, select/approve a base for valid zones, and explicitly finish each window.
Multiple zones and append-only corrections are supported. Provider review unlocks
only after blind/near-miss completion. Consult the repository workflow document
for frozen matching, acceptance tiers, denominators and limitations.

All required output files exist; empty results are placeholders for pending human
judgments, not claimed evidence. Automated browser clicks use isolated test
storage and never enter this collection. No forward-outcome research, Validation
query, OOS reveal, paid download, threshold change or push is authorized here.

## Test scope exception

A broad legacy test invocation nevertheless processed February 2024 data and
created test records in normal storage due to import-order isolation. Those test
records were specifically quarantined/removed; original records and sealed studies
remain preserved. No pre-existing OOS outcome was revealed. See
`isolation-incident/INCIDENT_REPORT.md`. This exception prevents a blanket claim
that Validation rows were untouched. Remaining verification is synthetic-only.
"""
    write("GROUND_TRUTH_COLLECTION_REPORT.md", report)
    names = [
        "human_annotations.json",
        "agreement_metrics.json",
        "blind_ground_truth.csv",
        "provider_review_labels.csv",
        "provider_comparison.csv",
        "false_positives.csv",
        "false_negatives.csv",
        "base_boundary_disagreements.csv",
        "known_limitations.md",
        "GROUND_TRUTH_COLLECTION_REPORT.md",
    ]
    write(
        "reproducibility_manifest.json",
        dict(
            protocol_sha256=b["protocol"]["protocol_sha256"],
            collection_sha256=sha(OUT / "collection.json"),
            identity=ident,
            artifact_hashes={n: sha(dest / n) for n in names},
            sample_hashes={
                n: sha(OUT / n)
                for n in [
                    "blind_windows.csv",
                    "provider_review_sample.csv",
                    "negative_near_miss_sample.csv",
                    "frozen_sampling_protocol.json",
                ]
            },
            provider_review_strata=dict(
                Counter(
                    str(
                        (
                            x["year"],
                            x["proposal"]["zone_type"],
                            x["proposal"]["base_count"],
                            x["proposal"]["pattern_type"],
                        )
                    )
                    for x in b["review"]
                )
            ),
            near_miss_counts=dict(Counter(x["private_reason"] for x in b["near_miss"])),
            human_labels_only=True,
            forward_outcomes=False,
            validation_rows_accessed_by_legacy_tests=True,
            existing_oos_outcomes_revealed=False,
            test_isolation_incident="See isolation-incident/INCIDENT_REPORT.md; test-created records quarantined and normal counts restored",
        ),
    )
    print(dest)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["sample", "initial-export", "export"])
    a = p.parse_args()
    if a.action == "sample":
        freeze()
    else:
        export(a.action == "initial-export")
