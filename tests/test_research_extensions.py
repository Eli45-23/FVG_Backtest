"""Synthetic causal sequence and columnar inference coverage; no live OOS outcomes."""

from types import SimpleNamespace
from decimal import Decimal as D
import pandas as pd
import pytest
from engine.research.sequences import Sequences
from engine.research.numeric import validate, accepts, bucket
from engine.research.columnar import Writer, OUTCOME_SCHEMA
from engine.research.queries import page, summary
from engine.research.structure import Structure
from engine.strategy import Bar

AT = pd.Timestamp("2020-01-06 15:00", tz="UTC")


def row(i, low=101, high=105, close=104, complete=True):
    return SimpleNamespace(
        timestamp_utc=AT + pd.Timedelta(minutes=5 * i),
        open=D(102),
        low=D(low),
        high=D(high),
        close=D(close),
        is_complete_5m=complete,
    )


def event(i=0, kind="BREAK_ACCEPTANCE", direction="UP"):
    return dict(
        event_id=f"{kind}-{i}",
        level_id="level",
        level_price="100",
        level_type="PDH",
        timestamp_utc=str(AT + pd.Timedelta(minutes=5 * (i + 1))),
        interaction_type=kind,
        direction=direction,
        approach_side="BELOW",
        touch_number=1,
        close="102",
        high="103",
        low="99",
        atr14=5,
        distance_through_level=1,
    )


@pytest.mark.parametrize(
    "low,close,expected",
    [
        (101, 104, {"BREAK_NEXT_CANDLE_CLOSE_HOLD", "BREAK_NEXT_CANDLE_FULL_HOLD"}),
        (99, 101, {"BREAK_NEXT_CANDLE_CLOSE_HOLD"}),
        (97, 99, {"BREAK_FAILED_NEXT_CANDLE_HOLD"}),
        (99, 100, set()),
    ],
)
def test_adjacent_hold_definitions(low, close, expected):
    s = Sequences()
    assert s.update(row(0), [event()]) == []
    out = s.update(row(1, low=low, close=close), [])
    assert {e["interaction_type"] for e in out} == expected
    assert all(
        pd.Timestamp(e["timestamp_utc"]) == AT + pd.Timedelta(minutes=10) for e in out
    )


@pytest.mark.parametrize(
    "close,kind", [(101, "BREAK_RETEST_HOLD"), (99, "BREAK_RETEST_FAIL")]
)
def test_retest_chain(close, kind):
    s = Sequences()
    s.update(row(0), [event()])
    s.update(row(1), [])
    out = s.update(row(2, low=99, close=close), [event(2, "RETEST")])
    assert kind in {e["interaction_type"] for e in out}
    assert all(
        e["component_event_ids"] == ["BREAK_ACCEPTANCE-0", "RETEST-2"] for e in out
    )


@pytest.mark.parametrize("kind", ["SWEEP_RECLAIM", "REJECTION"])
def test_confirmation(kind):
    s = Sequences()
    s.update(row(0), [event(kind=kind)])
    assert (
        s.update(row(1, low=97, close=98), [])[0]["interaction_type"]
        == kind + "_CONFIRMATION"
    )


def test_gap_and_incomplete_cannot_bridge():
    s = Sequences()
    s.update(row(0), [event()])
    assert not s.update(row(2), [])
    s = Sequences()
    s.update(row(0), [event()])
    assert not s.update(row(1, complete=False), [])
    assert not s.update(row(2), [])


def test_choch_not_overwritten_by_old_progression():
    s = Structure()
    s.state = "BULLISH"
    s.progression = {"HIGH": "HH", "LOW": "HL"}
    s.low = {"id": "l", "price": 100}
    s.update(Bar(AT, D(101), D(102), D(98), D(99), 1), AT + pd.Timedelta(minutes=5))
    assert s.state == "BEARISH"


