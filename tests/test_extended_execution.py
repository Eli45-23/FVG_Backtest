from decimal import Decimal as D
import pandas as pd
import pytest
from engine.runner import RunConfig, run
from engine.timeframes import aggregate
from engine.canonical import dumps

SOURCE = """from engine.strategy import Entry
from decimal import Decimal as D
class Strategy:
    def on_bar(self,ctx,p):
        if ctx.bar.time < '10:00': return Entry('LONG',ctx.bar.close-D('1'),D('1'))
"""


def data():
    times = pd.date_range("2020-01-06 14:30", periods=390, freq="min", tz="UTC")
    raw = pd.DataFrame(
        dict(
            ts_event=times,
            open=100_000_000_000,
            high=102_000_000_000,
            low=99_500_000_000,
            close=100_000_000_000,
            volume=1,
        )
    )
    return dict(minutes=raw, bars=aggregate(raw, "5m"))


def config(**kw):
    return RunConfig(
        start="2020-01-06",
        end="2020-01-07",
        dataset_profile="research_2020_2026",
        execution_mode="extended_v1",
        **kw,
    )


@pytest.mark.parametrize("limit,expected", [(1, 1), (2, 2), (3, 3), (None, 6)])
def test_sequential_daily_limits(limit, expected):
    r = run(SOURCE, {}, config(max_trades_per_day=limit), data=data())
    assert len(r["trades"]) == expected
    assert [t["trade_sequence_number"] for t in r["trades"]] == list(
        range(1, expected + 1)
    )
    if limit:
        assert "DAILY_TRADE_LIMIT" in {a["reason"] for a in r["audit"]}


def test_position_open_audit():
    source = SOURCE.replace("D('1'),D('1')", "D('10'),D('2')")
    r = run(source, {}, config(max_trades_per_day=None), data=data())
    assert len(r["trades"]) == 1 and "POSITION_OPEN" in {
        a["reason"] for a in r["audit"]
    }


def test_fixed_dollar_floor_and_zero():
    r = run(
        SOURCE,
        {},
        config(sizing_mode="FIXED_DOLLAR_RISK", risk_budget="9"),
        data=data(),
    )
    assert r["trades"][0]["final_quantity"] == 4
    r = run(
        SOURCE,
        {},
        config(sizing_mode="FIXED_DOLLAR_RISK", risk_budget="1"),
        data=data(),
    )
    assert not r["trades"] and r["audit"][0]["reason"] == "ZERO_RISK_QUANTITY"


def test_multi_frames_only_confirmed_and_repeatable():
    source = SOURCE.replace(
        "if ctx.bar.time < '10:00':",
        "assert all(b.timestamp < ctx.timestamp for b in ctx.frames.values())\n        if ctx.bar.time < '10:00':",
    )
    a = run(source, {}, config(timeframe="15m", max_trades_per_day=None), data=data())
    b = run(source, {}, config(timeframe="15m", max_trades_per_day=None), data=data())
    assert len(a["trades"]) == 2 and dumps(a) == dumps(b)
