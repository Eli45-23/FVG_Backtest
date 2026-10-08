import json, time, sqlite3
from pathlib import Path
import pytest
from sqlalchemy import text
from test_api import client, post
from backend.app import db, event_studies as api
from engine.canonical import digest
from engine.research.study import snapshot, run_detection, run_labels


def wait_study(client, id):
    until = time.monotonic() + 60
    while time.monotonic() < until:
        row = client.get("/api/level-research/studies/" + id).json()
        if row["status"] not in ["queued", "running"]:
            return row
        time.sleep(0.1)
    raise AssertionError("Study worker timeout")


def create(client, **kwargs):
    body = {"start": "2020-01-06", "end": "2020-01-08", **kwargs}
    r = post(client, "/api/level-research/studies", body)
    return wait_study(client, r["id"])


@pytest.fixture(scope="module")
def development(client):
    row = create(client)
    assert row["status"] == "completed", row
    return row


def test_profile_rows_and_identity(client):
    profiles = client.get("/api/level-research/profiles").json()
    p = next(p for p in profiles if p["profile"] == "research_2020_2026")
    assert p["files"]["minutes"]["rows"] == 2388306
    assert p["files"]["bars"]["rows"] == 477855
    assert len(p["files"]["bars"]["sha256"]) == 64


def test_worker_config_identity_and_more_than_one_per_day(client, development):
    r = development
    assert r["config_hash"] == digest(r["config"])
    events = client.get(f"/api/level-research/studies/{r['id']}/events").json()
    assert events["count"] > 2
    assert r["config"]["dataset_identity"]["profile"] == "research_2020_2026"


def test_summary_export_chart_filters(client, development):
    prefix = "/api/level-research/studies/" + development["id"]
    r = client.get(prefix + "/summary").json()
    assert r["overall"]["events"] > 0
    assert len(r["overall"]["probabilities"]) == 10
    e = client.get(prefix + "/events?level_type=O5H").json()["events"][0]
    assert e["level_type"] == "O5H"
    chart = client.get(prefix + "/events/" + e["event_id"] + "/chart").json()
    assert chart["candles"] and not chart["future_hidden"]
    assert (
        client.get(prefix + "/export").json()["config_hash"]
        == development["config_hash"]
    )
    assert "outcomes_json" in client.get(prefix + "/export?format=csv").text


def test_development_determinism(client, development):
    repeat = create(client)
    for name in [
        "events.json",
        "observations.json",
        "outcomes.json",
        "baseline_outcomes.json",
    ]:
        assert (api.root(repeat["id"]) / name).read_bytes() == (
            api.root(development["id"]) / name
        ).read_bytes()


def test_oos_hidden_until_explicit_reveal(client):
    row = create(client, segment="out-of-sample", start="2025-01-06", end="2025-01-07")
    assert row["status"] == "sealed" and not row["outcomes_available"]
    prefix = "/api/level-research/studies/" + row["id"]
    assert not (api.root(row["id"]) / "outcomes.json").exists()
    for path in ["/summary", "/export", "/export?format=csv"]:
        assert client.get(prefix + path).status_code == 409
    e = client.get(prefix + "/events").json()["events"][0]
    chart = client.get(prefix + "/events/" + e["event_id"] + "/chart").json()
    import pandas as pd

    assert chart["future_hidden"]
    assert all(
        pd.Timestamp(b["timestamp_utc"]) + pd.Timedelta(minutes=5)
        <= pd.Timestamp(e["timestamp_utc"])
        for b in chart["candles"]
    )
    post(client, prefix + "/reveal", {})
    assert wait_study(client, row["id"])["outcomes_available"]
    assert client.get(prefix + "/summary").status_code == 200
    with db.Session() as s:
        original = db.encode(s.get(db.EventReveal, row["id"]))
    post(client, prefix + "/reveal", {})
    with db.Session() as s:
        assert db.encode(s.get(db.EventReveal, row["id"])) == original
    with pytest.raises(Exception):
        with db.Session.begin() as s:
            s.execute(
                text("DELETE FROM event_study_reveals WHERE study_id=:id"),
                {"id": row["id"]},
            )


