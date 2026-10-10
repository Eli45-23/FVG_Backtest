from decimal import Decimal as D
from types import SimpleNamespace
import pandas as pd
import pytest
from scripts.simple_discovery.core import Detector, bracket, size

T = pd.Timestamp("2020-01-02 09:30", tz="America/New_York").tz_convert("UTC")


def bar(i, o, h, l, c, complete=True):
    return SimpleNamespace(
        timestamp_utc=T + pd.Timedelta(minutes=5 * i),
        open=D(str(o)),
        high=D(str(h)),
        low=D(str(l)),
        close=D(str(c)),
        is_complete_5m=complete,
    )


PATTERNS = {
    "TWO_PUSH": [(100, 102, 99, 101), (101, 105, 100, 104), (104, 108, 103, 107)],
    "OUTSIDE_REVERSAL": [(103, 105, 99, 100), (103, 104, 99, 100), (100, 106, 98, 105)],
    "INSIDE_BREAK": [(100, 105, 95, 101), (101, 104, 96, 100), (100, 108, 99, 107)],
}


@pytest.mark.parametrize("name", PATTERNS)
@pytest.mark.parametrize("mirror", [False, True])
def test_patterns_mirror_confirmation_and_causality(name, mirror):
    d = Detector()
    data = PATTERNS[name]
    if mirror:
        data = [(200 - o, 200 - l, 200 - h, 200 - c) for o, h, l, c in data]
    assert d.update(bar(0, *data[0])) == []
    assert d.update(bar(1, *data[1])) == []
    found = [s for s in d.update(bar(2, *data[2])) if s["hypothesis"] == name]
    assert len(found) == 1 and found[0]["direction"] == ("SHORT" if mirror else "LONG")
    assert found[0]["entry_time_utc"] == T + pd.Timedelta(minutes=15)
    econ = bracket(found[0], 1)
    assert abs(econ["target_price"] - econ["entry_price"]) == 2 * econ["risk_points"]
    assert econ["planned_loss_per_micro"] == 2 * econ["risk_points"] + D("1.96")
    assert (econ["stop_price"] * 4) % 1 == 0


@pytest.mark.parametrize("missing", [True, False])
def test_missing_or_incomplete_breaks_continuity(missing):
    d = Detector()
    data = PATTERNS["TWO_PUSH"]
    d.update(bar(0, *data[0]))
    d.update(bar(1, *data[1], complete=missing))
    assert d.update(bar(3 if missing else 2, *data[2])) == []


def econ(risk):
    return dict(
        risk_points=D(str(risk)),
        planned_loss_per_micro=D(str(risk)) * 2 + D("1.96"),
        planned_gain_per_micro=D(str(risk)) * 4 - D("1.96"),
    )


@pytest.mark.parametrize(
    "mode,q",
    [
        ("ONE_MICRO_DIAGNOSTIC", 1),
        ("ONE_MICRO_200", 1),
        ("RISK_SIZED_200", 2),
        ("RISK_SIZED_400", 1),
        ("RISK_SIZED_4763", 0),
    ],
)
def test_whole_contract_margin_plus_risk(mode, q):
    actual, reason = size(econ(10), mode, D(500))
    assert actual == q
    if actual:
        assert actual * econ(10)["planned_loss_per_micro"] <= 75


@pytest.mark.parametrize(
    "risk,reason",
    [
        (0, "NON_POSITIVE_RISK"),
        (37, "RISK_BUDGET"),
        (0.5, "NET_REWARD_NOT_GREATER_THAN_RISK"),
    ],
)
def test_budget_and_net_reward(risk, reason):
    assert size(econ(risk), "ONE_MICRO_DIAGNOSTIC", D(500)) == (0, reason)


def test_capital_declines_no_implicit_refunding():
    assert size(econ(10), "RISK_SIZED_200", D(500))[0] == 2
    assert size(econ(10), "RISK_SIZED_200", D(220))[0] == 0
    assert size(econ(10), "RISK_SIZED_200", D(-1))[0] == 0


def test_equality_does_not_break_inside_mother():
    d = Detector()
    data = PATTERNS["INSIDE_BREAK"]
    d.update(bar(0, *data[0]))
    d.update(bar(1, *data[1]))
    assert not any(
        s["hypothesis"] == "INSIDE_BREAK" for s in d.update(bar(2, 100, 106, 99, 105))
    )


@pytest.mark.parametrize("ticks,minimum", [(0, "4.46"), (1, "5.96"), (2, "7.46")])
def test_terminal_capacity_respects_net_reward_condition(ticks, minimum):
    from scripts.simple_discovery.run import minimum_loss

    assert minimum_loss(ticks) == D(minimum)


def test_month_block_evidence_deterministic_and_hides_unknown():
    from scripts.simple_discovery.report import block_evidence

    g = pd.DataFrame(
        {
            "month": ["2020-01", "2020-01", "2020-02", "2020-02"],
            "net_pnl_usd": [1.0, 0.0, 2.0, 0.0],
        }
    )
    assert block_evidence(g) == block_evidence(g)
    assert block_evidence(g)["ci_low"] > 0
    g.loc[0, "net_pnl_usd"] = float("nan")
    assert block_evidence(g)["evidence_status"] == "INCOMPLETE"
