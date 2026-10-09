"""Frozen PDH Development rerun with user-supplied fees; never visits reserved segments.

Usage: work/.venv/bin/python scripts/pdh_fee_corrected_development.py run|repeat|report
Existing immutable runs are resumed, never replaced. This is not a strategy optimizer.
"""

from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time
from decimal import Decimal as D

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
P = ROOT / "work/pdh-failed-break-short-v1-fee-corrected"
OLD = ROOT / "work/pdh-failed-break-short-v1-development"
VERSION = "a3dc35456fd7416abfa0df53f77fbb6e"
FEE = {
    "provenance": "actual observed Webull MNQ fee supplied by user",
    "commission_per_side_usd": "0.25",
    "exchange_per_side_usd": "0.35",
    "clearing_per_side_usd": "0.12",
    "nfa_per_side_usd": "0.01",
    "all_in_per_side_per_micro_usd": "0.73",
    "round_trip_per_micro_usd": "1.46",
}


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    from engine.canonical import dumps

    Path(path).write_text(dumps(value))


def identity():
    from backend.app import db

    with db.Session() as s:
        v = s.get(db.Version, VERSION)
        assert v is not None
        source = v.source
        spec = read(OLD / "frozen_strategy_specification.json")
        assert (
            v.source_hash
            == spec["source_hash"]
            == hashlib.sha256(source.encode()).hexdigest()
        )
        assert source == (OLD / "saved_strategy.py").read_text()
        assert spec["version_id"] == VERSION
    return source, spec


def preflight(source):
    # Reuse the exact reviewed reconciliation implementation, with output isolation
    # and the immutable database source (not a mutable built-in source file).
    text = (OLD / "reconcile.py").read_text()
    text = text.replace("ROOT=Path(__file__).resolve().parents[2]", "ROOT=TASK_ROOT")
    text = text.replace("P=Path(__file__).resolve().parent", "P=TASK_OUTPUT")
    text = text.replace(
        "source=(ROOT/'strategies/builtins/pdh_failed_break_short_v1.py').read_text()",
        "source=TASK_SOURCE",
    )
    exec(
        compile(text, str(OLD / "reconcile.py"), "exec"),
        {
            "__file__": str(OLD / "reconcile.py"),
            "TASK_ROOT": ROOT,
            "TASK_OUTPUT": P,
            "TASK_SOURCE": source,
        },
    )
    gate = read(P / "reconciliation_gate.json")
    assert gate == read(OLD / "reconciliation_gate.json")
    return gate


def run():
    from backend.app import db, services

    P.mkdir(parents=True, exist_ok=True)
    source, spec = identity()
    gate = preflight(source)
    snapshot = P / "frozen_strategy_identity.json"
    if not snapshot.exists():
        protected = {
            str(p.relative_to(ROOT)): sha(p) for p in OLD.rglob("*") if p.is_file()
        }
        save(P / "preserved_prior_artifacts.json", protected)
        save(
            snapshot,
            {
                **spec,
                "previous_specification_sha256": sha(
                    OLD / "frozen_strategy_specification.json"
                ),
                "fee_schedule": FEE,
                "scenarios": [
                    dict(slippage_ticks=t, commission="0.73") for t in range(3)
                ],
                "previous_engine_version": spec["engine_version"],
                "engine_version": services.engine_version(),
                "settings": {**spec["settings"], "commission": "0.73"},
                "commission_status": "USER_SUPPLIED_ACTUAL_ALL_IN_FEE",
            },
        )
    info = (
        read(P / "lab_runs.json")
        if (P / "lab_runs.json").exists()
        else {"version_id": VERSION, "runs": []}
    )
    for ticks in range(3):
        if any(x["slippage_ticks"] == ticks for x in info["runs"]):
            continue
        settings = {**spec["settings"], "commission": "0.73", "slippage": ticks}
        rid = services.enqueue(
            VERSION,
            {},
            settings,
            f"PDH Failed Break Short v1 — actual Webull fee — {ticks} tick"
            + (" PRIMARY" if ticks == 1 else ""),
            notes="DEVELOPMENT_ONLY_NOT_VALIDATED. User supplied all-in fee $0.73/side. Frozen signal, stop, 1R and one micro. No reserved data access authorized.",
            segment="development",
            extra_config={
                "status_label": "DEVELOPMENT_ONLY_NOT_VALIDATED",
                "actual_observed_fee_schedule": FEE,
                "candidate_identity_fingerprint": gate[
                    "candidate_identity_fingerprint"
                ],
                "frozen_strategy_version_id": VERSION,
                "daily_later_signal_reason": "DAILY_LIMIT_REACHED",
                "fee_corrected_specification_sha256": sha(snapshot),
            },
        )
        info["runs"].append({"slippage_ticks": ticks, "run_id": rid})
        save(P / "lab_runs.json", info)
        print("Queued", ticks, rid, flush=True)
    last = {}
    while True:
        states = []
        with db.Session() as s:
            for item in info["runs"]:
                r = s.get(db.Run, item["run_id"])
                states.append(r.status)
                state = (r.status, r.progress, r.error)
                if last.get(r.id) != state:
                    print(item["slippage_ticks"], state, flush=True)
                    last[r.id] = state
        if all(x in ("completed", "failed", "cancelled") for x in states):
            break
        time.sleep(5)
    assert states == ["completed"] * 3, states


def repeat():
    # Sequential independent fresh processes; no additional persisted runs.
    for item in read(P / "lab_runs.json")["runs"]:
        folder = P / f"repeat_{item['slippage_ticks']}"
        folder.mkdir(exist_ok=True)
        request = ROOT / "storage/artifacts" / item["run_id"] / "request.json"
        with (folder / "worker.log").open("w") as log:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "backend.app.worker",
                    str(request),
                    str(folder / "result.json"),
                    "run",
                ],
                cwd=ROOT,
                stdout=log,
                stderr=log,
                check=True,
                timeout=3600,
            )
        original = request.parent / "result.json"
        assert (
            original.read_bytes() == (folder / "result.json").read_bytes()
        ), "Nonidentical engine output"
        print("Byte-identical worker repeat", item["slippage_ticks"], flush=True)


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "run":
        run()
    elif action == "repeat":
        repeat()
    elif action == "report":
        from pdh_fee_corrected_report import report

        report()
    else:
        raise ValueError(action)
