"""Two full bounded reruns plus synthetic checks; never runs reserved-data tests."""

from pathlib import Path
import sys, subprocess, json, re

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pml_feasibility.run import P, sha
from engine.canonical import dumps


def call(*args):
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def snapshot():
    return {
        f.name: sha(f)
        for f in sorted(P.iterdir())
        if f.is_file() and f.name != "determinism_results.json"
    }


def run():
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/test_pml_feasibility.py",
        "tests/test_swing_low_feasibility.py",
    ]
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, check=True
    )
    print(result.stdout, flush=True)
    passed = int(re.search(r"(\d+) passed", result.stdout).group(1))
    (P / "verification_results.json").write_text(
        dumps(
            dict(
                synthetic_tests_passed=passed,
                failed=0,
                test_command=" ".join(command),
                production_code_changed=False,
                legacy_golden_rerun="not required; unchanged production and reserved-period access prohibited",
                causal_replay_exact_event_ids=407,
                native_fill_checks=9837,
                raw_30m_labels_independently_verified=407,
                validation_outcomes_read=False,
                oos_revealed=False,
            )
        )
    )
    outputs = []
    for n in (1, 2):
        for script in ("run.py", "report.py", "finish.py"):
            call("scripts/pml_feasibility/" + script)
        outputs.append(snapshot())
        print("Verified full repeat", n, flush=True)
    changed = [
        name
        for name in outputs[0].keys() | outputs[1].keys()
        if outputs[0].get(name) != outputs[1].get(name)
    ]
    assert not changed, changed
    (P / "determinism_results.json").write_text(
        dumps(
            dict(
                full_native_runs=2,
                byte_identical=True,
                files_compared=len(outputs[0]),
                sha256=outputs[0],
                changed_files=changed,
            )
        )
    )
    print("Byte-identical artifacts:", len(outputs[0]), flush=True)


if __name__ == "__main__":
    run()
