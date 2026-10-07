import os, tempfile, time, json
from pathlib import Path

# Isolate the whole API test database from the user's workspace database.
TEST_STORAGE = tempfile.TemporaryDirectory(prefix="lab-tests-")
os.environ["LAB_STORAGE"] = TEST_STORAGE.name
from fastapi.testclient import TestClient
from sqlalchemy import select
from backend.app.main import app
from backend.app import db, services
from engine.legacy import ROOT
import pytest


@pytest.fixture(scope="module")
def client():
    with TestClient(app, base_url="http://127.0.0.1") as c:
        yield c


def post(c, url, p):
    r = c.post(url, json=p)
    assert r.status_code == 200, r.text
    return r.json()


def draft(c, source=None):
    return post(
        c,
        "/api/strategies",
        {
            "name": "Test strategy",
            "source": source or (ROOT / "strategies/builtins/template.py").read_text(),
        },
    )


def wait(c, rid, seconds=40):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        r = c.get("/api/backtests/" + rid).json()
        if r["status"] in ("completed", "failed", "cancelled"):
            return r
        time.sleep(0.1)
    raise AssertionError("Worker did not finish")


def test_health_migration_seed(client):
    assert client.get("/api/health").json()["local_only"]
    db.migrate()
    db.migrate()
    assert len(client.get("/api/variants").json()) >= 3


def test_validation_good_and_syntax(client):
    assert post(
        client,
        "/api/strategies/validate",
        {"source": (ROOT / "strategies/builtins/cont_a.py").read_text()},
    )["valid"]
    r = post(
        client, "/api/strategies/validate", {"source": "class Strategy:\n broken("}
    )
    assert not r["valid"] and r["line"]


def test_validation_crash_isolation(client):
    r = post(client, "/api/strategies/validate", {"source": "import os\nos._exit(4)"})
    assert not r["valid"]
    assert client.get("/api/health").status_code == 200


def test_validation_timeout():
    assert not services.validate("while True: pass", timeout=0.3)["valid"]


def test_versions_and_rename(client):
    st = draft(client)
    body = {"name": "Renamed", "source": st["source"]}
    r = client.put("/api/strategies/" + st["id"], json=body).json()
    assert r["current_version"] == 1
    body["source"] += "\n# changed source\n"
    r = client.put("/api/strategies/" + st["id"], json=body).json()
    assert r["current_version"] == 2
    versions = client.get("/api/strategies/" + st["id"] + "/versions").json()
    assert (
        versions[1]["source"] == st["source"]
        and versions[0]["source_hash"] != versions[1]["source_hash"]
    )


def test_variant_snapshot(client):
    st = draft(client)
    r = post(
        client,
        "/api/variants",
        {
            "name": "Saved inputs",
            "strategy_version_id": st["version_id"],
            "parameters": {"target_r": 3},
        },
    )
    assert r["parameters"]["target_r"] == 3
    assert client.get("/api/strategies/" + st["id"]).json()["source"] == st["source"]


