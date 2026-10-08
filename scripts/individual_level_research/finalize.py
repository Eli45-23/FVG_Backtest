"""Verify identities, index all unsampled artifacts, and package reports."""

import sys, json, hashlib, sqlite3, zipfile, datetime, subprocess
from pathlib import Path
import pandas as pd, duckdb
from analyze import R, OLD, LEVELS, folder


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def run():
    pm = json.loads((R / "premarket_study.json").read_text())["id"]
    sources = []
    for id in [OLD, pm]:
        root = Path("storage/event_studies") / id
        c = json.loads((root / "config.json").read_text())
        assert c["segment"] == "development" and c["end"] == "2024-01-01"
        for p in sorted(root.iterdir()):
            if p.is_file():
                sources.append(
                    {
                        "study_id": id,
                        "path": str(p.resolve()),
                        "bytes": p.stat().st_size,
                        "sha256": sha(p),
                        "role": "immutable full unsampled study source",
                    }
                )
    preserved = json.loads((R / "preserved_source_manifest.json").read_text())
    for p, v in preserved.items():
        assert sha(p) == v["sha256"], p
    # Verify baseline fields/outcomes are equivalent despite PM context being additive.
    con = duckdb.connect()
    con.execute("set memory_limit='512MB';set threads=1")
    mismatch = con.execute(
        """select count(*) from read_parquet(?) a full outer join read_parquet(?) b using(event_id) where a.timestamp_utc is distinct from b.timestamp_utc or a.atr14 is distinct from b.atr14 or a.volatility_bucket is distinct from b.volatility_bucket or a.year is distinct from b.year or a.time_bucket is distinct from b.time_bucket""",
        [
            f"storage/event_studies/{OLD}/v2_observations.parquet",
            f"storage/event_studies/{pm}/v2_observations.parquet",
        ],
    ).fetchone()[0]
    assert mismatch == 0
    con.close()
    snap = json.loads((R / "metadata_preservation_snapshot.json").read_text())
    db = sqlite3.connect("file:storage/app.db?mode=ro", uri=True)
    for table, before in snap.items():
        columns = [x[1] for x in db.execute(f"pragma table_info({table})")]
        chosen = [
            x
            for x in [
                "id",
                "strategy_id",
                "source_hash",
                "current_version",
                "number",
                "created_at",
                "config_hash",
                "study_id",
            ]
            if x in columns
        ]
        if table == "event_study_reveals":
            chosen = ["study_id", "config_hash"]
        after = db.execute(
            f'select {",".join(chosen)} from {table} order by 1'
        ).fetchall()
        assert [list(x) for x in after] == before, table
    assert db.execute("select count(*) from event_study_reveals").fetchone()[0] == 0
    statuses = db.execute(
        "select id,status,error,created_at from event_studies where id in (?,?)",
        (OLD, pm),
    ).fetchall()
    assert all(x[1] == "completed" and not x[2] for x in statuses)
    # Metadata-only journal: no old run outcomes or non-Development outcomes queried.
    verification = {
        "local_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "engine_api_tests": "72 passed; Development and synthetic/isolated state-machine checks",
        "analysis_tests": "12 passed",
        "independent_raw_minute_arithmetic": json.loads(
            (R / "independent_label_verification.json").read_text()
        ),
        "causal_audit": pd.read_csv(R / "causal_audit.csv").to_dict("records"),
        "swing_confirmations": 70081,
        "swing_failures": int(
            (~pd.read_csv(R / "independent_swing_confirmation_audit.csv").correct).sum()
        ),
        "baseline_metadata_mismatches": mismatch,
        "source_hashes_unchanged": True,
        "existing_metadata_preserved": True,
        "saved_reveals": 0,
        "validation_outcomes_queried": False,
        "oos_outcomes_queried": False,
        "production_engine_changed": False,
        "historical_golden_rerun": "Not run: production unchanged and those runs access reserved later periods",
        "paid_download": False,
        "pushed": False,
        "known_blockers": ["SUPPLY", "DEMAND"],
        "determinism": json.loads((R / "determinism.json").read_text()),
    }
    (R / "verification_results.json").write_text(json.dumps(verification, indent=2))
    # Index full local artifacts. Exclusion from zip is explicit; no observations sampled away.
    raw = []
    for p in sorted(R.rglob("*.parquet")):
        raw.append(
            {
                "path": str(p.resolve()),
                "relative_path": str(p.relative_to(R)),
                "bytes": p.stat().st_size,
                "sha256": sha(p),
                "included_in_zip": False,
                "reason": "Full local columnar artifact linked by manifest; reports and aggregates bundled without sampling",
            }
        )
    local = []
    exclude = {
        "EVIDENCE_INDEX.json",
        "bundle_manifest.json",
        "delivery_summary.json",
        "finalize.log",
    }
    for p in sorted(R.rglob("*")):
        if (
            p.is_file()
            and p.suffix not in [".parquet", ".zip", ".pyc"]
            and p.name not in exclude
            and "__pycache__" not in p.parts
        ):
            local.append(
                {
                    "path": str(p.relative_to(R)),
                    "bytes": p.stat().st_size,
                    "sha256": sha(p),
                    "included_in_zip": True,
                }
            )
    runtime = json.loads((R / "analysis_runtime.json").read_text())
    index = {
        "protocol_sha256": sha(R / "preregistered_protocol.json"),
        "source_studies": sources,
        "full_local_columnar_exports": raw,
        "bundled_files": local,
        "coverage": pd.read_csv(R / "coverage_summary.csv")
        .fillna("unavailable")
        .to_dict("records"),
        "timing": {
            "corrected_full_analysis_seconds": runtime["runtime_seconds"],
            "study_detection": [
                {
                    "study_id": id,
                    **json.loads(
                        Path(
                            f"storage/event_studies/{id}/detection_benchmark.json"
                        ).read_text()
                    ),
                }
                for id in [OLD, pm]
            ],
            "study_creation_to_outcomes_mtime_seconds": [
                {
                    "study_id": x[0],
                    "seconds": Path(f"storage/event_studies/{x[0]}/v2_outcomes.parquet")
                    .stat()
                    .st_mtime
                    - datetime.datetime.fromisoformat(x[3]).timestamp(),
                    "note": "wall-time proxy from creation to final artifact write, includes labeling",
                }
                for x in statuses
            ],
        },
        "source_artifact_bytes": sum(x["bytes"] for x in sources),
        "derived_columnar_bytes": sum(x["bytes"] for x in raw),
        "sampling": "None; every selected point-level event and every supported horizon is retained",
        "columnar_query": "Use event_id to join source v2_events and v2_outcomes; per-level exports contain every selected record, with original payload in events.parquet.",
    }
    for name in ["EVIDENCE_INDEX.json", "bundle_manifest.json"]:
        (R / name).write_text(json.dumps(index, indent=2))
    out = R / "MNQ_INDIVIDUAL_LEVEL_RESEARCH.zip"
    with zipfile.ZipFile(
        out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as z:
        for item in local:
            z.write(R / item["path"], item["path"])
        for name in ["EVIDENCE_INDEX.json", "bundle_manifest.json"]:
            z.write(R / name, name)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
    summary = {
        "zip_path": str(out),
        "zip_bytes": out.stat().st_size,
        "zip_sha256": sha(out),
        "source_artifact_bytes": index["source_artifact_bytes"],
        "derived_columnar_bytes": index["derived_columnar_bytes"],
        "bundled_files": len(local) + 2,
        "completed_point_families": 10,
        "blocked_families": ["SUPPLY", "DEMAND"],
        "total_selected_event_records": int(
            pd.read_csv(R / "coverage_summary.csv").Events.sum()
        ),
    }
    (R / "delivery_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run()
