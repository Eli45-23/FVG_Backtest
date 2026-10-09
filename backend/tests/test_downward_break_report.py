import json, hashlib
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app import downward_break_report as r


def client(monkeypatch, tmp_path):
    monkeypatch.setattr(r, "P", tmp_path)
    app = FastAPI()
    app.include_router(r.router)
    return TestClient(app)


def test_unverified_not_exposed(monkeypatch, tmp_path):
    c = client(monkeypatch, tmp_path)
    assert c.get("/api/research/downward-break-feasibility").json()["ready"] is False
    assert c.get("/api/research/downward-break-feasibility/files/study.html").status_code == 409


def test_verified_allowlist_and_hash(monkeypatch, tmp_path):
    c = client(monkeypatch, tmp_path)
    p = tmp_path / "study.html"
    p.write_text("<h1>Development</h1>")
    m = dict(
        status="PASS",
        segment="development",
        entry_records=2,
        artifacts={
            "study.html": {"sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        },
    )
    (tmp_path / "reproducibility_manifest.json").write_text(json.dumps(m))
    assert c.get("/api/research/downward-break-feasibility").json()["events"] == 2
    assert c.get("/api/research/downward-break-feasibility/files/study.html").status_code == 200
    assert c.get("/api/research/downward-break-feasibility/files/.env").status_code == 404
    p.write_text("changed")
    assert c.get("/api/research/downward-break-feasibility/files/study.html").status_code == 409


def test_non_development_blocked(monkeypatch, tmp_path):
    c = client(monkeypatch, tmp_path)
    (tmp_path / "reproducibility_manifest.json").write_text(
        json.dumps(dict(status="PASS", segment="validation"))
    )
    assert c.get("/api/research/downward-break-feasibility/files/study.html").status_code == 409
