import json, hashlib, subprocess, sys
from analyze import R

names = [
    "all_levels_primary_outcomes.csv",
    "all_levels_statistical_evidence.csv",
    "all_levels_yearly_stability.csv",
    "all_levels_baseline_effects.csv",
    "MASTER_LEVEL_RESEARCH_REPORT.md",
]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = {x: sha(R / x) for x in names}
for script in ["consolidate.py", "report.py"]:
    subprocess.run(
        [sys.executable, str(R / script)], check=True, stdout=subprocess.DEVNULL
    )
after = {x: sha(R / x) for x in names}
assert before == after, {
    k: (before[k], after[k]) for k in names if before[k] != after[k]
}
(R / "determinism.json").write_text(
    json.dumps(
        {
            "byte_identical_key_summary_rerun": True,
            "files": after,
            "scope": "Full aggregation/correction/report regeneration from the same complete outcome exports; all selected events retained. Independent source arithmetic and raw-minute label checks recorded separately.",
        },
        indent=2,
    )
)
print("five key outputs byte-identical")
