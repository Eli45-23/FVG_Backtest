"""Repeat every study stage, require byte identity, and publish a hashed local bundle.

Run after detect/label/analyze/qa/report have produced the initial complete study.
No database writes, downloads, strategy execution or reserved outcome access.
"""
import sys, json, time, subprocess, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.eight_level_study.detect import P, sha

EXCLUDE = {
    "reproducibility_manifest.json", "evidence_index.json", "study_bundle.zip",
    "verification_runtime.json", "browser_verification.json",
}

def inventory():
    return {
        p.relative_to(P).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size}
        for p in sorted(P.rglob("*"))
        if p.is_file() and p.suffix in {".json", ".csv", ".parquet", ".md", ".html", ".svg"}
        and p.name not in EXCLUDE
    }

def save(name, value):
    (P / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")

def main():
    before = inventory()
    assert "quality_verification.json" in before and "study.html" in before
    assert json.loads((P / "quality_verification.json").read_text())["status"] == "PASS"
    started = time.monotonic()
    timings = {}
    for stage in ["detect", "label", "analyze", "qa", "report"]:
        at = time.monotonic()
        subprocess.run([sys.executable, str(ROOT / f"scripts/eight_level_study/{stage}.py")], check=True, cwd=ROOT)
        timings[stage] = round(time.monotonic() - at, 3)
    after = inventory()
    assert before == after, {k: (before.get(k), after.get(k)) for k in set(before) | set(after) if before.get(k) != after.get(k)}
    identity = json.loads((P / "source_identity.json").read_text())
    for name, expected in identity["source_hashes"].items():
        assert sha(ROOT / name) == expected, name
    code = {
        p.relative_to(ROOT).as_posix(): sha(p)
        for folder in [ROOT / "scripts/eight_level_study", ROOT / "engine/research"]
        for p in sorted(folder.glob("*.py"))
    }
    code["scripts/eight_level_study/viewer.html"] = sha(ROOT / "scripts/eight_level_study/viewer.html")
    index = dict(
        study="EIGHT_LEVEL_REACTION_ENTRY_V1", segment="development",
        root=str(P), complete_unsampled_artifacts=after,
        source_hashes=identity["source_hashes"], code_hashes=code,
        note="ZIP contains all reports and aggregate tables. Full Parquet observations/outcomes remain at the listed local paths, not sampled. No database study was created or modified.",
    )
    save("evidence_index.json", index)
    # Fixed archive timestamps and permissions make the bundle reproducible.
    with zipfile.ZipFile(P / "study_bundle.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in sorted([k for k in after if not k.endswith(".parquet")] + ["evidence_index.json"]):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, (P / name).read_bytes())
    artifacts = dict(after)
    for name in ["evidence_index.json", "study_bundle.zip"]:
        artifacts[name] = dict(sha256=sha(P / name), bytes=(P / name).stat().st_size)
    save("reproducibility_manifest.json", dict(
        status="PASS", segment="development", entry_records=json.loads((P / "quality_verification.json").read_text())["entry_records"],
        deterministic_rerun=True, byte_identical_artifacts=len(after),
        source_hashes_unchanged=True, validation_oos_outcomes_read=False,
        production_execution_changed=False, database_records_changed=False,
        code_hashes=code, artifacts=artifacts,
    ))
    save("verification_runtime.json", dict(repeat_stage_seconds=timings, total_repeat_seconds=round(time.monotonic()-started,3)))
    print("PASS: byte-identical artifacts", len(after), "seconds", round(time.monotonic()-started, 2), flush=True)

if __name__ == "__main__":
    main()
