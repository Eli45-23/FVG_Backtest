"""Reuse six immutable event populations, add O15, and generate causal entries."""

from pathlib import Path
import sys, json, hashlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
import pyarrow.parquet as pq
from engine.canonical import digest, clean
from engine.research.levels import SessionConfig, LevelEngine, FIVE, NY, valid_bar
from engine.research.events import EventDetector
from engine.research.sequences import Sequences
from scripts.eight_level_study.core import Opening15, Entries

P = ROOT / "work/eight-level-reaction-entry-study-v1"
MASTER = ROOT / "work/mnq-individual-level-master-research"
PM = "78c96aa0e91147ba9913e365f33ed2f9"
OLD = "5cb7fab0d4e7414792a3fbe59ded4999"
LEVELS = ["PDH", "PDL", "PMH", "PML", "O5H", "O5L", "O15H", "O15L"]
DIRS = ["01_PDH", "02_PDL", "03_PMH", "04_PML", "05_O5H", "06_O5L"]


def sha(p):
    with open(p, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def write(name, df):
    df.to_csv(P / name, index=False, float_format="%.12g", lineterminator="\n")


def load():
    configs = {
        id: json.loads(
            (ROOT / "storage/event_studies" / id / "config.json").read_text()
        )
        for id in [OLD, PM]
    }
    for c in configs.values():
        assert (c["start"], c["end"], c["segment"]) == (
            "2020-01-01",
            "2024-01-01",
            "development",
        )
    cfg = configs[PM]
    assert (
        cfg["session"]["premarket_start"] == "00:00"
        and cfg["session"]["premarket_end"] == "09:30"
    )
    provenance = {}
    for id in [OLD, PM]:
        p = ROOT / "storage/event_studies" / id / "config.json"
        provenance[str(p.relative_to(ROOT))] = sha(p)
    for v in cfg["dataset_identity"]["files"].values():
        p = ROOT / "outputs/data" / v["name"]
        assert sha(p) == v["sha256"]
        provenance[str(p.relative_to(ROOT))] = v["sha256"]
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
    assert (
        bars.timestamp_utc.is_unique
        and bars.timestamp_utc.between(start, end, inclusive="left").all()
    )
    sessions = {
        k: tuple(map(pd.Timestamp, v))
        for k, v in cfg["calendar"]["sessions"].items()
        if "2020-01-01" <= k < "2024-01-01"
    }
    cols = [
        "event_id",
        "timestamp_utc",
        "date",
        "year",
        "session_close",
        "price_at_event",
        "atr14",
        "volatility_bucket",
        "time_bucket",
        "atr_regime",
    ]
    p = ROOT / "storage/event_studies" / PM / "v2_observations.parquet"
    provenance[str(p.relative_to(ROOT))] = sha(p)
    baseline = pd.read_parquet(p, columns=cols)
    assert (
        baseline.date.between("2020-01-01", "2023-12-31").all()
        and baseline.timestamp_utc.is_unique
    )
    baseline.to_parquet(P / "baseline_observations.parquet", index=False)
    grouped = {}
    source = []
    recon = []
    fields = [
        "event_id",
        "root_event_id",
        "interaction_type",
        "direction",
        "approach_side",
        "timestamp_utc",
        "date",
        "level_id",
        "level_type",
        "level_price",
        "level_available_at",
        "touch_number",
        "high",
        "low",
        "close",
        "open",
        "component_event_ids",
    ]
    for kind, d in zip(LEVELS, DIRS):
        p = MASTER / d / "events.parquet"
        provenance[str(p.relative_to(ROOT))] = sha(p)
        for batch in pq.ParquetFile(p).iter_batches(
            columns=["payload"], batch_size=512
        ):
            for raw in batch.to_pylist():
                full = json.loads(raw["payload"])
                e = {k: full.get(k) for k in fields}
                assert (
                    e["level_type"] == kind and "2020-01-01" <= e["date"] < "2024-01-01"
                )
                grouped.setdefault(pd.Timestamp(e["timestamp_utc"]), []).append(e)
                source.append(e)
        a = [e for e in source if e["level_type"] == kind]
        assert len({e["event_id"] for e in a}) == len(a)
        recon.append(
            dict(
                level=kind,
                source_events=len(a),
                study_id=PM if kind in ["PMH", "PML"] else OLD,
                source_hash=provenance[str(p.relative_to(ROOT))],
                reused_exactly=True,
            )
        )
    return cfg, provenance, bars, sessions, baseline, grouped, source, recon


def main():
    P.mkdir(exist_ok=True, parents=True)
    protocol = json.loads((P / "protocol.json").read_text())
    assert (
        sha(ROOT / "docs/EIGHT_LEVEL_REACTION_ENTRY_STUDY_V1.md")
        == protocol["specification_sha256"]
    )
    cfg, provenance, bars, sessions, base, grouped, source, recon = load()
    contexts = {
        pd.Timestamp(r.timestamp_utc): dict(
            atr14=None if pd.isna(r.atr14) else float(r.atr14),
            volatility_bucket=r.volatility_bucket,
            time_bucket=r.time_bucket,
            atr_regime=r.atr_regime,
        )
        for r in base.itertuples(index=False)
    }
    opening = Opening15(sessions)
    det = EventDetector(SessionConfig())
    seq = Sequences()
    entries = Entries()
    level = LevelEngine(SessionConfig("00:00", "09:30"), sessions)
    result = []
    coverage = {}
    new = []
    quality = []
    for row in bars.itertuples(index=False):
        at = row.timestamp_utc
        now = at + FIVE
        day = str(at.tz_convert(NY).date())
        session = sessions.get(day)
        known = opening.active(at)
        opening.update(row)
        level.update(row)
        for l in [*level.active(now), *opening.active(now)]:
            coverage[(day, l.level_type)] = l
        extra = det.update(row, known, session)
        extra += seq.update(row, extra)
        if not session or not session[0] <= at < session[1]:
            entries.update(row, [], {}, None)
            continue
        current = [*grouped.get(now, []), *extra]
        if valid_bar(row):
            assert now in contexts
            ctx = contexts[now]
            for e in extra:
                new.append({**e, **ctx})
            result.extend(entries.update(row, current, ctx, session))
        else:
            entries.update(row, [], {}, session)
    source.extend(new)
    for kind in LEVELS[-2:]:
        recon.append(
            dict(
                level=kind,
                source_events=sum(e["level_type"] == kind for e in new),
                study_id="EIGHT_LEVEL_REACTION_ENTRY_V1",
                source_hash=digest([protocol["specification_sha256"], kind]),
                reused_exactly=False,
            )
        )
    for day, s in sessions.items():
        for kind in LEVELS:
            l = coverage.get((day, kind))
            quality.append(
                dict(
                    date=day,
                    level=kind,
                    available=l is not None,
                    price=float(l.price) if l else None,
                    availability=l.availability_timestamp if l else None,
                    source_date=l.source_date if l else None,
                    reason=(
                        "COMPLETE_SOURCE"
                        if l
                        else "MISSING_INCOMPLETE_REQUIRED_SOURCE_OR_PRIOR_SESSION"
                    ),
                )
            )
    df = pd.DataFrame(result).sort_values(
        ["timestamp_utc", "level_type", "entry_kind", "event_id"]
    )
    assert df.event_id.is_unique and df.date.between("2020-01-01", "2023-12-31").all()
    assert (
        pd.to_datetime(df.level_available_at, utc=True)
        <= pd.to_datetime(df.timestamp_utc, utc=True) - FIVE
    ).all()
    df.to_parquet(P / "entry_events.parquet", index=False)
    # Avoid mixed Arrow list/null types in original component IDs by canonical strings.
    src = pd.DataFrame(source)
    src["component_event_ids"] = src.component_event_ids.map(lambda x: json.dumps(x))
    src.to_parquet(P / "source_events.parquet", index=False)
    write("source_reconciliation.csv", pd.DataFrame(recon))
    write("level_coverage.csv", pd.DataFrame(quality))
    (P / "source_identity.json").write_text(
        json.dumps(
            dict(
                dataset=cfg["dataset_identity"],
                source_hashes=provenance,
                calendar=cfg["calendar"],
                protocol_hash=sha(P / "protocol.json"),
                rows_5m=len(bars),
            ),
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    print(
        "Causal entries:",
        len(df),
        df.groupby("level_type").size().to_dict(),
        flush=True,
    )


if __name__ == "__main__":
    main()
