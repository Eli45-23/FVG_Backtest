import pytest
import pyarrow.parquet as pq
import pandas as pd
from engine.legacy import ROOT, reference
from engine.canonical import clean
from backend.app.charts import chart_payload, Annotation


@pytest.fixture
def trades():
    path = ROOT / "outputs/results/CONT_A_risk100_no_1000_1029_trades.parquet"
    if not path.exists():
        pytest.skip("Local reference required")
    return clean(pq.read_table(path).to_pylist())


@pytest.mark.parametrize("window", ["30", "60", "session"])
def test_source_candles_and_markers(trades, window):
    r = chart_payload(trades, trades[0]["trade_id"], window)
    source = (
        pq.read_table(reference.INPUTS["bars"]).to_pandas().set_index("timestamp_utc")
    )
    for c in r["candles"]:
        row = source.loc[pd.Timestamp(c["timestamp_utc"])]
        for k in ["open", "high", "low", "close"]:
            assert float(c[k]) == float(row[k])
    t = trades[0]
    annotations = r["annotations"]
    for label, key in [
        ("Entry", "entry_price"),
        ("Original stop", "stop_price"),
        ("Original target", "target_price"),
    ]:
        a = next(a for a in annotations if a["label"] == label)
        assert a["price"] == float(t[key])
        assert pd.Timestamp(a["start_time"]) == pd.Timestamp(t["entry_time_utc"])
    a = next(a for a in annotations if a["category"] == "exit")
    assert a["price"] == float(t["exit_price"])
    assert pd.Timestamp(a["start_time"]) == pd.Timestamp(t["exit_time_utc"])
    box = next(a for a in annotations if a["type"] == "box")
    assert box["price_low"] == float(t["fvg_bottom"])
    assert box["price_high"] == float(t["fvg_top"])


def test_navigation_and_no_fvg(trades):
    t = {**trades[1], "fvg_top": 0, "fvg_bottom": 0}
    r = chart_payload([trades[0], t, trades[2]], t["trade_id"])
    assert r["previous_trade_id"] == trades[0]["trade_id"]
    assert r["next_trade_id"] == trades[2]["trade_id"]
    assert not any(a["category"] == "fvg" for a in r["annotations"])


def test_bad_chart_id(trades):
    with pytest.raises(ValueError, match="Invalid trade"):
        chart_payload(trades, "bad")


def test_annotation_validation():
    with pytest.raises(ValueError):
        Annotation(type="script", start_time="bad")
