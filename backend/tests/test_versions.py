from test_api import client, post, draft, wait
from backend.app import db


def changed(client):
    st = draft(client)
    newer = client.put(
        "/api/strategies/" + st["id"],
        json={"name": st["name"], "source": st["source"] + "\n# v2"},
    ).json()
    return st, newer


def test_version_detail_immutable(client):
    a, b = changed(client)
    r = client.get("/api/versions/" + a["version_id"]).json()
    assert r["source"] == a["source"]
    assert r["number"] == 1
    assert (
        client.put(
            "/api/versions/" + a["version_id"], json={"source": "bad"}
        ).status_code
        == 405
    )


def test_version_diff(client):
    a, b = changed(client)
    r = client.get(f"/api/versions/{a['version_id']}/diff/{b['version_id']}").json()
    assert "+# v2" in r["unified_diff"]
    assert r["original"]["source"] == a["source"]
    assert r["modified"]["source"] == b["source"]


def test_clone_historical(client):
    a, b = changed(client)
    c = post(
        client, f"/api/versions/{a['version_id']}/clone", {"name": "Historic clone"}
    )
    r = client.get("/api/strategies/" + c["strategy_id"]).json()
    assert r["source"] == a["source"] and r["id"] != a["id"]


def test_restore_appends(client):
    a, b = changed(client)
    r = post(client, f"/api/versions/{a['version_id']}/restore", {})
    assert r["number"] == 3
    vs = client.get("/api/strategies/" + a["id"] + "/versions").json()
    assert vs[0]["source"] == vs[2]["source"] == a["source"]
    assert vs[1]["source"] == b["source"]


def test_restore_current_still_appends(client):
    a = draft(client)
    r = post(client, f"/api/versions/{a['version_id']}/restore", {})
    assert r["number"] == 2 and r["version_id"] != a["version_id"]


def test_run_keeps_exact_source(client):
    a, b = changed(client)
    rid = post(
        client,
        "/api/backtests",
        {
            "strategy_version_id": a["version_id"],
            "settings": {"start": "2024-02-05", "end": "2024-02-06"},
        },
    )["id"]
    assert wait(client, rid)["status"] == "completed"
    detail = client.get("/api/versions/" + a["version_id"]).json()
    assert any(r["id"] == rid for r in detail["runs"])
    assert detail["source_hash"] == a["source_hash"]
    assert (
        client.get("/api/backtests/" + rid).json()["config"]["source_hash"]
        == a["source_hash"]
    )


def test_variant_version_relationship(client):
    a, b = changed(client)
    v = post(
        client,
        "/api/variants",
        {"strategy_version_id": a["version_id"], "name": "Old inputs"},
    )
    assert any(
        x["id"] == v["id"]
        for x in client.get("/api/versions/" + a["version_id"]).json()["variants"]
    )


def test_invalid_version(client):
    assert client.get("/api/versions/absent").status_code == 404
