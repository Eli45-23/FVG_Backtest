"""Reviewed-sample metrics; no outcome access or provider parameter changes."""

from collections import Counter
import pandas as pd


def base_key(z):
    return tuple(str(pd.Timestamp(t)) for t in z["base_timestamps"])


def agreement(h, p):
    supply = h["side"] == "SUPPLY"
    return dict(
        human_base_timestamps=list(h["base_timestamps"]),
        provider_base_timestamps=list(p["base_timestamps"]),
        human_top=h["top"],
        human_bottom=h["bottom"],
        provider_top=p["top"],
        provider_bottom=p["bottom"],
        human_availability=h["availability"],
        provider_availability=p["availability_timestamp"],
        proximal_difference=h["proximal"] - (p["bottom"] if supply else p["top"]),
        distal_difference=h["distal"] - (p["top"] if supply else p["bottom"]),
        EXACT_BASE_MATCH=base_key(h) == base_key(p),
        EXACT_BOUNDARY_MATCH=(h["top"], h["bottom"]) == (p["top"], p["bottom"]),
        proximal_agreement=h["proximal"] == (p["bottom"] if supply else p["top"]),
        distal_agreement=h["distal"] == (p["top"] if supply else p["bottom"]),
        AVAILABILITY_MATCH=pd.Timestamp(h["availability"])
        == pd.Timestamp(p["availability_timestamp"]),
    )


