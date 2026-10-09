import json
import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app import zone_ground_truth_v2 as z
from engine.zone_ground_truth import collection as c
from engine.zone_ground_truth.comparison import measure


@pytest.fixture
def data(monkeypatch, tmp_path):
    rows = []
    for i in range(8):
        at = pd.Timestamp("2020-02-03 18:00", tz="America/New_York") + pd.Timedelta(
            hours=4 * i
        )
        rows.append(
            dict(
                timestamp=at,
                availability_timestamp=at + pd.Timedelta(hours=4),
                bar_id=str(i),
                session_date="2020-02-04",
                complete=True,
                full=True,
                schedule_resolved=True,
                open=100.0,
                high=105.0,
                low=95.0,
                close=101.0,
                atr14=10.0,
            )
        )
    bars = pd.DataFrame(rows)
    ident = {
        "dataset_sha256": "test",
        "provider_configuration": {"secret_proposal_context": True},
    }
    b = c.window(bars, 5, "BLIND")
    n = c.window(bars, 6, "NEAR_MISS", private_reason="WEAK_DEPARTURE")
    proposal = dict(
        zone_id="z",
        zone_type="SUPPLY",
        base_timestamps=[str(bars.iloc[4].timestamp)],
        top=105.0,
        bottom=100.0,
        availability_timestamp=str(bars.iloc[5].availability_timestamp),
        base_count=1,
        pattern_type="RALLY_BASE_DROP",
    )
    r = c.window(bars, 5, "PROVIDER_REVIEW", proposal=proposal)
    bundle = dict(
        blind=[b],
        near_miss=[n],
        review=[r],
        protocol=dict(
            protocol_sha256="p",
            minimum={"blind_human_zones": 1},
            acceptance={
                "HUMAN_GROUND_TRUTH_ACCEPTED": dict(
                    precision=0.9,
                    recall=0.9,
                    base=0.9,
                    proximal=0.9,
                    distal=0.9,
                    availability=0.95,
                )
            },
            matching="test",
        ),
    )
    monkeypatch.setattr(z, "foundation", lambda: (bars, ident, [proposal], bundle))
    monkeypatch.setattr(z.db, "STORE", tmp_path)
    return bars, ident, bundle


def unlock(bundle):
    for s in bundle["blind"] + bundle["near_miss"]:
        z.annotate(z.Annotation(sample_id=s["sample_id"], label="NOT_A_ZONE"))


def test_blind_no_rectangle_or_provider_or_future(data):
    bars, _, b = data
    s = b["blind"][0]
    v = z.view(s["sample_id"])
    assert v["proposal"] is None and not v["chart"]["annotations"]
    assert "provider_configuration" not in v["identity"]
    assert (
        max(pd.Timestamp(x["timestamp_utc"]) for x in v["chart"]["candles"])
        == bars.iloc[5].timestamp
    )
    bars.loc[6:, "high"] = 999999
    assert z.view(s["sample_id"]) == v
    assert "private_reason" not in z.view(b["near_miss"][0]["sample_id"])


def test_proposals_locked_until_blind_complete(data):
    _, _, b = data
    with pytest.raises(ValueError):
        z.view(b["review"][0]["sample_id"])
    unlock(b)
    assert z.view(b["review"][0]["sample_id"])["proposal"]["zone_id"] == "z"
    original = z.latest()[0]
    with pytest.raises(ValueError, match="exposure"):
        z.annotate(
            z.Annotation(
                sample_id=original["sample_id"],
                label="NOT_A_ZONE",
                supersedes=original["annotation_id"],
            )
        )


@pytest.mark.parametrize("side,top,bottom", [("SUPPLY", 105, 100), ("DEMAND", 101, 95)])
def test_human_boundaries(data, side, top, bottom):
    _, _, b = data
    s = z.Selection(sample_id=b["blind"][0]["sample_id"], first=3, last=4, side=side)
    h = z.calculate(s)
    assert (h["top"], h["bottom"]) == (top, bottom)
    assert h["base_ids"] == ["3", "4"]


def test_excluded_or_departure_candles_cannot_be_base(data):
    bars, _, b = data
    sid = b["blind"][0]["sample_id"]
    with pytest.raises(ValueError):
        z.calculate(z.Selection(sample_id=sid, first=3, last=5, side="SUPPLY"))
    bars.loc[3, "schedule_resolved"] = False
    with pytest.raises(ValueError):
        z.calculate(z.Selection(sample_id=sid, first=3, last=4, side="SUPPLY"))
    assert "3" not in [x["bar_id"] for x in z.view(sid)["choices"]]


