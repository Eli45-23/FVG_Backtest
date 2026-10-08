import sys, json, hashlib
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
import numpy as np, pandas as pd
from analyze import R, clustered_many, LEVELS, folder, K
from engine.research.statistics import clustered, benjamini_hochberg


def test_vectorized_cluster_matches_validated_engine():
    rng = np.random.default_rng(33)
    for n in [1, 2, 11, 100]:
        f = pd.DataFrame(
            {
                "date": np.repeat(np.arange(n), 3),
                "up_a1": rng.integers(0, 2, n * 3),
                "down_a1": rng.integers(0, 2, n * 3),
                "b_up_a1": rng.random(n * 3),
                "b_down_a1": rng.random(n * 3),
            }
        )
        out = clustered_many(f, ["up_a1", "down_a1"])
        for c in ["up_a1", "down_a1"]:
            ref = clustered(f.date, f[c], f["b_" + c])
            v = out[c]
            for k in [
                "events",
                "unique_dates",
                "event_probability",
                "baseline_probability",
                "effect",
            ]:
                assert np.isclose(v[k], ref[k])
            if ref["p_value"] is not None:
                assert v["p_value"] == ref["p_value"]
                np.testing.assert_allclose([v["ci_low"], v["ci_high"]], ref["ci95"])


def test_date_replication_not_independence():
    f = pd.DataFrame({"date": ["a", "b"], "up_a1": [1.0, 0.0], "b_up_a1": [0.5, 0.5]})
    a = clustered_many(f, ["up_a1"])["up_a1"]
    b = clustered_many(pd.concat([f] * 10), ["up_a1"])["up_a1"]
    for k in ["unique_dates", "effect", "ci_low", "ci_high", "p_value"]:
        assert a[k] == b[k]


def test_primary_family_complete():
    f = pd.read_csv(R / "all_levels_primary_outcomes.csv")
    assert len(f) == 12 * len(K) * 2 * 2
    assert not f.duplicated(
        ["level", "interaction", "stored_direction", "measured_direction"]
    ).any()
    np.testing.assert_allclose(
        f.bh_q_value, benjamini_hochberg(f.p_for_correction.tolist())
    )


def test_source_hashes_preserved():
    for p, v in json.loads((R / "preserved_source_manifest.json").read_text()).items():
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        assert h.hexdigest() == v["sha256"]


def test_all_events_development_and_unique():
    for level in LEVELS[:10]:
        e = pd.read_parquet(folder(level) / "events.parquet")
        assert e.event_id.is_unique
        assert e.date.between("2020-01-01", "2023-12-31").all()
        for h in ["5", "10", "15", "30", "60", "session_close"]:
            o = pd.read_parquet(
                folder(level) / f"outcomes_{h}.parquet",
                columns=["event_id", "complete", "up_a1"],
            )
            assert set(o.event_id) == set(e.event_id)
            assert o.loc[~o.complete, "up_a1"].isna().all()


def test_pm_midnight_and_missing_policy():
    cov = pd.read_csv(R / "premarket_coverage.csv")
    assert cov.expected.eq(114).all()
    for level in ["PMH", "PML"]:
        c = json.loads((folder(level) / "configuration.json").read_text())[
            "source_config"
        ]
        assert c["session"]["premarket_start"] == "00:00"
        assert c["session"]["premarket_end"] == "09:30"
        e = pd.read_parquet(folder(level) / "events.parquet")
        assert set(e.date) <= set(cov.loc[cov.available, "date"])
        assert (
            pd.to_datetime(e.level_available_at, utc=True)
            .dt.tz_convert("America/New_York")
            .dt.strftime("%H:%M")
            .eq("09:30")
            .all()
        )


def test_causal_audit_zero_failures():
    f = pd.read_csv(R / "causal_audit.csv")
    assert len(f) == 10
    assert f.failures.eq(0).all()
    assert f.charts.ge(8).all()


def test_direction_and_threshold_consistency():
    for level in LEVELS[:10]:
        o = pd.read_parquet(folder(level) / "outcomes_30.parquet")
        g = o[o.complete & (o.atr14 > 0)]
        np.testing.assert_array_equal(
            g.up_a1.astype(bool), (g.maximum_high_excursion >= g.atr14)
        )
        np.testing.assert_array_equal(
            g.down_a1.astype(bool), (g.maximum_low_excursion >= g.atr14)
        )
        e = pd.read_parquet(folder(level) / "events.parquet")
        f = e[e.interaction_type == "BREAK_FAILED_NEXT_CANDLE_HOLD"]
        assert (f.direction != f.logical_direction).all()


def test_decimal_thresholds_and_times_present():
    for level in LEVELS[:10]:
        o = pd.read_parquet(folder(level) / "outcomes_30.parquet")
        g = o[o.complete & (o.atr14 > 0)]
        for side, exc in [
            ("up", "maximum_high_excursion"),
            ("down", "maximum_low_excursion"),
        ]:
            for t in [0.25, 0.5, 0.75, 1, 1.5, 2, 3]:
                k = str(t).replace(".", "p")
                v = g[f"{side}_a{k}"]
                assert v.notna().all()
                np.testing.assert_array_equal(v.astype(bool), g[exc] >= g.atr14 * t)
                tm = g[f"{side}_t{k}"]
                assert tm[v == 1].between(1, 30).all()
                assert tm[v == 0].isna().all()


def test_primary_not_empty_and_context_anchor_agrees():
    p = pd.read_csv(R / "all_levels_primary_outcomes.csv")
    assert (p.unique_dates > 30).sum() > 400
    for level in LEVELS[:10]:
        o = pd.read_parquet(folder(level) / "outcomes_30.parquet")
        g = o[
            (o.interaction_type == "BREAK_ACCEPTANCE")
            & (o.direction == "DOWN")
            & o.complete
            & (o.atr14 > 0)
        ]
        r = clustered(g.date, g.down_a1, g.b_down_a1)
        x = p[
            (p.level == level)
            & (p.interaction == "BREAK_ACCEPTANCE")
            & (p.stored_direction == "DOWN")
            & (p.measured_direction == "DOWN")
        ].iloc[0]
        assert np.isclose(x.effect, r["effect"])
        assert np.isclose(x.p_value, r["p_value"])


def test_independent_pivots():
    f = pd.read_csv(R / "independent_swing_confirmation_audit.csv")
    assert len(f) == 70081
    assert f.correct.all()


def test_zone_absence_is_reported_as_blocker():
    a = json.loads((R / "foundation_audit.json").read_text())
    assert a["frames"]["4h"]["atr_available"] == 0
    assert a["frames"]["4h"]["zones"] == 0
    for level in LEVELS[10:]:
        assert (
            json.loads((folder(level) / "configuration.json").read_text())["status"]
            == "BLOCKED_NO_ELIGIBLE_ZONES"
        )