def test_numeric_bounds_and_buckets():
    spec = validate({"atr14": {"min": 10, "max": 20, "edges": [10, 15, 20]}})
    assert accepts({"atr14": 10}, spec) and not accepts({"atr14": None}, spec)
    assert bucket(15, [10, 15, 20]) == "[15, 20)"
    with pytest.raises(ValueError):
        validate({"atr14": {"edges": [20, 10]}})


def artifacts(tmp_path):
    for name in ("events", "observations"):
        w = Writer(tmp_path / f"v2_{name}.parquet")
        for i in range(12):
            w.add(
                dict(
                    event_id=f"{name}-{i}",
                    timestamp_utc=str(AT + pd.Timedelta(days=i)),
                    date=f"2020-01-{i+6:02}",
                    year=2020,
                    time_bucket="10:00",
                    volatility_bucket="low",
                    direction="UP",
                    atr14=10 + i,
                    price_at_event=100,
                )
            )
        w.close()
    w = Writer(tmp_path / "v2_outcomes.parquet", OUTCOME_SCHEMA)
    for name, kind in [("events", "event"), ("observations", "baseline")]:
        for i in range(12):
            w.add(
                dict(
                    event_id=f"{name}-{i}",
                    kind=kind,
                    horizon="30",
                    complete=True,
                    up_50=i % 2 == 0 if kind == "event" else False,
                    down_50=False,
                    maximum_high_excursion=50,
                    maximum_low_excursion=5,
                    forward_close_change=1,
                    payload="{}",
                )
            )
    w.close()


def test_columnar_page_stats_determinism(tmp_path):
    artifacts(tmp_path)
    assert page(tmp_path, numeric={"atr14": {"min": 15}}, limit=2)["count"] == 7
    cfg = {
        "research_settings": {
            "numeric_filters": {},
            "statistics": {"seed": 1, "iterations": 100, "minimum_dates": 10},
        }
    }
    a = summary(tmp_path, cfg)
    assert a == summary(tmp_path, cfg)
    r = a["groups"][0]
    assert (
        r["events"] == 12
        and r["unique_dates"] == 12
        and r["effect"] == 0.5
        and r["q_value"] is not None
    )
    assert summary(tmp_path, cfg, numeric={"atr14": {"edges": [15]}}, group="atr14")[
        "groups"
    ][0]["events"] in (5, 7)
    with pytest.raises(ValueError):
        page(tmp_path, sort="DROP TABLE events")


def test_invalid_ohlc_resets_sequence():
    s = Sequences()
    s.update(row(0), [event()])
    assert not s.update(row(1, low=110, high=105), [])
    assert not s.update(row(2), [event(2, "RETEST")])


def test_atr_labels_use_event_atr_and_minute_end_time(tmp_path, monkeypatch):
    from engine.research import study2
    from engine.research.columnar import query
    import json

    raw = pd.DataFrame(
        dict(
            ts_event=pd.date_range(AT, periods=60, freq="min"),
            open=100_000_000_000,
            high=104_000_000_000,
            low=98_000_000_000,
            close=102_000_000_000,
            volume=1,
        )
    )
    monkeypatch.setattr(study2, "source", lambda config: raw.copy())
    e = Writer(tmp_path / "v2_events.parquet")
    e.add(
        dict(
            event_id="test",
            date="2020-01-06",
            timestamp_utc=str(AT),
            session_close=str(AT + pd.Timedelta(minutes=60)),
            price_at_event=100,
            direction="UP",
            atr14=2,
        )
    )
    e.close()
    b = Writer(tmp_path / "v2_observations.parquet")
    b.close()
    study2.labels({"research_settings": {"atr_thresholds": [0.5, 1, 2, 3]}}, tmp_path)
    out = json.loads(
        query(tmp_path, "SELECT payload FROM outcomes WHERE horizon='5'")[0]["payload"]
    )
    assert (
        out["mfe_atr"] == 2
        and out["mae_atr"] == 1
        and out["forward_close_change_atr"] == 1
    )
    assert out["atr_thresholds"]["up_2"] == {"reached": True, "minutes": 1}
    assert out["atr_thresholds"]["up_3"] == {"reached": False, "minutes": None}
