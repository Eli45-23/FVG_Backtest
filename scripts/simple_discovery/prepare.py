"""Freeze inputs without altering an existing experiment identity."""

import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.simple_discovery.run import P, sha


def main():
    P.mkdir(parents=True, exist_ok=True)
    files = ["docs/SIMPLE_STRATEGY_DISCOVERY_V1.md", "scripts/simple_discovery/core.py"]
    v = dict(
        status="PREREGISTERED_DEVELOPMENT_ONLY",
        hashes={s: sha(ROOT / s) for s in files},
        margin_source_access_date="2026-10-10",
        official_intraday_snapshot=166.71,
        official_initial_snapshot=4763,
        historical_margin_verified=False,
        primary_assumed_margin=200,
        primary_family_size=3,
        seed=1729,
    )
    p = P / "protocol.json"
    if p.exists():
        assert json.loads(p.read_text()) == v, "Do not overwrite frozen rules"
    else:
        p.write_text(json.dumps(v, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