def test_no_segment_bypass(client):
    r = client.post(
        "/api/level-research/studies",
        json={"segment": "development", "start": "2025-01-01", "end": "2025-01-02"},
    )
    assert r.status_code == 422


def test_immutable_configuration(client, development):
    with pytest.raises(Exception):
        with db.Session.begin() as s:
            s.execute(
                text("UPDATE event_studies SET config='{}' WHERE id=:id"),
                {"id": development["id"]},
            )


def test_unknown_id_and_chart(client, development):
    assert client.get("/api/level-research/studies/../../etc/passwd").status_code == 404
    assert client.get("/api/level-research/studies/nope").status_code == 404
    assert (
        client.get(
            "/api/level-research/studies/" + development["id"] + "/events/nope/chart"
        ).status_code
        == 404
    )


def test_migration_preserves_v11_copy(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    src = sqlite3.connect("work/levels-before.db")
    p = tmp_path / "old.db"
    target = sqlite3.connect(p)
    src.backup(target)
    target.close()
    src.close()
    c = sqlite3.connect(p)
    tables = [
        r[0] for r in c.execute("select name from sqlite_master where type='table'")
    ]
    before = {t: c.execute(f"select * from {t}").fetchall() for t in tables}
    c.close()
    oldengine, oldsession = db.engine, db.Session
    try:
        db.engine = create_engine("sqlite:///" + str(p))
        db.Session = sessionmaker(db.engine)
        db.migrate()
        db.migrate()
        c = sqlite3.connect(p)
        for t, rows in before.items():
            if t != "schema_migrations":
                assert c.execute(f"select * from {t}").fetchall() == rows
        assert (
            c.execute("select max(version) from schema_migrations").fetchone()[0] == 4
        )
        c.close()
    finally:
        db.engine.dispose()
        db.engine, db.Session = oldengine, oldsession


def test_worker_failure_isolated(client, monkeypatch):
    monkeypatch.setattr(
        api, "snapshot", lambda c: {**snapshot(c), "research_engine_version": "invalid"}
    )
    row = create(client)
    assert row["status"] == "failed"
    assert client.get("/api/health").status_code == 200


def test_cancel_queued_without_work(client, monkeypatch):
    monkeypatch.setattr(api.pool, "submit", lambda *args: None)
    row = post(
        client,
        "/api/level-research/studies",
        {"start": "2020-01-06", "end": "2020-01-07"},
    )
    post(client, "/api/level-research/studies/" + row["id"] + "/cancel", {})
    api.execute(row["id"], "detect")
    assert (
        client.get("/api/level-research/studies/" + row["id"]).json()["status"]
        == "cancelled"
    )


def test_export_directional_labels_and_frozen_calendar(client, development):
    result = client.get(
        "/api/level-research/studies/" + development["id"] + "/export"
    ).json()
    assert result["config"]["calendar"]["sha256"] == digest(
        result["config"]["calendar"]["sessions"]
    )
    from engine.research.profiles import profile

    assert (
        result["config"]["dataset_identity"] == profile("research_2020_2026").identity()
    )
    for e in result["events"]:
        for outcome in result["outcomes"][e["event_id"]].values():
            if outcome["complete"] and e["direction"] != "UNKNOWN":
                assert outcome["mfe"] is not None and outcome["mae"] is not None


def test_chart_level_does_not_precede_availability(client, development):
    prefix = "/api/level-research/studies/" + development["id"]
    e = client.get(prefix + "/events?level_type=O5H").json()["events"][0]
    c = client.get(prefix + "/events/" + e["event_id"] + "/chart").json()
    import pandas as pd

    assert pd.Timestamp(c["annotations"][0]["start_time"]) >= pd.Timestamp(
        e["level_available_at"]
    )
