import copy, json, sqlite3, subprocess, os, shutil
from pathlib import Path
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from test_api import client, post, draft, wait
from backend.app import db, services
from backend.app.experiments import validate_ranges, sweep_guard
from engine.canonical import digest
from engine.legacy import ROOT

RANGES = {
    "development": {"start": "2024-02-05", "end": "2024-02-06"},
    "validation": {"start": "2024-02-06", "end": "2024-02-07"},
    "out-of-sample": {"start": "2024-02-07", "end": "2024-02-08"},
}


def make(client):
    st = draft(client)
    split = post(
        client, "/api/research-splits", {"name": "Test split", "ranges": RANGES}
    )
    exp = post(
        client,
        "/api/experiments",
        {
            "name": "Test experiment",
            "research_split_id": split["id"],
            "strategy_version_id": st["version_id"],
            "parameters": {"target_r": 3},
        },
    )
    return st, split, exp


@pytest.fixture(scope="module")
def frozen(client):
    st, sp, e = make(client)
    for segment in ["development", "validation"]:
        rid = post(client, f"/api/experiments/{e['id']}/run", {"segment": segment})[
            "id"
        ]
        assert wait(client, rid)["status"] == "completed"
    e = post(client, f"/api/experiments/{e['id']}/freeze", {})
    return st, sp, e


def test_valid_split():
    assert validate_ranges(RANGES) == []


@pytest.mark.parametrize(
    "segment,field,value",
    [
        ("validation", "start", "2024-02-05"),
        ("development", "end", "2024-02-04"),
        ("out-of-sample", "end", "2027-01-01"),
        ("validation", "start", "2024-02-08"),
    ],
)
def test_invalid_splits(segment, field, value):
    r = copy.deepcopy(RANGES)
    r[segment][field] = value
    with pytest.raises(ValueError):
        validate_ranges(r)


def test_gaps_allowed():
    r = copy.deepcopy(RANGES)
    r["validation"]["start"] = "2024-02-06"
    r["development"]["end"] = "2024-02-05"
    r["development"]["start"] = "2024-02-04"
    assert validate_ranges(r)


def test_snapshot_exact_version_inputs(client):
    st, sp, e = make(client)
    assert e["config"]["parameters"]["target_r"] == 3
    assert (
        e["config"]["source_hash"] == st["source_hash"]
        and e["strategy_version_id"] == st["version_id"]
    )
    assert e["snapshot_hash"] == digest(e["config"])


