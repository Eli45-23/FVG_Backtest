"""Frozen Development sampling, identities and human-only measurement."""

from pathlib import Path
from dataclasses import asdict
import json, random, hashlib
import pandas as pd
from engine.canonical import clean, digest
from engine.zone_v2.provider import ProviderConfig, ratio

ROOT = Path(__file__).resolve().parents[2]
FOUNDATION = ROOT / "work/zone-v2-calendar-foundation"
OUT = ROOT / "work/zone-ground-truth-v2-calendar-accepted"
SEED = 20261008


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def load():
    manifest = json.loads((FOUNDATION / "determinism_manifest.json").read_text())
    for name in [
        "four_hour_bar_inventory.parquet",
        "frozen_calendar_profile.json",
        "human_ground_truth_readiness.json",
        "detected_supply_zones.parquet",
        "detected_demand_zones.parquet",
    ]:
        if sha(FOUNDATION / name) != manifest["artifacts"][name]["sha256"]:
            raise ValueError("Foundation identity changed: " + name)
    gate = json.loads((FOUNDATION / "human_ground_truth_readiness.json").read_text())
    if gate["status"] != "READY_FOR_HUMAN_GROUND_TRUTH":
        raise ValueError("Foundation not ready")
    profile = json.loads((FOUNDATION / "frozen_calendar_profile.json").read_text())
    bars = pd.read_parquet(FOUNDATION / "four_hour_bar_inventory.parquet")
    excluded = sorted(
        bars.loc[~bars.schedule_resolved.astype(bool), "session_date"].unique()
    )
    assert len(excluded) == 104
    accepted = bars.complete & bars.full & bars.schedule_resolved.astype(bool)
    if not (
        (
            bars.loc[accepted, "timestamp"]
            >= pd.Timestamp("2020-01-01", tz="America/New_York")
        )
        & (
            bars.loc[accepted, "availability_timestamp"]
            < pd.Timestamp("2024-01-01", tz="America/New_York")
        )
    ).all():
        raise ValueError("Development required")
    identity = clean(
        dict(
            dataset=profile["dataset"],
            dataset_sha256=digest(profile["dataset"]),
            calendar=profile["calendar_version"],
            calendar_sha256=profile["profile_sha256"],
            bar_profile=profile["bar_version"],
            bar_profile_sha256=digest(
                {
                    "version": profile["bar_version"],
                    "calendar": profile["profile_sha256"],
                    "bars": gate["bars_sha256"],
                }
            ),
            bars_sha256=gate["bars_sha256"],
            accepted_subset_policy="resolved AND complete AND full; base/departure adjacent; no unresolved chart candles",
            exclusion_dates=excluded,
            exclusion_sha256=digest(excluded),
            provider_configuration=asdict(ProviderConfig()),
            provider_configuration_sha256=digest(asdict(ProviderConfig())),
            provider_source_sha256=sha(ROOT / "engine/zone_v2/provider.py"),
        )
    )
    zones = []
    for side in ("supply", "demand"):
        zones.extend(
            json.loads(x)
            for x in pd.read_parquet(
                FOUNDATION / f"detected_{side}_zones.parquet"
            ).payload
        )
    return bars, identity, zones


def consecutive(bars, a, c):
    s = bars.iloc[a : c + 1]
    return (
        a >= 0
        and bool((s.complete & s.full & s.schedule_resolved.astype(bool)).all())
        and all(
            s.iloc[j].availability_timestamp == s.iloc[j + 1].timestamp
            for j in range(len(s) - 1)
        )
    )


def window(bars, c, kind, **extra):
    at = bars.iloc[c].availability_timestamp
    return clean(
        dict(
            sample_id=digest([kind, str(at), extra.get("proposal", {}).get("zone_id")]),
            kind=kind,
            candidate=c,
            confirmation=at,
            ny_date=str(at.tz_convert("America/New_York").date()),
            year=at.tz_convert("America/New_York").year,
            **extra,
        )
    )


