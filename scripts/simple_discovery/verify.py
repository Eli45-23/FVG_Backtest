"""Independent signal/account checks and deterministic local artifacts."""

import sys, json
from pathlib import Path
from decimal import Decimal as D
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.simple_discovery.run import P, sha, save, storage
from scripts.simple_discovery.core import MODES, HYPOTHESES


def independent(g):
    p = g.shift(1)
    m = g.shift(2)
    ok = (
        g.is_complete_5m
        & p.is_complete_5m.eq(True)
        & m.is_complete_5m.eq(True)
        & (g.timestamp_utc - p.timestamp_utc).eq(pd.Timedelta(minutes=5))
        & (p.timestamp_utc - m.timestamp_utc).eq(pd.Timedelta(minutes=5))
    )
    out = []
    for side in ["LONG", "SHORT"]:
        if side == "LONG":
            patterns = {
                "TWO_PUSH": (p.close > p.open)
                & (g.close > g.open)
                & (p.close > m.high)
                & (g.close > p.high),
                "OUTSIDE_REVERSAL": (p.close < p.open)
                & (g.close > g.open)
                & (g.low < p.low)
                & (g.close > p.high),
                "INSIDE_BREAK": (p.high < m.high)
                & (p.low > m.low)
                & (g.close > m.high),
            }
        else:
            patterns = {
                "TWO_PUSH": (p.close < p.open)
                & (g.close < g.open)
                & (p.close < m.low)
                & (g.close < p.low),
                "OUTSIDE_REVERSAL": (p.close > p.open)
                & (g.close < g.open)
                & (g.high > p.high)
                & (g.close < p.low),
                "INSIDE_BREAK": (p.high < m.high) & (p.low > m.low) & (g.close < m.low),
            }
        for h, mask in patterns.items():
            for ix in g.index[ok & mask]:
                anchor = (
                    (
                        min(p.loc[ix, "low"], g.loc[ix, "low"])
                        if side == "LONG"
                        else max(p.loc[ix, "high"], g.loc[ix, "high"])
                    )
                    if h == "TWO_PUSH"
                    else (
                        g.loc[ix, "low" if side == "LONG" else "high"]
                        if h == "OUTSIDE_REVERSAL"
                        else m.loc[ix, "low" if side == "LONG" else "high"]
                    )
                )
                out.append(
                    (
                        g.loc[ix, "timestamp_utc"] + pd.Timedelta(minutes=5),
                        h,
                        side,
                        float(anchor),
                    )
                )
    return out


