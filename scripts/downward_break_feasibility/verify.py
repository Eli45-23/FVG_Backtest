"""Repeat native diagnostics and summaries; freeze exact local artifact identities."""

import sys, json, time, subprocess, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.downward_break_feasibility.run import P, sha

EXCLUDE = {
    "reproducibility_manifest.json",
    "evidence_index.json",
    "verification_runtime.json",
}
LARGE = {
    "all_event_paths.csv",
    "all_target_executions.csv",
    "exact_raw_events.csv",
    "ambiguity_audit.csv",
}


def inventory():
    return {
        p.name: dict(sha256=sha(p), bytes=p.stat().st_size)
        for p in sorted(P.iterdir())
        if p.is_file()
        and p.suffix in {".csv", ".json", ".md", ".html"}
        and p.name not in EXCLUDE
    }


def save(name, value):
    (P / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def main():
    before = inventory()
    assert "study.html" in before and "execution_verification.json" in before
    started = time.monotonic()
    runtime = {}
    for stage in ["run", "report"]:
        at = time.monotonic()
        subprocess.run(
            [
                sys.executable,
                str(ROOT / f"scripts/downward_break_feasibility/{stage}.py"),
            ],
            check=True,
            cwd=ROOT,
        )
        runtime[stage] = round(time.monotonic() - at, 3)
    after = inventory()
    assert before == after, {
        k: (before.get(k), after.get(k))
        for k in set(before) | set(after)
        if before.get(k) != after.get(k)
    }
    v = json.loads((P / "execution_verification.json").read_text())
    for name, h in v["source_hashes_verified"].items():
        assert sha(ROOT / name) == h
    code = {
        str(p.relative_to(ROOT)): sha(p)
        for p in sorted((ROOT / "engine").rglob("*.py"))
    }
    for folder in [
        "scripts/downward_break_feasibility",
        "scripts/pml_feasibility",
        "scripts/swing_low_feasibility",
    ]:
        for p in sorted((ROOT / folder).glob("*.py")):
            code[str(p.relative_to(ROOT))] = sha(p)
    for name in [
        "scripts/downward_break_feasibility/viewer.html",
        "outputs/cont_a_backtest.py",
        "scripts/zone_reaction_backtest/report.py",
    ]:
        code[name] = sha(ROOT / name)
    save(
        "evidence_index.json",
        dict(
            segment="development",
            root=str(P),
            complete_unsampled_artifacts=after,
            source_hashes=v["source_hashes_verified"],
            code_hashes=code,
            note="All raw rows retained locally. Large event/path/fill CSVs are linked by exact hash instead of being sampled into the report bundle.",
        ),
    )
    with zipfile.ZipFile(
        P / "study_bundle.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9
    ) as z:
        for name in sorted(
            [k for k in after if k not in LARGE] + ["evidence_index.json"]
        ):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, (P / name).read_bytes())
    artifacts = dict(after)
    for name in ["evidence_index.json", "study_bundle.zip"]:
        artifacts[name] = dict(sha256=sha(P / name), bytes=(P / name).stat().st_size)
    save(
        "reproducibility_manifest.json",
        dict(
            status="PASS",
            segment="development",
            entry_records=v["raw_events"],
            deterministic_rerun=True,
            byte_identical_artifacts=len(after),
            native_independent_checks=v["native_independent_checks"],
            production_execution_changed=False,
            validation_oos_outcomes_read=False,
            artifacts=artifacts,
            code_hashes=code,
        ),
    )
    save(
        "verification_runtime.json",
        dict(
            repeat_stage_seconds=runtime,
            total_repeat_seconds=round(time.monotonic() - started, 3),
        ),
    )
    print("PASS: byte-identical artifacts", len(after), flush=True)


if __name__ == "__main__":
    main()
