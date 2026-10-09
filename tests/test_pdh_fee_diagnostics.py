"""Synthetic tests only: no market data, database, Validation or OOS reads."""

import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from pdh_fee_corrected_report import drawdown, pf
from pdh_fee_corrected_development import FEE
from decimal import Decimal as D


def test_actual_fee_components():
    keys = [
        "commission_per_side_usd",
        "exchange_per_side_usd",
        "clearing_per_side_usd",
        "nfa_per_side_usd",
    ]
    assert sum(D(FEE[k]) for k in keys) == D(".73")
    assert D(FEE["round_trip_per_micro_usd"]) == D("1.46")
    assert D("1.46") * 58 == D("84.68")


@pytest.mark.parametrize(
    "values,expected",
    [
        ([-2, -3], (5.0, 0, 2)),
        ([3, -2, -4, 5], (6.0, 1, 3)),
        ([1, 2], (0.0, 0, 0)),
        ([], (0.0, 0, 0)),
    ],
)
def test_closed_drawdown_includes_initial_zero(values, expected):
    assert drawdown(values) == expected


def test_net_profit_factor_accounts_for_fee_changed_sign():
    gross = np.array([1.0, 10.0, -5.0])
    net = gross - 1.46
    assert pf(gross) == 2.2
    assert pf(net) == pytest.approx(8.54 / 6.92)


def test_no_losses_returns_null_pf():
    assert pf([1, 2]) is None


def test_fee_r_uses_each_original_risk_not_average_risk():
    risks = np.array([10.0, 100.0])
    gross = np.array([20.0, -200.0])
    net = gross - 1.46
    assert np.mean(gross / (2 * risks) - net / (2 * risks)) == pytest.approx(
        np.mean(1.46 / (2 * risks))
    )
    assert np.mean(1.46 / (2 * risks)) != pytest.approx(1.46 / (2 * np.mean(risks)))


def test_peak_to_trough_signed_attribution():
    pnl = np.array([10.0, -8.0, 2.0, -6.0, 20.0])
    dd, peak, bottom = drawdown(pnl)
    assert (dd, peak, bottom) == (12.0, 1, 4)
    # A high-risk winner during the drawdown offsets rather than adds to depth.
    selected = np.array([False, True, True, False, False])
    assert -pnl[peak:bottom][selected[peak:bottom]].sum() == 6