def test_no_oos_before_freeze(client):
    st, sp, e = make(client)
    assert (
        client.post(
            f"/api/experiments/{e['id']}/run", json={"segment": "out-of-sample"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/backtests",
            json={"strategy_version_id": st["version_id"], "segment": "out-of-sample"},
        ).status_code
        == 422
    )
    r = client.get("/api/experiments/" + e["id"]).json()
    assert r["oos_status"] == "SEALED" and "out-of-sample" not in r["runs"]


def test_freeze_requires_reviews(client):
    st, sp, e = make(client)
    assert client.post(f"/api/experiments/{e['id']}/freeze", json={}).status_code == 422
    assert (
        client.post(
            f"/api/experiments/{e['id']}/run", json={"segment": "validation"}
        ).status_code
        == 422
    )


def test_freeze_snapshot_immutable(frozen, client):
    st, sp, e = frozen
    assert e["frozen_at"]
    client.put(
        "/api/strategies/" + st["id"],
        json={"name": st["name"], "source": st["source"] + "\n# newer"},
    )
    now = client.get("/api/experiments/" + e["id"]).json()
    assert now["config"] == e["config"] and now["snapshot_hash"] == e["snapshot_hash"]
    with pytest.raises(IntegrityError):
        with db.Session.begin() as s:
            s.execute(
                text("UPDATE experiment_snapshots SET config = :v WHERE id = :id"),
                {"v": "{}", "id": e["id"]},
            )


def test_official_oos_and_reveal(frozen, client):
    st, sp, e = frozen
    before = client.get("/api/experiments/" + e["id"]).json()
    assert before["oos_revealed_at"] is None
    rid = post(client, f"/api/experiments/{e['id']}/run", {"segment": "out-of-sample"})[
        "id"
    ]
    run = wait(client, rid)
    assert run["status"] == "completed"
    assert run["config"]["experiment_snapshot_id"] == e["id"]
    assert run["config"]["parameters"] == e["config"]["parameters"]
    assert run["config"]["settings"]["start"] == RANGES["out-of-sample"]["start"]
    after = client.get("/api/experiments/" + e["id"]).json()
    assert after["oos_revealed_at"] and after["oos_run_at"]
    assert after["oos_status"] == "REVEALED"
    assert (
        post(client, f"/api/experiments/{e['id']}/run", {"segment": "out-of-sample"})[
            "id"
        ]
        == rid
    )
    assert client.get(f"/api/experiments/{e['id']}/combined").status_code == 200


def test_development_sweep(frozen, client):
    st, sp, e = frozen
    sw = post(
        client,
        "/api/sweeps",
        {
            "name": "Dev only",
            "run": {
                "strategy_version_id": st["version_id"],
                "research_split_id": sp["id"],
                "settings": RANGES["development"],
            },
            "parameter": "target_r",
            "values": [2],
        },
    )
    row = next(x for x in client.get("/api/sweeps").json() if x["id"] == sw["id"])
    assert wait(client, row["children"][0]["id"])["status"] == "completed"


def test_oos_sweep_rejected(frozen, client):
    st, sp, e = frozen
    assert (
        client.post(
            "/api/sweeps",
            json={
                "run": {
                    "strategy_version_id": st["version_id"],
                    "research_split_id": sp["id"],
                    "segment": "out-of-sample",
                    "settings": RANGES["out-of-sample"],
                },
                "parameter": "target_r",
                "values": [2],
            },
        ).status_code
        == 422
    )
    with pytest.raises(ValueError, match="overlaps frozen"):
        sweep_guard(RANGES["out-of-sample"], "development")


def test_validation_advanced_override(frozen):
    st, sp, e = frozen
    with pytest.raises(ValueError, match="override"):
        sweep_guard(RANGES["validation"], "validation", sp["id"])
    sweep_guard(RANGES["validation"], "validation", sp["id"], True)


def test_split_bounds_on_sweep(frozen):
    st, sp, e = frozen
    with pytest.raises(ValueError, match="inside"):
        sweep_guard(RANGES["out-of-sample"], "development", sp["id"])


def test_comparison_split_and_segment_warnings(frozen, client):
    e = client.get("/api/experiments/" + frozen[2]["id"]).json()
    ids = [e["runs"][k]["id"] for k in ["development", "validation"]]
    assert any(
        "segment" in w for w in post(client, "/api/compare", {"ids": ids})["warnings"]
    )
    st, sp, new = make(client)
    rid = post(client, f"/api/experiments/{new['id']}/run", {"segment": "development"})[
        "id"
    ]
    assert wait(client, rid)["status"] == "completed"
    assert any(
        "research_split_id" in w
        for w in post(client, "/api/compare", {"ids": [ids[0], rid]})["warnings"]
    )


def test_frozen_identity_mismatch(frozen):
    c = frozen[2]["config"]
    with pytest.raises(ValueError, match="engine_version"):
        services.enqueue(
            c["strategy_version_id"],
            c["parameters"],
            {**c["settings"], **RANGES["development"]},
            "Wrong identity",
            expected_identity={**c, "engine_version": "bad"},
        )


def test_migrate_real_v1_database_preserves_rows(tmp_path):
    old = ROOT / "work/v11-before.db"
    if not old.exists():
        pytest.skip("Local v1 migration snapshot unavailable")
    store = tmp_path / "migration"
    store.mkdir()
    shutil.copy2(old, store / "app.db")
    tables = [
        "strategies",
        "strategy_versions",
        "variants",
        "runs",
        "run_metrics",
        "run_artifacts",
        "sweeps",
        "sweep_runs",
    ]

    def rows():
        with sqlite3.connect(store / "app.db") as c:
            return {
                t: c.execute("select * from " + t + " order by 1").fetchall()
                for t in tables
            }

    before = rows()
    p = subprocess.run(
        [
            str(ROOT / "work/.venv/bin/python"),
            "-c",
            "from backend.app import db; db.migrate(); db.migrate()",
        ],
        cwd=ROOT,
        env={**os.environ, "LAB_STORAGE": str(store)},
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stderr
    assert rows() == before
    with sqlite3.connect(store / "app.db") as c:
        assert (
            c.execute("select max(version) from schema_migrations").fetchone()[0] == 3
        )
        for (path,) in c.execute("select path from run_artifacts where kind='result'"):
            assert json.loads(Path(path).read_text())["summary"]["overall"][
                "trades"
            ] in (263, 235, 170)
