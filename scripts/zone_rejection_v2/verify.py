"""Two full Development-only reruns; immutable baseline artifacts are read-only."""

import sys, json, subprocess, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.zone_rejection_v2.run import P, sha


def snapshot():
    return {
        p.name: sha(p)
        for p in sorted(P.iterdir())
        if p.suffix in {".csv", ".json", ".md"}
        and p.name != "reproducibility_manifest.json"
    }


def main():
    initial = time.monotonic()
    first = None
    for i in range(2):
        subprocess.run(
            [sys.executable, "scripts/zone_rejection_v2/run.py"],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            [sys.executable, "-m", "scripts.zone_rejection_v2.report"],
            cwd=ROOT,
            check=True,
        )
        current = snapshot()
        if first is not None:
            assert first == current, "Deterministic artifacts differ"
        first = current
    code = [
        *sorted((ROOT / "scripts/zone_rejection_v2").glob("*.py")),
        ROOT / "tests/test_zone_rejection_v2.py",
        ROOT / "engine/zone_v2/acceptance.py",
        ROOT / "engine/zone_v2/provider.py",
        ROOT / "engine/partial_execution.py",
    ]
    manifest = dict(
        status="PASS",
        repeat_count=2,
        byte_identical_artifacts=first,
        code_hashes={str(p.relative_to(ROOT)): sha(p) for p in code},
        runtime_seconds=round(time.monotonic() - initial, 3),
        validation_oos_outcomes_read=False,
    )
    (P / "reproducibility_manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    )
    print("PASS: two byte-identical full Development reruns", flush=True)


if __name__ == "__main__":
    main()
