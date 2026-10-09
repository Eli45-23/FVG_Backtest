import pytest
from scripts.o15l_validation.gate import classify
from scripts.o15l_validation.detect import load_bars

P = {"min_trades": 30, "min_dates": 30, "max_drawdown_r": 7.031524868463503}
M = {
    "trades": 50,
    "unique_dates": 45,
    "net_usd": 100,
    "avg_net_r": 0.1,
    "profit_factor": 1.2,
    "losses": 20,
    "wins": 30,
    "max_dd_r": 5,
}
I = {"mean_r_ci_low": 0.01}


def test_support():
    assert (
        classify(M, I, 0, P)["classification"]
        == "VALIDATION_SUPPORTS_FROZEN_HYPOTHESIS"
    )


def test_interval_crosses_zero_is_conditional():
    assert (
        classify(M, {"mean_r_ci_low": -0.01}, 0, P)["classification"]
        == "CONDITIONAL_VALIDATION_EVIDENCE"
    )


def test_missing_execution_overrides_profit():
    assert classify(M, I, 1, P)["classification"] == "INCONCLUSIVE_INTEGRITY"


@pytest.mark.parametrize("key,value", [("trades", 29), ("unique_dates", 29)])
def test_small_sample(key, value):
    assert (
        classify({**M, key: value}, I, 0, P)["classification"] == "INCONCLUSIVE_SAMPLE"
    )


@pytest.mark.parametrize(
    "key,value",
    [("net_usd", 0), ("avg_net_r", 0), ("profit_factor", 1), ("max_dd_r", 7.031525)],
)
def test_each_economic_condition_required(key, value):
    assert (
        classify({**M, key: value}, I, 0, P)["classification"]
        == "VALIDATION_GATE_FAILED"
    )


def test_oos_decode_rejected_before_file_access():
    with pytest.raises(AssertionError):
        load_bars("2024-01-01", "2025-01-02")


def test_zero_loss_pf_handled():
    assert classify({**M, "losses": 0, "profit_factor": None}, I, 0, P)["checks"][
        "net_pf_above_one"
    ]
