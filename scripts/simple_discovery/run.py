"""Bounded Development search; native fills, causal account selection, no DB writes."""

import sys, json, hashlib, sqlite3
from pathlib import Path
from decimal import Decimal as D
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.simple_discovery.core import Detector, HYPOTHESES, MODES, bracket, size, NY
from engine.partial_execution import execute
from engine.strategy import Entry
from engine.legacy import reference as ref
from scripts.swing_low_feasibility.core import independent_fill
from scripts.pml_feasibility.core import short_fill

P = ROOT / "work/simple-strategy-discovery-v1"
SOURCE = ROOT / "work/eight-level-reaction-entry-study-v1"


def sha(p):
    with open(p, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def save(name, v):
    (P / name).write_text(
        json.dumps(v, sort_keys=True, indent=2, default=str, allow_nan=False) + "\n"
    )


def write(name, rows):
    (rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)).to_csv(
        P / name, index=False, float_format="%.12g", lineterminator="\n"
    )


def storage():
    c = sqlite3.connect("file:" + str(ROOT / "storage/app.db") + "?mode=ro", uri=True)
    q = {
        "runs": "id,status",
        "event_studies": "id,status,config_hash",
        "strategies": "id,current_version,updated_at",
        "strategy_versions": "id,source_hash",
        "variants": "id",
        "schema_migrations": "version",
        "research_splits": "id",
        "experiment_snapshots": "id,snapshot_hash",
    }
    x = {
        k: c.execute(f"SELECT {cols} FROM {k} ORDER BY 1").fetchall()
        for k, cols in q.items()
    }
    x["reveals"] = c.execute("SELECT * FROM event_study_reveals ORDER BY 1").fetchall()
    c.close()
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, default=str).encode()
    ).hexdigest()