def sample(bars, identity, zones):
    rng = random.Random(SEED)
    ids = [c for c in range(2, len(bars)) if consecutive(bars, c - 2, c)]
    blind = []
    for year in range(2020, 2024):
        pool = [
            c
            for c in ids
            if bars.iloc[c].availability_timestamp.tz_convert("America/New_York").year
            == year
        ]
        blind.extend(window(bars, c, "BLIND") for c in sorted(rng.sample(pool, 20)))
    used = {x["candidate"] for x in blind}
    # Balanced deterministic round-robin strata, not subsequent response.
    review = []
    lookup = {str(t): i for i, t in enumerate(bars.availability_timestamp)}
    for side in ("SUPPLY", "DEMAND"):
        groups = {}
        for z in sorted(zones, key=lambda z: z["zone_id"]):
            if z["zone_type"] != side:
                continue
            c = lookup[str(pd.Timestamp(z["availability_timestamp"]))]
            key = (
                bars.iloc[c].availability_timestamp.year,
                z["base_count"],
                z["pattern_type"],
            )
            groups.setdefault(key, []).append((c, z))
        for pool in groups.values():
            rng.shuffle(pool)
        keys = sorted(groups)
        count = 0
        while count < 25 and any(groups.values()):
            for k in keys:
                if groups[k] and count < 25:
                    c, z = groups[k].pop()
                    review.append(window(bars, c, "PROVIDER_REVIEW", proposal=z))
                    count += 1
    # Near misses: diagnostic categories retained privately, never sent with blind charts.
    pools = {
        k: []
        for k in [
            "BASE_BODY",
            "BASE_WIDTH",
            "NO_OVERLAP",
            "WEAK_DEPARTURE",
            "LATE_DEPARTURE",
            "NO_CLOSE_OUTSIDE",
        ]
    }
    for c in ids:
        if c in used:
            continue
        for depn in (1, 2, 3):
            for basen in (1, 2, 3):
                a = c - depn - basen + 1
                b = c - depn
                if not consecutive(bars, a, c):
                    continue
                base = bars.iloc[a : b + 1].to_dict("records")
                deps = bars.iloc[b + 1 : c + 1].to_dict("records")
                atr = base[-1]["atr14"]
                if pd.isna(atr) or atr <= 0:
                    continue
                hi = max(x["high"] for x in base)
                lo = min(x["low"] for x in base)
                sign = (
                    1 if deps[-1]["close"] > hi else -1 if deps[-1]["close"] < lo else 0
                )
                prox = (
                    max(max(x["open"], x["close"]) for x in base)
                    if sign == 1
                    else min(min(x["open"], x["close"]) for x in base)
                )
                failures = []
                if max(map(ratio, base)) > 0.5:
                    failures.append("BASE_BODY")
                if hi - lo > 1.25 * atr:
                    failures.append("BASE_WIDTH")
                if min(x["high"] for x in base) <= max(x["low"] for x in base):
                    failures.append("NO_OVERLAP")
                if max(map(ratio, deps)) < 0.6 or (
                    sign and (deps[-1]["close"] - prox) * sign < atr
                ):
                    failures.append("WEAK_DEPARTURE")
                if not sign:
                    failures.append("NO_CLOSE_OUTSIDE")
                if depn == 3:
                    if any(
                        (x["close"] - prox) * sign >= atr
                        and (x["close"] > hi if sign == 1 else x["close"] < lo)
                        and max(map(ratio, deps[: j + 1])) >= 0.6
                        for j, x in enumerate(deps[:2])
                    ):
                        continue
                    failures.append("LATE_DEPARTURE")
                if len(failures) == 1:
                    pools[failures[0]].append((c, a, b))
                elif "NO_OVERLAP" in failures and depn <= 2:
                    pools["NO_OVERLAP"].append((c, a, b))
    negative = []
    for reason, pool in pools.items():
        rng.shuffle(pool)
        n = 0
        for c, a, b in pool:
            if c in used:
                continue
            negative.append(
                window(
                    bars,
                    c,
                    "NEAR_MISS",
                    private_reason=reason,
                    diagnostic_first=a,
                    diagnostic_last=b,
                )
            )
            used.add(c)
            n += 1
            if n == 4:
                break
    if len(negative) < 20:
        raise ValueError("Insufficient deterministic near misses")
    protocol = dict(
        version="ZONE_GROUND_TRUTH_ACCEPTED_V2",
        seed=SEED,
        identity=identity,
        provider_status="PROVISIONAL_PENDING_HUMAN_GROUND_TRUTH",
        opportunity="All human zones whose confirmation is exactly the displayed cutoff; preceding candles are context only. Base ends 1–3 adjacent full candles before cutoff; human labels are not forced to obey provider thresholds.",
        blind_sample="20/year uniform random accepted opportunities, independent of provider; near misses separate exploratory stratum",
        matching="Same direction, same confirmation cutoff, intersecting base candle IDs, same last-base candle (same departure sequence). Deterministic maximum-cardinality one-to-one matching; exact base/boundaries/availability scored separately.",
        collection_order="Complete all 80 blind and >=20 near-miss windows before provider review; finish each window after marking every zone or explicitly none.",
        minimum=dict(
            blind_windows=80,
            provider_supply=25,
            provider_demand=25,
            near_miss_windows=20,
            blind_human_zones=10,
        ),
        acceptance=dict(
            HUMAN_GROUND_TRUTH_ACCEPTED=dict(
                precision=0.9,
                recall=0.9,
                base=0.9,
                proximal=0.9,
                distal=0.9,
                availability=0.95,
            ),
            HUMAN_GROUND_TRUTH_ACCEPTED_WITH_LIMITATIONS=dict(
                precision=0.8,
                recall=0.8,
                base=0.8,
                proximal=0.8,
                distal=0.8,
                availability=0.9,
            ),
        ),
        decision_rule="Below lower tier after minimum coverage: REJECTED. Missing coverage or undefined metrics: INSUFFICIENT_HUMAN_LABELS. Metrics describe these reviewed samples only. No population claims.",
        availability_limit="Fixed confirmation opportunities condition matching on timing; availability agreement here is mechanical and cannot estimate population confirmation-time accuracy.",
        near_miss_limit="No-overlap examples may also violate other criteria; strata are diagnostics, not asserted negative labels.",
        no_outcomes=True,
    )
    protocol["protocol_sha256"] = digest(protocol)
    return protocol, blind, review, negative


def freeze():
    OUT.mkdir(parents=True, exist_ok=True)
    bars, ident, zones = load()
    p, b, r, n = sample(bars, ident, zones)
    bundle = dict(protocol=p, blind=b, review=r, near_miss=n)
    path = OUT / "collection.json"
    encoded = json.dumps(clean(bundle), sort_keys=True, indent=2) + "\n"
    if path.exists() and path.read_text() != encoded:
        raise ValueError("Frozen collection differs; new version required")
    path.write_text(encoded)
    (OUT / "frozen_sampling_protocol.json").write_text(
        json.dumps(p, indent=2, sort_keys=True) + "\n"
    )
    for name, rows in [
        ("blind_windows", b),
        ("provider_review_sample", r),
        ("negative_near_miss_sample", n),
    ]:
        pd.DataFrame(
            [
                {
                    k: json.dumps(v, sort_keys=True) if isinstance(v, dict) else v
                    for k, v in x.items()
                }
                for x in rows
            ]
        ).to_csv(OUT / (name + ".csv"), index=False)
    return bundle
