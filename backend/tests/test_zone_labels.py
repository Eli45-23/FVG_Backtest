import json
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from backend.app import zone_labels as z


@pytest.fixture
def data(monkeypatch, tmp_path):
    rows = []
    for i in range(20):
        t = pd.Timestamp("2020-02-03 18:00", tz="America/New_York") + pd.Timedelta(
            hours=4 * i
        )
        rows.append(
            dict(
                timestamp=t,
                availability_timestamp=t + pd.Timedelta(hours=4),
                open=100.0,
                high=104.0,
                low=96.0,
                close=101.0,
                volume=1,
                atr14=8.0,
                full=True,
                complete=True,
            )
        )
    bars = pd.DataFrame(rows)
    ident = {
        "dataset": "synthetic-development",
        "construction": {"schedule_sha256": "test"},
        "status": "PROVISIONAL_PENDING_HUMAN_GROUND_TRUTH",
    }
    monkeypatch.setattr(z, "foundation", lambda: (bars, ident))
    monkeypatch.setattr(z.db, "STORE", tmp_path)
    return bars, ident


def selection(**kw):
    return z.Selection(**dict(candidate=5, first=2, last=3, zone_type="SUPPLY", **kw))


@pytest.mark.parametrize("side,top,bottom", [("SUPPLY", 104, 100), ("DEMAND", 101, 96)])
def test_boundaries_and_hidden_future(data, side, top, bottom):
    b, i = data
    s = z.Selection(candidate=5, first=2, last=3, zone_type=side)
    x = z.preview(s, b, i)
    assert (x["top"], x["bottom"]) == (top, bottom)
    assert x["base_count"] == 2 and len(x["departure_timestamps"]) == 2
    assert (
        max(pd.Timestamp(c["timestamp_utc"]) for c in x["chart"]["candles"])
        == b.iloc[5].timestamp
    )
    changed = b.copy()
    changed.loc[6:, "high"] = 99999
    assert z.preview(s, changed, i) == x


@pytest.mark.parametrize("first,last", [(2, 5), (6, 6), (0, 1)])
def test_departure_must_be_separate(data, first, last):
    with pytest.raises(ValueError):
        z.preview(
            z.Selection(candidate=5, first=first, last=last, zone_type="SUPPLY"), *data
        )


@pytest.mark.parametrize("column", ["complete", "full"])
def test_incomplete_shortened_no_selection(data, column):
    b, i = data
    b.loc[3, column] = False
    with pytest.raises(ValueError):
        z.preview(selection(), b, i)


def test_missing_adjacency(data):
    b, i = data
    b.loc[3, "timestamp"] += pd.Timedelta(minutes=1)
    with pytest.raises(ValueError):
        z.preview(selection(), b, i)


def test_seed_and_date_boundary(data):
    assert z.candidate(mode="random", seed=42) == z.candidate(mode="random", seed=42)
    for date in ("2019-12-31", "2024-01-01", "2025-01-01"):
        with pytest.raises(ValueError):
            z.candidate(mode="jump", jump=date)


def test_immutable_annotations_freeze_and_comparison(data):
    x = z.preview(selection(), *data)
    body = z.Label(
        **selection().model_dump(),
        decision="VALID_SUPPLY",
        rectangle_approved=True,
        departure_excluded_confirmed=True,
        notes="synthetic",
        preview_hash=x["preview_hash"]
    )
    a = z.annotate(body)
    assert a == z.annotate(body)
    snap = z.freeze()
    assert snap == z.freeze()
    assert len(z.annotations()) == 1
    assert z.comparison(snap["id"])["report"]["false_negatives"] == 1
    with pytest.raises(ValueError):
        z.comparison("../bad")


def test_reject_unapproved_or_stale(data):
    x = z.preview(selection(), *data)
    d = dict(
        **selection().model_dump(),
        decision="VALID_SUPPLY",
        rectangle_approved=True,
        departure_excluded_confirmed=True,
        preview_hash=x["preview_hash"]
    )
    for change in (
        {"rectangle_approved": False},
        {"departure_excluded_confirmed": False},
        {"preview_hash": "stale"},
        {"decision": "VALID_DEMAND"},
    ):
        with pytest.raises(ValueError):
            z.annotate(z.Label(**(d | change)))


def test_reviewed_metrics_and_timing(data):
    x = z.preview(selection(), *data)
    h = dict(id="a", preview=x, decision="VALID_SUPPLY")
    pred = dict(
        zone_id="p",
        zone_type="SUPPLY",
        base_timestamps=[pd.Timestamp(t) for t in x["base_timestamps"]],
        top=x["top"],
        bottom=x["bottom"],
        availability_timestamp=pd.Timestamp(x["availability"]) - pd.Timedelta(hours=4),
    )
    r = z.compare([h], [pred])
    assert r["true_positives"] == 1 and r["precision"] == 1 and r["recall"] == 1
    assert r["exact_boundary_agreement"] == 1 and r["availability_time_agreement"] == 0
    assert z.compare([h], [])["false_negatives"] == 1
    h["decision"] = "NOT_A_ZONE"
    assert z.compare([h], [pred])["false_positives"] == 1
    assert z.compare([h], [])["true_negatives"] == 1
    assert z.compare([], [])["precision"] is None


def test_api_roundtrip(data):
    app = FastAPI()
    app.include_router(z.router)
    client = TestClient(app)
    c = client.get("/api/zone-labels/candidate").json()
    assert "chart" in c
    p = client.post("/api/zone-labels/preview", json=selection().model_dump()).json()
    r = client.post(
        "/api/zone-labels/annotations",
        json=dict(
            **selection().model_dump(),
            decision="NOT_A_ZONE",
            rectangle_approved=False,
            departure_excluded_confirmed=True,
            preview_hash=p["preview_hash"]
        ),
    )
    assert r.status_code == 200
    assert len(client.get("/api/zone-labels/annotations").json()) == 1
    assert client.post("/api/zone-labels/freeze").status_code == 200


def test_negative_labels_do_not_inflate_agreement(data):
    x = z.preview(selection(), *data)
    pred = dict(
        zone_id="p",
        zone_type="SUPPLY",
        base_timestamps=[pd.Timestamp(t) for t in x["base_timestamps"]],
        top=x["top"],
        bottom=x["bottom"],
        availability_timestamp=x["availability"],
    )
    r = z.compare(
        [
            dict(id="yes", preview=x, decision="VALID_SUPPLY"),
            dict(id="no", preview=x, decision="NOT_A_ZONE"),
        ],
        [pred],
    )
    assert r["precision"] == 0.5
    assert r["exact_boundary_agreement"] == 1
    assert r["availability_time_agreement"] == 1
    assert r["base_candle_agreement"] == 1


def test_preview_hash_prevents_identity_mismatch(data):
    b, i = data
    x = z.preview(selection(), b, i)
    assert (
        z.preview(selection(), b, dict(i, bars_sha256="new"))["preview_hash"]
        != x["preview_hash"]
    )