def test_bad_params(client):
    st = draft(client)
    assert (
        client.post(
            "/api/backtests",
            json={
                "strategy_version_id": st["version_id"],
                "parameters": {"unknown": 1},
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/backtests",
            json={
                "strategy_version_id": st["version_id"],
                "settings": {"start": "2030-01-01"},
            },
        ).status_code
        == 422
    )


def test_completed_persisted_compared_and_exported(client):
    st = draft(client)
    body = {
        "strategy_version_id": st["version_id"],
        "settings": {"start": "2024-02-05", "end": "2024-02-07"},
    }
    a = post(client, "/api/backtests", body)["id"]
    ar = wait(client, a)
    assert ar["status"] == "completed", ar
    assert ar["metrics"]["overall"]["trades"] == 0
    b = post(client, "/api/backtests/" + a + "/clone", {})["id"]
    br = wait(client, b)
    assert br["status"] == "completed"
    assert ar["config"]["reproduction_hash"] == br["config"]["reproduction_hash"]
    assert (db.STORE / "artifacts" / a / "result.json").read_bytes() == (
        db.STORE / "artifacts" / b / "result.json"
    ).read_bytes()
    result = post(client, "/api/compare", {"ids": [a, b]})
    assert not result["warnings"] and len(result["runs"]) == 2
    assert client.get("/api/backtests/" + a + "/export.csv").status_code == 200
    assert client.get("/api/backtests/" + a + "/trades").json() == []


def test_failure_does_not_crash_service(client):
    st = draft(
        client,
        'class Strategy:\n def on_bar(self,ctx,p): raise RuntimeError("Test failure")\n',
    )
    rid = post(
        client,
        "/api/backtests",
        {
            "strategy_version_id": st["version_id"],
            "settings": {"start": "2024-02-05", "end": "2024-02-06"},
        },
    )["id"]
    assert wait(client, rid)["status"] == "failed"
    assert client.get("/api/health").status_code == 200


def test_cancel_hung_worker(client):
    st = draft(
        client, "class Strategy:\n def on_bar(self,ctx,p):\n  while True: pass\n"
    )
    rid = post(
        client,
        "/api/backtests",
        {
            "strategy_version_id": st["version_id"],
            "settings": {"start": "2024-02-05", "end": "2024-02-06"},
        },
    )["id"]
    time.sleep(0.5)
    assert (
        post(client, "/api/backtests/" + rid + "/cancel", {})["status"] == "cancelled"
    )
    assert wait(client, rid)["status"] == "cancelled"


def test_compare_warns_date_differences(client):
    st = draft(client)
    ids = []
    for end in ["2024-02-06", "2024-02-07"]:
        rid = post(
            client,
            "/api/backtests",
            {
                "strategy_version_id": st["version_id"],
                "settings": {"start": "2024-02-05", "end": end},
            },
        )["id"]
        assert wait(client, rid)["status"] == "completed"
        ids.append(rid)
    assert post(client, "/api/compare", {"ids": ids})["warnings"]


def test_sweep_children(client):
    st = draft(client)
    sw = post(
        client,
        "/api/sweeps",
        {
            "name": "Test sweep",
            "run": {
                "strategy_version_id": st["version_id"],
                "settings": {"start": "2024-02-05", "end": "2024-02-06"},
            },
            "parameter": "target_r",
            "values": [1, 2],
        },
    )
    row = next(r for r in client.get("/api/sweeps").json() if r["id"] == sw["id"])
    assert len(row["children"]) == 2
    for r in row["children"]:
        assert wait(client, r["id"])["status"] == "completed"


def test_data_and_research(client):
    assert len(client.get("/api/data").json()["datasets"]) == 4
    r = client.get("/api/research/fvgs?direction=bullish&touched=true&limit=2").json()
    assert len(r["rows"]) == 2 and r["stats"]["count"] >= 2


def test_archive_retains_versions(client):
    st = draft(client)
    client.delete("/api/strategies/" + st["id"])
    assert all(s["id"] != st["id"] for s in client.get("/api/strategies").json())
    assert client.get("/api/strategies/" + st["id"] + "/versions").json()


def test_reject_nonlocal_origin(client):
    assert (
        client.post(
            "/api/strategies/validate",
            headers={"origin": "https://evil.example"},
            json={"source": ""},
        ).status_code
        == 403
    )


def test_typed_settings_reject_unknown(client):
    st = draft(client)
    assert (
        client.post(
            "/api/backtests",
            json={
                "strategy_version_id": st["version_id"],
                "settings": {"lookahead": True},
            },
        ).status_code
        == 422
    )


def test_actual_nonempty_run_and_candles(client):
    source = "from engine.strategy import Entry\nclass Strategy:\n def on_bar(self,ctx,p):\n  if ctx.bar.time=='09:45':return Entry('LONG',ctx.bar.low-ctx.tick_size)\n"
    st = draft(client, source)
    rid = post(
        client,
        "/api/backtests",
        {
            "strategy_version_id": st["version_id"],
            "settings": {"start": "2024-02-05", "end": "2024-02-07"},
        },
    )["id"]
    r = wait(client, rid)
    assert r["status"] == "completed", r
    assert r["metrics"]["overall"]["trades"] == 2
    trades = client.get("/api/backtests/" + rid + "/trades").json()
    assert len(trades) == 2
    assert trades[0]["strategy_id"] == st["id"] and trades[0]["run_id"] == rid
    candles = client.get(f"/api/backtests/{rid}/candles/{trades[0]['trade_id']}").json()
    assert len(candles["bars"]) > 0
