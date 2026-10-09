"""Repeat both calculations; expose results only after exact artifact reconciliation."""

from pathlib import Path
import sys, json, subprocess, zipfile, time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.level_combination.run import P, sha


def artifacts():
    return {
        p.name: {"sha256": sha(p), "bytes": p.stat().st_size}
        for p in sorted(P.iterdir())
        if p.is_file()
        and p.suffix in [".csv", ".json", ".md", ".html"]
        and p.name not in ["reproducibility_manifest.json", "verification_runtime.json"]
    }


def regression():
    import pandas as pd

    old = ROOT / "work/downward-break-execution-feasibility-v1"
    m = json.loads((old / "reproducibility_manifest.json").read_text())
    path = old / "all_target_executions.csv"
    assert sha(path) == m["artifacts"][path.name]["sha256"]
    a = pd.read_csv(path, low_memory=False)
    a = a[a.stop == "BREAK_CANDLE_HIGH"].rename(columns={"event_id": "opportunity_id"})
    b = pd.read_csv(P / "all_executions.csv", low_memory=False)
    b = b[(b.policy == "IMMEDIATE") & (b.direction == "DOWN")]
    keys = ["opportunity_id", "ticks", "target_r"]
    cols = [
        "execution_status",
        "entry_price",
        "stop_price",
        "target_price",
        "risk_points",
        "exit_time_utc",
        "exit_reason",
        "exit_price",
        "gross_pnl_usd",
        "commission_usd",
        "net_pnl_usd",
        "result_r",
        "duration_minutes",
        "mfe_points",
        "mae_points",
        "mfe_r",
        "mae_r",
        "same_minute_stop_target_conflict",
    ]
    a = a.set_index(keys).sort_index()[cols]
    b = b.set_index(keys).sort_index()[cols]
    pd.testing.assert_frame_equal(
        a[["execution_status", "entry_price", "stop_price", "risk_points"]],
        b[["execution_status", "entry_price", "stop_price", "risk_points"]],
        check_dtype=False,
        check_exact=True,
    )
    completed = a.execution_status == "COMPLETED"
    pd.testing.assert_frame_equal(
        a[completed], b[completed], check_dtype=False, check_exact=True
    )
    assert len(a) == 11364 * 6
    (P / "prior_development_regression.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "exact_economic_rows": len(a),
                "prior_artifact_sha256": sha(path),
                "source": str(path.relative_to(ROOT)),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )


def main():
    regression()
    before = artifacts()
    started = time.monotonic()
    for script in ["run", "report"]:
        subprocess.run(
            [sys.executable, str(ROOT / f"scripts/level_combination/{script}.py")],
            cwd=ROOT,
            check=True,
        )
    regression()
    after = artifacts()
    assert before == after, "Rerun artifact drift"
    ver = json.loads((P / "execution_verification.json").read_text())
    # Trace stable tracked source identity separately from the generated artifacts.
    code = {
        str(p.relative_to(ROOT)): sha(p)
        for p in sorted((ROOT / "scripts/level_combination").glob("*.py"))
    }
    m = dict(
        status="PASS",
        segment="development",
        entry_records=ver["entry_records"],
        raw_events=ver["raw_events"],
        byte_identical_artifacts=len(before),
        source_hashes=ver["source_hashes"],
        code_hashes=code,
        native_independent_checks=ver["native_independent_checks"],
        artifacts=after,
    )
    # No self-referential hash or wall clock enters economic artifacts.
    (P / "reproducibility_manifest.json").write_text(
        json.dumps(m, sort_keys=True, indent=2) + "\n"
    )
    archive = P / "study_bundle.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name in [*sorted(after), "reproducibility_manifest.json"]:
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, (P / name).read_bytes())
    m["artifacts"][archive.name] = {
        "sha256": sha(archive),
        "bytes": archive.stat().st_size,
    }
    (P / "reproducibility_manifest.json").write_text(
        json.dumps(m, sort_keys=True, indent=2) + "\n"
    )
    (P / "verification_runtime.json").write_text(
        json.dumps(
            {
                "repeat_seconds": round(time.monotonic() - started, 3),
                "artifact_bytes": sum(
                    p.stat().st_size for p in P.iterdir() if p.is_file()
                ),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    print(
        "PASS",
        len(before),
        "byte-identical files; native checks",
        ver["native_independent_checks"],
        flush=True,
    )


if __name__ == "__main__":
    main()
