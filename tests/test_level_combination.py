from types import SimpleNamespace as S
import pandas as pd
import pytest
from scripts.level_combination.core import context, wait_entry

T = pd.Timestamp("2020-03-09 14:00", tz="UTC")


def event(**kw):
    return dict(
        timestamp_utc=T,
        session_close=T + pd.Timedelta(minutes=20),
        level_type="O5H",
        direction="UP",
        level_price=100,
        price_at_event=101,
        atr14=10,
        high=102,
        low=99,
        barrier_price=110,
        **kw
    )


def level(name, price, minutes=0, available=True):
    return dict(
        level=name,
        price=price,
        availability=T + pd.Timedelta(minutes=minutes),
        available=available,
    )


def bar(i, c=112, lo=111, hi=113, complete=True):
    return S(
        timestamp_utc=T + pd.Timedelta(minutes=5 * i),
        open=c,
        close=c,
        high=hi,
        low=lo,
        is_complete_5m=complete,
    )


def test_future_levels_not_context():
    c = context(event(), [level("O5H", 100), level("O15H", 110, 5)])
    assert c["known_level_count"] == 1 and c["obstacle_count"] == 0


def test_unavailable_not_context():
    assert (
        context(event(), [level("PMH", 110, available=False)])["known_level_count"] == 0
    )


def test_nearby_boundary_and_far_exclusion():
    c = context(event(), [level("PDH", 111), level("PMH", 111.25)])
    assert c["obstacle_count"] == 1 and c["barrier_price"] == 111


def test_downside_mirror():
    e = event()
    e.update(direction="DOWN", price_at_event=99, barrier_price=90)
    c = context(e, [level("PDL", 90)])
    assert c["barrier_price"] == 90
    w, r = wait_entry(e, [bar(0, c=89, lo=88, hi=92), bar(1, c=88, lo=87, hi=89)])
    assert r == "CONFIRMED" and w["price_at_event"] == 88


def test_atr_missing_retained_as_unknown():
    e = event()
    e["atr14"] = None
    c = context(e, [level("PDH", 110)])
    assert c["cluster_group"] == "UNKNOWN" and c["known_level_count"] == 1


def test_exact_coincident_distinct_level_is_cluster_not_obstacle():
    c = context(event(), [level("O5H", 100), level("PMH", 100)])
    assert (
        c["coincident_levels"] == 1
        and c["cluster_count"] == 1
        and c["obstacle_count"] == 0
    )


def test_cluster_is_not_claim_of_candle_contact():
    c = context(event(), [level("PDH", 110)])
    assert c["cluster_count"] == 1 and c["cluster_candle_contacts"] == 0


def test_clearance_then_full_hold_entry_close():
    w, r = wait_entry(event(), [bar(0, lo=105), bar(1)])
    assert r == "CONFIRMED" and w["timestamp_utc"] == T + pd.Timedelta(minutes=10)


def test_clearance_alone_no_entry():
    e = event()
    e["session_close"] = T + pd.Timedelta(minutes=5)
    assert wait_entry(e, [bar(0)])[1] == "SESSION_ENDED"


def test_touching_barrier_not_full_hold():
    e = event()
    e["session_close"] = T + pd.Timedelta(minutes=10)
    assert wait_entry(e, [bar(0), bar(1, lo=110)])[0] is None


@pytest.mark.parametrize("rows", [[bar(1)], [bar(0), bar(2)], [bar(0, complete=False)]])
def test_broken_adjacency_cancels(rows):
    assert wait_entry(event(), rows) == (None, "MISSING_OR_INCOMPLETE_ADJACENCY")


@pytest.mark.parametrize("close", [99, 100])
def test_root_reclaimed_cancels(close):
    assert wait_entry(event(), [bar(0, c=close, lo=98)])[1] == "ROOT_RECLAIMED"


def test_later_outcomes_do_not_change_confirmation():
    rows = [bar(0), bar(1)]
    assert wait_entry(event(), rows) == wait_entry(event(), rows + [bar(2, c=1, lo=0)])


def test_old_completed_signal_candle_not_used_for_hold():
    w, r = wait_entry(event(), [bar(-1), bar(0), bar(1)])
    assert w["timestamp_utc"] == T + pd.Timedelta(minutes=10)


def test_never_beyond_session():
    e = event()
    e["session_close"] = T + pd.Timedelta(minutes=5)
    assert wait_entry(e, [bar(0), bar(1)])[1] == "SESSION_ENDED"


def test_bh_full_family_and_order():
    import numpy as np
    from scripts.level_combination.report import bh

    p = [0.001, 0.5, 0.01] + [1] * 29
    q = bh(p)
    assert q[0] == 0.032 and q[2] == 0.16 and q[1] == 1
    assert np.array_equal(q, bh(p))


def test_date_cluster_inference_deterministic_and_equal_dates():
    from scripts.level_combination.report import inference

    df = pd.DataFrame({"date": ["a"] * 100 + ["b"], "effect": [1] * 100 + [-1]})
    a = inference(df)
    assert a["effect"] == 0 and a["dates"] == 2 and a == inference(df)


def test_empty_inference_not_positive_evidence():
    from scripts.level_combination.report import inference

    a = inference(pd.DataFrame(columns=["date", "effect"]))
    assert a["effect"] is None and a["p_value"] == 1


def test_signal_at_session_close_has_no_future_waiting_window():
    e = event()
    e["session_close"] = T
    assert wait_entry(e, [bar(0), bar(1)]) == (None, "SESSION_ENDED")