def measure(bundle, labels, zones):
    done = {x["sample_id"] for x in labels if x["window_complete"]}
    blind_ids = {x["sample_id"] for x in bundle["blind"]}
    review_ids = {x["sample_id"] for x in bundle["review"]}
    near_ids = {x["sample_id"] for x in bundle["near_miss"]}
    humans = [x for x in labels if x["sample_id"] in blind_ids and x["human"]]
    reviews = [x for x in labels if x["sample_id"] in review_ids]
    result = dict(
        status="INSUFFICIENT_HUMAN_LABELS",
        reviewed_blind_windows=len(done & blind_ids),
        near_miss_windows_completed=len(done & near_ids),
        provider_proposals_reviewed=len(reviews),
        total_human_annotations=len(labels),
        human_valid_supply=sum(x["human"]["side"] == "SUPPLY" for x in humans),
        human_valid_demand=sum(x["human"]["side"] == "DEMAND" for x in humans),
        human_NOT_A_ZONE=sum(
            x["label"] == "NOT_A_ZONE" and x["sample_id"] in blind_ids for x in labels
        ),
        concept_precision=None,
        blind_window_recall=None,
        base_agreement=None,
        proximal_agreement=None,
        distal_agreement=None,
        availability_agreement=None,
        scope="Reviewed samples only; near misses excluded from primary precision/recall. Never population precision/recall.",
        rows=[],
    )
    if not blind_ids | review_ids | near_ids <= done:
        return result
    rows = []
    for s in bundle["blind"]:
        hs = [x for x in humans if x["sample_id"] == s["sample_id"]]
        ps = sorted(
            [
                z
                for z in zones
                if pd.Timestamp(z["availability_timestamp"])
                == pd.Timestamp(s["confirmation"])
            ],
            key=lambda z: z["zone_id"],
        )
        edges = {
            i: [
                j
                for j, p in enumerate(ps)
                if h["human"]["side"] == p["zone_type"]
                and base_key(h["human"])[-1] == base_key(p)[-1]
                and set(base_key(h["human"])) & set(base_key(p))
            ]
            for i, h in enumerate(hs)
        }
        matched = {}

        def augment(i, seen):
            for j in edges[i]:
                if j in seen:
                    continue
                seen.add(j)
                if j not in matched or augment(matched[j], seen):
                    matched[j] = i
                    return True
            return False

        for i in range(len(hs)):
            augment(i, set())
        reverse = {i: j for j, i in matched.items()}
        for i, h in enumerate(hs):
            p = ps[reverse[i]] if i in reverse else None
            rows.append(
                dict(
                    sample_id=s["sample_id"],
                    mode="BLIND",
                    annotation_id=h["annotation_id"],
                    zone_id=p["zone_id"] if p else None,
                    side=h["human"]["side"],
                    base_count=h["human"]["base_count"],
                    pattern=p["pattern_type"] if p else "UNMATCHED",
                    outcome="TP" if p else "FN",
                    ZONE_CONCEPT_MATCH=bool(p),
                    reason=h["notes"] if not p else "",
                    **(agreement(h["human"], p) if p else {}),
                )
            )
        for j, p in enumerate(ps):
            if j not in matched:
                rows.append(
                    dict(
                        sample_id=s["sample_id"],
                        mode="BLIND",
                        zone_id=p["zone_id"],
                        side=p["zone_type"],
                        base_count=p["base_count"],
                        pattern=p["pattern_type"],
                        outcome="PROVIDER_ONLY",
                        ZONE_CONCEPT_MATCH=False,
                        reason="No matching human zone in completed blind opportunity",
                    )
                )
    for r in reviews:
        p = r["provider"]
        h = r["human"]
        rows.append(
            dict(
                sample_id=r["sample_id"],
                mode="PROVIDER_REVIEW",
                annotation_id=r["annotation_id"],
                zone_id=p["zone_id"],
                side=p["zone_type"],
                base_count=p["base_count"],
                pattern=p["pattern_type"],
                outcome=r["label"],
                ZONE_CONCEPT_MATCH=h is not None,
                reason=r["notes"] or r["label"],
                **(agreement(h, p) if h else {}),
            )
        )
    rr = [r for r in rows if r["mode"] == "PROVIDER_REVIEW"]
    br = [r for r in rows if r["mode"] == "BLIND"]
    matched = [r for r in rows if r["ZONE_CONCEPT_MATCH"]]

    def avg(items, key):
        return sum(bool(r.get(key)) for r in items) / len(items) if items else None

    result.update(
        rows=rows,
        concept_precision=avg(rr, "ZONE_CONCEPT_MATCH"),
        blind_window_recall=(
            sum(r["outcome"] == "TP" for r in br) / len(humans) if humans else None
        ),
        human_zones_found=len(humans),
        provider_zones_found=sum(r["outcome"] in ("TP", "PROVIDER_ONLY") for r in br),
        true_positives=sum(r["outcome"] == "TP" for r in br),
        false_negatives=sum(r["outcome"] == "FN" for r in br),
        provider_only_detections=sum(r["outcome"] == "PROVIDER_ONLY" for r in br),
        base_agreement=avg(matched, "EXACT_BASE_MATCH"),
        proximal_agreement=avg(matched, "proximal_agreement"),
        distal_agreement=avg(matched, "distal_agreement"),
        availability_agreement=avg(matched, "AVAILABILITY_MATCH"),
        review_decisions=dict(Counter(r["outcome"] for r in rr)),
    )
    # Agreements are also disaggregated; overlapping samples are not independent estimates.
    result["agreement_denominator"] = len(matched)
    result["groups"] = {}

    def grouped(g):
        review = [r for r in g if r["mode"] == "PROVIDER_REVIEW"]
        blind = [r for r in g if r["mode"] == "BLIND" and r["outcome"] in ("TP", "FN")]
        matches = [r for r in g if r["ZONE_CONCEPT_MATCH"]]
        return dict(
            n=len(g),
            provider_review_precision=avg(review, "ZONE_CONCEPT_MATCH"),
            blind_recall=avg(blind, "ZONE_CONCEPT_MATCH"),
            matched_count=len(matches),
            base_agreement=avg(matches, "EXACT_BASE_MATCH"),
            proximal_agreement=avg(matches, "proximal_agreement"),
            distal_agreement=avg(matches, "distal_agreement"),
            availability_agreement=avg(matches, "AVAILABILITY_MATCH"),
        )

    for column in ["side", "base_count", "pattern", "mode"]:
        result["groups"][column] = {
            str(v): grouped([r for r in rows if r.get(column) == v])
            for v in sorted({r.get(column) for r in rows}, key=str)
        }
    result["false_positive_reasons"] = dict(
        Counter(r["reason"] for r in rr if not r["ZONE_CONCEPT_MATCH"])
    )
    result["false_negative_reasons"] = dict(
        Counter(
            r["reason"] or "Unspecified by human" for r in br if r["outcome"] == "FN"
        )
    )
    result["base_disagreement_reasons"] = dict(
        Counter(
            r["reason"] or "Selected base differs"
            for r in matched
            if not r["EXACT_BASE_MATCH"]
        )
    )
    values = dict(
        precision=result["concept_precision"],
        recall=result["blind_window_recall"],
        base=result["base_agreement"],
        proximal=result["proximal_agreement"],
        distal=result["distal_agreement"],
        availability=result["availability_agreement"],
    )
    if len(humans) < bundle["protocol"]["minimum"]["blind_human_zones"] or any(
        v is None for v in values.values()
    ):
        return result
    result["status"] = "HUMAN_GROUND_TRUTH_REJECTED"
    for status, thresholds in bundle["protocol"]["acceptance"].items():
        if all(values[k] >= v for k, v in thresholds.items()):
            result["status"] = status
            break
    return result
