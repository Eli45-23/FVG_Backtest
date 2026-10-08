import json, sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from backend.app.event_studies import create, StudyBody, pool, gate, studies

R = Path("work/mnq-individual-level-master-research")
p = R / "premarket_study.json"
if p.exists():
    raise SystemExit("Already created; inspect status rather than duplicate")
c = json.loads(
    Path(
        "storage/event_studies/5cb7fab0d4e7414792a3fbe59ded4999/config.json"
    ).read_text()
)
body = StudyBody(
    name="Individual Level Master — Midnight PMH/PML Development v1",
    research_version=2,
    start="2020-01-01",
    end="2024-01-01",
    session={**c["session"], "premarket_start": "00:00", "premarket_end": "09:30"},
    research_settings=c["research_settings"],
)
from engine.research.study import snapshot
from engine.canonical import digest

expected_hash = digest(snapshot(body.model_dump(exclude={"name"})))
equivalent = [
    x
    for x in studies()
    if x["config_hash"] == expected_hash and x["status"] == "completed"
]
r = {"id": equivalent[0]["id"]} if equivalent else create(body)
p.write_text(json.dumps(r, indent=2))
print(r, flush=True)
pool.shutdown(wait=True)
print(gate(r["id"])["status"], flush=True)