def main():
    raw = pd.read_csv(P / "raw_signals.csv")
    a = pd.read_csv(P / "signal_audit.csv")
    t = pd.read_csv(P / "trades.csv")
    daily = pd.read_csv(P / "daily.csv")
    bars = pd.read_parquet(P / "chart_bars.parquet")
    expected = []
    for _, g in bars.groupby("date"):
        expected += independent(g)
    observed = [
        (pd.Timestamp(r.entry_time_utc), r.hypothesis, r.direction, r.stop_anchor)
        for r in raw.itertuples()
    ]
    assert sorted(expected) == sorted(observed)
    assert (
        raw.signal_id.is_unique and raw.date.between("2020-01-01", "2023-12-31").all()
    )
    assert len(a) == len(raw) * 15
    assert t.groupby(["hypothesis", "ticks", "mode", "date"]).size().max() == 1
    assert daily.groupby(["hypothesis", "ticks", "mode"]).size().eq(1000).all()
    assert daily.date.between("2020-01-01", "2023-12-31").all()
    assert (
        t.planned_loss.le(75 + 1e-8).all() and (t.planned_gain > t.planned_loss).all()
    )
    assert t.quantity.ge(1).all() and t.quantity.eq(t.quantity.astype(int)).all()
    assert ((t.net_pnl_usd - (t.gross_pnl_usd - t.quantity * 1.46)).abs() < 1e-7).all()
    signs = t.direction.map({"LONG": 1, "SHORT": -1})
    assert ((t.entry_price - t.stop_price) * signs - t.risk_points).abs().lt(1e-8).all()
    assert (
        ((t.target_price - t.entry_price) * signs - 2 * t.risk_points)
        .abs()
        .lt(1e-8)
        .all()
    )
    assert (
        pd.to_datetime(t.entry_time_utc, utc=True)
        == pd.to_datetime(t.trigger_start, utc=True) + pd.Timedelta(minutes=5)
    ).all()
    for key, g in a.groupby(["hypothesis", "ticks", "mode"]):
        h, k, mode = key
        ds = daily[
            (daily.hypothesis == h) & (daily.ticks == k) & (daily["mode"] == mode)
        ].set_index("date")
        for date, sigs in g.groupby("date", sort=True):
            eq = ds.loc[date, "balance_before"]
            used = False
            for r in sigs.sort_values("entry_time_utc").itertuples():
                if pd.isna(eq):
                    break
                if used:
                    assert r.selection_status in [
                        "DAILY_LIMIT_REACHED",
                        "ACCOUNT_PATH_UNKNOWN",
                    ]
                    continue
                at = pd.Timestamp(r.entry_time_utc)
                end = pd.Timestamp(r.session_close)
                loss = D(str(r.risk_points)) * 2 + D(".5") * int(k) + D("1.46")
                gain = D(str(r.risk_points)) * 4 - D(".5") * int(k) - D("1.46")
                q = 0
                if at < end and r.risk_points > 0 and loss <= 75 and gain > loss:
                    if mode == "ONE_MICRO_DIAGNOSTIC":
                        q = 1
                    else:
                        q = max(
                            0,
                            min(
                                int(D(75) // loss),
                                int(D(str(round(eq, 2))) // (MODES[mode] + loss)),
                            ),
                        )
                        if mode == "ONE_MICRO_200":
                            q = min(1, q)
                assert r.quantity == q
                if q:
                    assert r.selection_status in [
                        "TRADE_COMPLETE",
                        "EXECUTION_DATA_UNAVAILABLE",
                        "MARGIN_PATH_UNRESOLVED",
                    ]
                    used = True
        if mode != "ONE_MICRO_DIAGNOSTIC":
            tr = t[(t.hypothesis == h) & (t.ticks == k) & (t["mode"] == mode)]
            assert (
                tr.quantity * float(MODES[mode]) + tr.planned_loss
                <= tr.balance_before + 1e-8
            ).all()
            eq = 500.0
            for r in ds.reset_index().itertuples():
                if pd.isna(r.net_pnl_usd):
                    break
                assert abs(r.balance_before - eq) < 1e-7
                eq += r.net_pnl_usd
                assert abs(r.balance_after - eq) < 1e-7
    verification = json.loads((P / "execution_verification.json").read_text())
    assert storage() == verification["storage_metadata_sha256"]
    protocol = json.loads((P / "protocol.json").read_text())
    for f, h in protocol["hashes"].items():
        assert sha(ROOT / f) == h
    for f, h in verification["source_hashes"].items():
        assert sha(ROOT / f) == h
    artifacts = {
        f.name: dict(sha256=sha(f), bytes=f.stat().st_size)
        for f in sorted(P.iterdir())
        if f.suffix in [".json", ".csv", ".parquet", ".html", ".md"]
        and f.name not in ["reproducibility_manifest.json", "determinism_first.json"]
    }
    first = P / "determinism_first.json"
    if not first.exists():
        save("determinism_first.json", artifacts)
        print("First verification passed; repeat run/report/verify.")
        return
    assert json.loads(first.read_text()) == artifacts, "Artifact rerun mismatch"
    save(
        "reproducibility_manifest.json",
        dict(
            status="PASS",
            segment="development",
            entry_records=len(raw),
            independent_signals=len(expected),
            completed_scenario_trades=len(t),
            independent_native_fill_checks=verification[
                "independent_native_fill_checks"
            ],
            byte_identical_rerun=True,
            validation_oos_outcomes_read=False,
            storage_metadata_sha256=storage(),
            code_hashes={
                str(f.relative_to(ROOT)): sha(f)
                for f in sorted((ROOT / "scripts/simple_discovery").glob("*"))
                if f.is_file()
            },
            artifacts=artifacts,
        ),
    )
    print(
        "PASS: independent signals, independent daily selection, native fill checks, exact rerun, preserved sources/storage"
    )


if __name__ == "__main__":
    main()