def minimum_loss(ticks):
    """Smallest tick-aligned risk whose net 2R gain exceeds all-in planned loss."""
    cost = D("1.46") + D(".50") * ticks
    risk = (cost // D(".25") + 1) * D(".25")
    return risk * 2 + cost


def main():
    protocol = json.loads((P / "protocol.json").read_text())
    for f, h in protocol["hashes"].items():
        assert sha(ROOT / f) == h
    before = storage()
    identity = json.loads((SOURCE / "source_identity.json").read_text())
    m = json.loads((SOURCE / "reproducibility_manifest.json").read_text())
    assert m["segment"] == "development" and m["status"] == "PASS"
    assert (
        sha(SOURCE / "source_identity.json")
        == m["artifacts"]["source_identity.json"]["sha256"]
    )
    hashes = identity["source_hashes"]
    for f, h in hashes.items():
        assert sha(ROOT / f) == h
    frames = {}
    lo = pd.Timestamp("2020-01-01", tz=NY).tz_convert("UTC")
    hi = pd.Timestamp("2024-01-01", tz=NY).tz_convert("UTC")
    for kind, key in [("bars", "timestamp_utc"), ("minutes", "ts_event")]:
        path = ROOT / "outputs/data" / identity["dataset"]["files"][kind]["name"]
        g = pq.read_table(path, filters=[(key, ">=", lo), (key, "<", hi)]).to_pandas()
        if key not in g:
            g = g.reset_index()
        assert g[key].is_unique and g[key].between(lo, hi, inclusive="left").all()
        if kind == "minutes":
            for c in ["open", "high", "low", "close"]:
                g[c] = g[c].map(lambda x: D(int(x)).scaleb(-9))
        g["date"] = g[key].dt.tz_convert(NY).dt.strftime("%Y-%m-%d")
        frames[kind] = g.sort_values(key)
    days = {}
    for date, g in frames["minutes"].groupby("date"):
        g = g.set_index("ts_event")
        g.index = g.index.as_unit("ns")
        days[date] = g
    sessions = {
        d: tuple(map(pd.Timestamp, v))
        for d, v in identity["calendar"]["sessions"].items()
        if "2020-01-01" <= d < "2024-01-01"
        and pd.Timestamp(v[1]) - pd.Timestamp(v[0]) == pd.Timedelta(hours=6, minutes=30)
    }
    bar_days = {d: g for d, g in frames["bars"].groupby("date")}
    signals = []
    chartbars = []
    for date, (op, cl) in sorted(sessions.items()):
        g = bar_days.get(date, frames["bars"].iloc[:0])
        rth = g[(g.timestamp_utc >= op) & (g.timestamp_utc < cl)]
        det = Detector()
        for b in rth.itertuples():
            signals.extend(dict(**s, session_close=cl) for s in det.update(b))
        chartbars.extend(rth.to_dict("records"))
    assert len({s["signal_id"] for s in signals}) == len(signals)
    write("raw_signals.csv", signals)
    pd.DataFrame(chartbars).to_parquet(P / "chart_bars.parquet", index=False)
    by = {}
    for s in signals:
        by.setdefault((s["hypothesis"], s["date"]), []).append(s)
    print(
        "Frozen signal counts",
        pd.DataFrame(signals).hypothesis.value_counts().to_dict(),
        flush=True,
    )
    cache = {}
    checks = 0

    def fill(s, b, ticks, q):
        nonlocal checks
        key = (s["signal_id"], ticks, q)
        if key in cache:
            return cache[key]
        at = s["entry_time_utc"]
        end = s["session_close"]
        day = days.get(s["date"], pd.DataFrame())
        ix = pd.date_range(at, end, freq="min", inclusive="left")
        missing = ix.difference(day.index)
        cutoff = missing[0] if len(missing) else end
        arr = day.loc[
            (day.index >= at) & (day.index < cutoff), ["open", "high", "low", "close"]
        ].to_numpy(float)
        ind = (independent_fill if s["direction"] == "LONG" else short_fill)(
            arr,
            float(b["entry_price"]),
            float(b["stop_price"]),
            float(b["target_price"]),
            ticks,
            len(ix),
        )
        try:
            native, _ = execute(
                dict(**s, **b),
                day,
                ref.Config(D(".73"), ticks),
                q,
                Entry(s["direction"], b["stop_price"], D(2)),
                None,
                {},
                {},
                end,
            )
        except ValueError as e:
            assert "Missing execution minute" in str(e) and ind is None
            cache[key] = dict(
                status="EXECUTION_DATA_UNAVAILABLE", first_missing_owned_minute=cutoff
            )
            return cache[key]
        assert ind is not None
        i, reason, price, conflict = ind
        sign = D(1) if s["direction"] == "LONG" else D(-1)
        assert native["exit_reason"] == reason and float(native["exit_price"]) == price
        assert native["exit_time_utc"] == at + pd.Timedelta(minutes=i + 1)
        assert native["same_minute_stop_target_conflict"] == conflict
        assert (
            native["net_pnl_usd"]
            == (D(str(price)) - b["entry_price"]) * sign * 2 * q - D("1.46") * q
        )
        assert (
            native["management_event_count"] == 0
            and native["final_stop_price"] == b["stop_price"]
        )
        # Exclude exit-minute wick extremes after a possible fill. Opening is known before exit.
        owned = arr[: i + 1]
        en = float(b["entry_price"])
        adverse = max(
            0,
            (
                en - owned[:-1, 2].min()
                if i and sign == 1
                else owned[:-1, 1].max() - en if i else 0
            ),
            (en - owned[-1, 0]) if sign == 1 else (owned[-1, 0] - en),
        )
        fields = [
            "exit_time_utc",
            "exit_time_ny",
            "exit_reason",
            "exit_price",
            "gross_pnl_usd",
            "commission_usd",
            "net_pnl_usd",
            "result_r",
            "mfe_points",
            "mae_points",
            "mfe_r",
            "mae_r",
            "duration_minutes",
            "same_minute_stop_target_conflict",
        ]
        result = {k: native[k] for k in fields}
        result.update(
            status="COMPLETE",
            adverse_active_points=D(str(adverse)),
            adverse_stop_gap=reason == "STOP"
            and (
                (owned[-1, 0] < float(b["stop_price"]))
                if sign == 1
                else (owned[-1, 0] > float(b["stop_price"]))
            ),
        )
        cache[key] = result
        checks += 1
        return result

    audits = []
    trades = []
    daily = []
    for hyp in HYPOTHESES:
        for ticks in [0, 1, 2]:
            for mode, margin in MODES.items():
                equity = D(500)
                unknown = False
                terminal = None
                for date, (op, cl) in sorted(sessions.items()):
                    before_eq = equity
                    used = False
                    profit = D(0)
                    status = "NO_ELIGIBLE_SIGNAL"
                    n = 0
                    if unknown:
                        status = "ACCOUNT_PATH_UNKNOWN"
                    elif (
                        mode != "ONE_MICRO_DIAGNOSTIC"
                        and equity < margin + minimum_loss(ticks)
                    ):
                        terminal = terminal or date
                        status = "CAPITAL_LOCKOUT"
                    for s in by.get((hyp, date), []):
                        n += 1
                        b = bracket(s, ticks)
                        record = dict(**s, **b, ticks=ticks, mode=mode)
                        if unknown:
                            reason = "ACCOUNT_PATH_UNKNOWN"
                            q = 0
                        elif used:
                            reason = "DAILY_LIMIT_REACHED"
                            q = 0
                        elif s["entry_time_utc"] >= cl:
                            reason = "AT_SESSION_CLOSE"
                            q = 0
                        else:
                            q, reason = size(b, mode, equity)
                        if reason:
                            audits.append(
                                dict(**record, quantity=q, selection_status=reason)
                            )
                            continue
                        used = True
                        f = fill(s, b, ticks, q)
                        if f["status"] != "COMPLETE":
                            status = "EXECUTION_DATA_UNAVAILABLE"
                            profit = None
                            audits.append(
                                dict(
                                    **record,
                                    quantity=q,
                                    selection_status=status,
                                    first_missing_owned_minute=f[
                                        "first_missing_owned_minute"
                                    ],
                                )
                            )
                            if mode != "ONE_MICRO_DIAGNOSTIC":
                                unknown = True
                                equity = None
                            continue
                        profit = f["net_pnl_usd"]
                        margin_breach = (
                            margin is not None
                            and equity
                            - D(".73") * q
                            - f["adverse_active_points"] * 2 * q
                            < margin * q
                        )
                        equity += profit
                        status = (
                            "TRADE_COMPLETE"
                            if not margin_breach
                            else "MARGIN_PATH_UNRESOLVED"
                        )
                        trades.append(
                            dict(
                                **record,
                                quantity=q,
                                **{k: v for k, v in f.items() if k != "status"},
                                planned_loss=b["planned_loss_per_micro"] * q,
                                planned_gain=b["planned_gain_per_micro"] * q,
                                balance_before=before_eq,
                                balance_after=equity,
                                margin_breach=margin_breach,
                                loss_exceeds_75=profit < -75,
                            )
                        )
                        audits.append(
                            dict(**record, quantity=q, selection_status=status)
                        )
                        if margin_breach:
                            unknown = True
                            equity = None
                            profit = None
                    daily.append(
                        dict(
                            hypothesis=hyp,
                            ticks=ticks,
                            mode=mode,
                            date=date,
                            year=int(date[:4]),
                            month=date[:7],
                            raw_signals=n,
                            status=status,
                            net_pnl_usd=(
                                profit
                                if not (status == "ACCOUNT_PATH_UNKNOWN")
                                else None
                            ),
                            balance_before=before_eq,
                            balance_after=equity,
                            terminal_lockout_date=terminal,
                        )
                    )
                print(
                    hyp, ticks, mode, "ending", equity, "unknown", unknown, flush=True
                )
    write("signal_audit.csv", audits)
    write("trades.csv", trades)
    write("daily.csv", daily)
    for f, h in hashes.items():
        assert sha(ROOT / f) == h
    assert storage() == before
    save(
        "execution_verification.json",
        dict(
            segment="development",
            raw_signals=len(signals),
            full_sessions=len(sessions),
            source_bars=len(frames["bars"]),
            source_minutes=len(frames["minutes"]),
            independent_native_fill_checks=checks,
            source_hashes=hashes,
            storage_metadata_sha256=before,
            validation_oos_outcomes_read=False,
            production_execution_changed=False,
        ),
    )


if __name__ == "__main__":
    main()