def test_append_correction_preserves_old_version(data):
    _, _, b = data
    sid = b["blind"][0]["sample_id"]
    a = z.annotate(z.Annotation(sample_id=sid, label="NOT_A_ZONE"))
    h = z.calculate(z.Selection(sample_id=sid, first=4, last=4, side="SUPPLY"))
    body = z.Annotation(
        sample_id=sid,
        label="VALID_SUPPLY",
        selection=z.Selection(sample_id=sid, first=4, last=4, side="SUPPLY"),
        preview_hash=h["preview_hash"],
        rectangle_approved=True,
        departure_excluded=True,
        supersedes=a["annotation_id"],
    )
    newer = z.annotate(body)
    assert newer["version"] == 2 and len(z.records()) == 2 and len(z.latest()) == 1
    with pytest.raises(ValueError):
        z.annotate(body)


def test_no_auto_labels_and_no_early_metrics(data):
    assert z.records() == []
    m = z.comparison()
    assert m["status"] == "INSUFFICIENT_HUMAN_LABELS" and m["concept_precision"] is None


def test_provider_review_exact_and_comparison(data):
    _, _, b = data
    sid = b["blind"][0]["sample_id"]
    selection = z.Selection(sample_id=sid, first=4, last=4, side="SUPPLY")
    h = z.calculate(selection)
    z.annotate(
        z.Annotation(
            sample_id=sid,
            label="VALID_SUPPLY",
            selection=selection,
            preview_hash=h["preview_hash"],
            rectangle_approved=True,
            departure_excluded=True,
        )
    )
    z.annotate(
        z.Annotation(sample_id=b["near_miss"][0]["sample_id"], label="NOT_A_ZONE")
    )
    sid = b["review"][0]["sample_id"]
    selection = z.Selection(sample_id=sid, first=4, last=4, side="SUPPLY")
    h = z.calculate(selection)
    z.annotate(
        z.Annotation(
            sample_id=sid,
            label="ACCEPT_EXACT",
            selection=selection,
            preview_hash=h["preview_hash"],
            rectangle_approved=True,
            departure_excluded=True,
        )
    )
    m = z.comparison()
    assert (
        m["concept_precision"] == 1
        and m["blind_window_recall"] == 1
        and m["base_agreement"] == 1
    )
    assert m["status"] == "HUMAN_GROUND_TRUTH_ACCEPTED"
    assert z.export()["snapshot_id"] == z.export()["snapshot_id"]


def test_multiple_zones_and_explicit_window_completion(data):
    _, _, b = data
    sid = b["blind"][0]["sample_id"]
    for side in ("SUPPLY", "DEMAND"):
        sel = z.Selection(sample_id=sid, first=4, last=4, side=side)
        h = z.calculate(sel)
        z.annotate(
            z.Annotation(
                sample_id=sid,
                label="VALID_" + side,
                selection=sel,
                preview_hash=h["preview_hash"],
                rectangle_approved=True,
                departure_excluded=True,
                window_complete=False,
            )
        )
    assert sid not in z.completed()
    z.complete_window(sid)
    assert sid in z.completed() and len(z.latest()) == 2


def test_api_and_immutable_export(data):
    app = FastAPI()
    app.include_router(z.router)
    client = TestClient(app)
    assert client.get("/api/zone-ground-truth-v2/collection").status_code == 200
    assert (
        client.get("/api/zone-ground-truth-v2/comparison").json()["concept_precision"]
        is None
    )
    assert client.post("/api/zone-ground-truth-v2/export").status_code == 200


def test_provider_sample_ids_unique_per_proposal(data):
    bars, _, _ = data
    assert (
        c.window(bars, 5, "PROVIDER_REVIEW", proposal={"zone_id": "a"})["sample_id"]
        != c.window(bars, 5, "PROVIDER_REVIEW", proposal={"zone_id": "b"})["sample_id"]
    )


def test_collection_does_not_leak_provider_dates_before_blind_done(data):
    _, _, b = data
    response = z.collection()
    assert all(s["kind"] != "PROVIDER_REVIEW" for s in response["samples"])
    unlock(b)
    assert any(s["kind"] == "PROVIDER_REVIEW" for s in z.collection()["samples"])


def test_backend_engine_bound_to_isolated_storage():
    from pathlib import Path

    assert Path(z.db.engine.url.database).resolve().parent != z.db.ROOT / "storage"
