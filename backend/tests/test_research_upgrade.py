from test_api import client, post
from test_event_studies import create
from backend.app import db, event_studies
from engine.canonical import digest
import pytest


@pytest.fixture(scope="module")
def upgraded(client):
    r = create(
        client,
        research_version=2,
        research_settings={
            "statistics": {"iterations": 100},
            "numeric_filters": {"atr14": {"min": 0, "edges": [10, 25, 50]}},
        },
    )
    assert r["status"] == "completed", r
    return r


def test_v2_query_stats_export(client, upgraded):
    prefix = "/api/level-research/studies/" + upgraded["id"]
    rows = post(
        client, prefix + "/query", {"numeric": {"atr14": {"min": 10}}, "limit": 5}
    )
    assert rows["count"] >= len(rows["events"]) > 0
    stats = post(client, prefix + "/statistics", {"group": "atr14"})
    assert stats["groups"] and "ci95" in stats["groups"][0]
    assert stats == post(client, prefix + "/statistics", {"group": "atr14"})
    assert client.get(prefix + "/export").json()["config_hash"] == digest(
        upgraded["config"]
    )
    assert client.get(prefix + "/export?format=csv").status_code == 200
    chart = client.get(
        prefix + "/events/" + rows["events"][0]["event_id"] + "/chart"
    ).json()
    assert chart["candles"]


def test_v2_sealed_statistics_gate(client, monkeypatch):
    monkeypatch.setattr(event_studies.pool, "submit", lambda *args: None)
    r = post(
        client,
        "/api/level-research/studies",
        {
            "research_version": 2,
            "segment": "out-of-sample",
            "start": "2025-01-06",
            "end": "2025-01-07",
        },
    )
    with db.Session.begin() as s:
        s.get(db.EventStudy, r["id"]).status = "sealed"
    assert (
        client.post(
            "/api/level-research/studies/" + r["id"] + "/statistics", json={}
        ).status_code
        == 409
    )


def test_research_profile_split(client):
    r = post(
        client,
        "/api/research-splits",
        {
            "name": "Research profile",
            "dataset_profile": "research_2020_2026",
            "ranges": {
                "development": {"start": "2020-01-01", "end": "2024-01-01"},
                "validation": {"start": "2024-01-01", "end": "2025-01-01"},
                "out-of-sample": {"start": "2025-01-01", "end": "2026-10-06"},
            },
        },
    )
    assert r["dataset_profile"] == "research_2020_2026"


def test_partial_run_profile_identity_and_artifact(client):
    from test_api import wait

    source = """from engine.strategy import PositionPlan, TargetLeg
from decimal import Decimal as D
class Strategy:
    def on_bar(self,ctx,p):
        if ctx.bar.time in ('09:35','10:00'):
            assert ctx.frames['1m'].timestamp < ctx.timestamp
            return PositionPlan('LONG',ctx.bar.close-D('2'),legs=(TargetLeg(1,D('1'),'TP1'),TargetLeg(1,None,'runner')),break_even_after_tp1=True)
"""
    st = post(
        client,
        "/api/strategies",
        {"name": "Synthetic partial capability", "source": source},
    )
    r = post(
        client,
        "/api/backtests",
        {
            "strategy_version_id": st["version_id"],
            "settings": {
                "dataset_profile": "research_2020_2026",
                "execution_mode": "extended_v1",
                "start": "2020-01-06",
                "end": "2020-01-07",
                "quantity": 2,
                "max_trades_per_day": 3,
            },
        },
    )
    result = wait(client, r["id"])
    assert result["status"] == "completed", result
    assert result["config"]["dataset_identity"]["files"]["minutes"]["rows"] == 2388306
    trades = client.get("/api/backtests/" + r["id"] + "/trades").json()
    # API returns paginated records.
    rows = (
        trades["trades"]
        if isinstance(trades, dict) and "trades" in trades
        else trades.get("rows", []) if isinstance(trades, dict) else trades
    )
    assert (
        rows
        and rows[0]["initial_quantity"] == 2
        and rows[0]["partial_execution_history"]
    )

    trade = rows[0]
    chart = client.get(
        f"/api/backtests/{r['id']}/trades/{trade['trade_id']}/chart"
    ).json()
    assert [a["price"] for a in chart["annotations"] if a["category"] == "exit"] == [
        float(f["exit_price"]) for f in trade["partial_execution_history"]
    ]
    assert [a["price"] for a in chart["annotations"] if a["category"] == "target"] == [
        float(l["price"]) for l in trade["target_legs"] if l["price"] is not None
    ]


def test_v2_artifacts_deterministic(client, upgraded):
    from test_event_studies import create

    repeat = create(
        client,
        research_version=2,
        research_settings={
            "statistics": {"iterations": 100},
            "numeric_filters": {"atr14": {"min": 0, "edges": [10, 25, 50]}},
        },
    )
    assert repeat["status"] == "completed"
    for name in ("v2_events.parquet", "v2_observations.parquet", "v2_outcomes.parquet"):
        assert (event_studies.root(repeat["id"]) / name).read_bytes() == (
            event_studies.root(upgraded["id"]) / name
        ).read_bytes()


def test_atr_statistics_query(client, upgraded):
    r = post(
        client,
        "/api/level-research/studies/" + upgraded["id"] + "/statistics",
        {"threshold_atr": 0.5},
    )
    assert r["threshold_atr"] == 0.5 and r["threshold_points"] is None
