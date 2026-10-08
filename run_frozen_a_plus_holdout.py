from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import date
from decimal import Decimal as D
from pathlib import Path

import exchange_calendars as xc
import pandas as pd
import pyarrow.parquet as pq

from engine.canonical import digest
from engine.runner import run, RunConfig
import engine.runner as runner
from engine.legacy import reference as ref


ROOT = Path(
    "/Users/DayTrade/Documents/Codex/2026-10-06/"
    "1-connect-to-databento-2-request"
)

ARTIFACTS = ROOT / "storage/artifacts"

EXPANDED_MINUTES = ROOT / (
    "outputs/data/"
    "GLBX.MDP3_MNQ.v.0_ohlcv-1m_2020-01-01_2026-10-06.parquet"
)

EXPANDED_BARS = ROOT / (
    "outputs/data/"
    "MNQ_5m_2020-01-01_2026-10-06.parquet"
)

REPORT_DIR = ROOT / "work/a_plus_v1_holdout"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


DEGRADED_WEEKDAYS = {
    "2020-02-27",
    "2020-02-28",
    "2020-05-05",
    "2020-06-30",
    "2020-07-01",
}


# ============================================================
# HELPERS
# ============================================================

def dec(v):
    return D(str(v))


def trade_date(t):
    value = t.get("entry_time_ny") or t.get("second_bar_time_ny")
    return str(value)[:10]


def net(t):
    return dec(t["net_pnl_usd"])


def result_r(t):
    return float(t["result_r"])


def risk_points(t):
    return float(t["risk_points"])


def performance(trades):
    trades = list(trades)

    pnls = [net(t) for t in trades]
    rs = [result_r(t) for t in trades]

    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]

    gross_profit = sum(wins, D(0))
    gross_loss = abs(sum(losses, D(0)))

    pf = (
        float(gross_profit / gross_loss)
        if gross_loss != 0
        else (math.inf if gross_profit > 0 else None)
    )

    equity = D(0)
    peak = D(0)
    max_dd = D(0)

    for x in pnls:
        equity += x
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)

    return {
        "trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": (
            100 * len(wins) / len(trades)
            if trades else None
        ),
        "net_pnl_usd": float(sum(pnls, D(0))),
        "profit_factor": pf,
        "average_r": (
            sum(rs) / len(rs)
            if rs else None
        ),
        "total_r": sum(rs),
        "max_drawdown_usd": float(max_dd),
    }


def grouped(trades, key):
    groups = defaultdict(list)

    for t in trades:
        groups[str(key(t))].append(t)

    return {
        name: performance(rows)
        for name, rows in sorted(groups.items())
    }


def time_bin(t):
    ts = pd.Timestamp(t["second_bar_time_ny"])

    minute = ts.hour * 60 + ts.minute

    if 570 <= minute < 600:
        return "09:30-09:59"
    if 600 <= minute < 630:
        return "10:00-10:29"
    if 630 <= minute < 660:
        return "10:30-10:59"

    return ts.strftime("%H:%M")


def risk_bin(t):
    r = risk_points(t)

    if r < 25:
        return "0-25"
    if r < 50:
        return "25-50"
    if r < 75:
        return "50-75"
    if r < 100:
        return "75-100"
    if r < 150:
        return "100-150"
    if r < 200:
        return "150-200"

    return "200+"


def report(name, result):
    trades = result["trades"]

    return {
        "name": name,
        "overall": performance(trades),
        "year": grouped(
            trades,
            lambda t: pd.Timestamp(
                t["entry_time_ny"]
            ).year,
        ),
        "direction": grouped(
            trades,
            lambda t: t["direction"],
        ),
        "time": grouped(
            trades,
            time_bin,
        ),
        "risk": grouped(
            trades,
            risk_bin,
        ),
        "weekday": grouped(
            trades,
            lambda t: pd.Timestamp(
                t["entry_time_ny"]
            ).day_name(),
        ),
        "degraded_date_trades": [
            {
                "date": trade_date(t),
                "direction": t["direction"],
                "entry_time_ny": str(t["entry_time_ny"]),
                "net_pnl_usd": float(net(t)),
                "result_r": result_r(t),
            }
            for t in trades
            if trade_date(t) in DEGRADED_WEEKDAYS
        ],
    }


def show(title, r):
    o = r["overall"]

    print()
    print("=" * 78)
    print(title)
    print("=" * 78)

    print(f"Trades:        {o['trades']}")
    print(f"Wins/Losses:   {o['wins']} / {o['losses']}")
    print(
        "Win rate:      "
        + (
            f"{o['win_rate_pct']:.3f}%"
            if o["win_rate_pct"] is not None
            else "N/A"
        )
    )
    print(f"Net P&L:       ${o['net_pnl_usd']:,.2f}")

    pf = o["profit_factor"]

    print(
        "Profit factor: "
        + (
            f"{pf:.3f}"
            if pf is not None and math.isfinite(pf)
            else str(pf)
        )
    )

    print(
        "Average R:     "
        + (
            f"{o['average_r']:.3f}"
            if o["average_r"] is not None
            else "N/A"
        )
    )

    print(f"Total R:       {o['total_r']:.3f}")
    print(f"Max drawdown:  ${o['max_drawdown_usd']:,.2f}")

    print()
    print("YEAR")

    for k, v in r["year"].items():
        print(
            f"  {k}: "
            f"{v['trades']} trades | "
            f"WR {v['win_rate_pct']:.2f}% | "
            f"${v['net_pnl_usd']:,.2f} | "
            f"PF {v['profit_factor']:.3f} | "
            f"AvgR {v['average_r']:.3f} | "
            f"DD ${v['max_drawdown_usd']:,.2f}"
        )

    print()
    print("DIRECTION")

    for k, v in r["direction"].items():
        print(
            f"  {k}: "
            f"{v['trades']} | "
            f"WR {v['win_rate_pct']:.2f}% | "
            f"${v['net_pnl_usd']:,.2f} | "
            f"PF {v['profit_factor']:.3f} | "
            f"AvgR {v['average_r']:.3f}"
        )

    print()
    print("TIME")

    for k, v in r["time"].items():
        print(
            f"  {k}: "
            f"{v['trades']} | "
            f"WR {v['win_rate_pct']:.2f}% | "
            f"${v['net_pnl_usd']:,.2f} | "
            f"PF {v['profit_factor']:.3f} | "
            f"AvgR {v['average_r']:.3f}"
        )

    print()
    print("RISK")

    for k, v in r["risk"].items():
        print(
            f"  {k}: "
            f"{v['trades']} | "
            f"WR {v['win_rate_pct']:.2f}% | "
            f"${v['net_pnl_usd']:,.2f} | "
            f"PF {v['profit_factor']:.3f} | "
            f"AvgR {v['average_r']:.3f}"
        )

    print()
    print("WEEKDAY")

    for k, v in r["weekday"].items():
        print(
            f"  {k}: "
            f"{v['trades']} | "
            f"WR {v['win_rate_pct']:.2f}% | "
            f"${v['net_pnl_usd']:,.2f} | "
            f"PF {v['profit_factor']:.3f} | "
            f"AvgR {v['average_r']:.3f}"
        )

    print()

    degraded = r["degraded_date_trades"]

    print(
        "Trades on Databento degraded weekday dates: "
        f"{len(degraded)}"
    )

    for t in degraded:
        print(
            f"  {t['date']} | "
            f"{t['direction']} | "
            f"${t['net_pnl_usd']:.2f} | "
            f"{t['result_r']:.3f}R"
        )


# ============================================================
# FIND EXACT FROZEN A+ DEVELOPMENT RUN
# ============================================================

print("Searching immutable Lab artifacts for frozen A+ v1...")

candidates = []

for result_path in ARTIFACTS.glob("*/result.json"):
    try:
        value = json.loads(result_path.read_text())
    except Exception:
        continue

    trades = value.get("trades")

    if not isinstance(trades, list):
        continue

    if len(trades) != 41:
        continue

    try:
        pnl = sum(
            dec(t["net_pnl_usd"])
            for t in trades
        )
    except Exception:
        continue

    if pnl != D("2299.5"):
        continue

    root = result_path.parent
    request = root / "request.json"
    config = root / "config.json"

    if request.exists() and config.exists():
        candidates.append(
            (
                result_path.stat().st_mtime,
                root,
                value,
                json.loads(request.read_text()),
                json.loads(config.read_text()),
            )
        )


if not candidates:
    raise RuntimeError(
        "Could not locate the frozen 41-trade / +$2,299.50 "
        "A+ v1 artifact. No holdout was run."
    )


candidates.sort(reverse=True, key=lambda x: x[0])

_, frozen_root, frozen_result, request, frozen_config = candidates[0]

print(f"Found {len(candidates)} matching saved artifact(s).")
print(f"Selected: {frozen_root}")
print(f"Run ID:   {frozen_root.name}")


source = request["source"]
params = request["parameters"]
settings = request["settings"]


# ============================================================
# VERIFY FROZEN SOURCE / PARAMETERS
# ============================================================

if "source_hash" in frozen_config:
    import hashlib

    actual_source_hash = hashlib.sha256(
        source.encode()
    ).hexdigest()

    if actual_source_hash != frozen_config["source_hash"]:
        raise RuntimeError(
            "Frozen strategy source hash mismatch. "
            "No holdout was run."
        )


print()
print("Frozen source hash verified.")
print("Frozen parameters:")
print(json.dumps(params, indent=2, sort_keys=True))


# ============================================================
# REPRODUCE DEVELOPMENT RESULT EXACTLY BEFORE OOS
# ============================================================

print()
print("=" * 78)
print("REPRODUCING ORIGINAL 2024-2026 FROZEN DEVELOPMENT RUN")
print("=" * 78)

reproduced = run(
    source,
    params,
    RunConfig(**settings),
)

expected_digest = digest(frozen_result)
actual_digest = digest(reproduced)

print(f"Saved result digest:      {expected_digest}")
print(f"Reproduced result digest: {actual_digest}")

if actual_digest != expected_digest:
    raise RuntimeError(
        "Frozen 2024-2026 result did NOT reproduce exactly. "
        "Stopping before revealing 2020-2023."
    )

print("EXACT REPRODUCTION: PASSED")


# ============================================================
# LOAD EXPANDED DATA
# ============================================================

print()
print("Loading expanded 2020-2026 data...")

minutes = pq.read_table(
    EXPANDED_MINUTES
).to_pandas()

bars = pq.read_table(
    EXPANDED_BARS
).to_pandas()

expanded = {
    "minutes": minutes,
    "bars": bars,
}

print(f"1m rows: {len(minutes):,}")
print(f"5m bars: {len(bars):,}")


# ============================================================
# PROCESS-LOCAL DATE RANGE EXTENSION
#
# No engine file is modified.
# Strategy source and parameters remain frozen.
# ============================================================

original_validate = RunConfig.validate
original_full_sessions = ref.full_sessions


def expanded_validate(self):
    a = date.fromisoformat(self.start)
    b = date.fromisoformat(self.end)

    if not date(2020, 1, 1) <= a < b <= date(2026, 10, 6):
        raise ValueError(
            "Expanded research range must lie within "
            "2020-01-01 to 2026-10-06 (end exclusive)"
        )

    if not isinstance(self.quantity, int) or not 1 <= self.quantity <= 100:
        raise ValueError("Quantity must be 1–100")

    if self.instrument != "MNQ" or self.timeframe != "5m":
        raise ValueError("Engine supports MNQ / 5m only")

    ref.Config(
        D(self.commission),
        self.slippage,
    )


def expanded_full_sessions(
    start="2020-01-01",
    end="2026-10-06",
):
    schedule = xc.get_calendar(
        "XNYS",
        start=start,
        end=end,
    ).schedule

    rows = []

    for d, row in schedule.iterrows():
        op = row["open"].tz_convert(
            "America/New_York"
        )
        cl = row["close"].tz_convert(
            "America/New_York"
        )

        full = (
            op.strftime("%H:%M") == "09:30"
            and cl.strftime("%H:%M") == "16:00"
            and (cl - op) == pd.Timedelta(minutes=390)
        )

        rows.append(
            {
                "date": d.date().isoformat(),
                "open_utc": row["open"].isoformat(),
                "close_utc": row["close"].isoformat(),
                "full_session": full,
            }
        )

    return (
        {
            r["date"]
            for r in rows
            if r["full_session"]
        },
        rows,
    )


RunConfig.validate = expanded_validate
ref.full_sessions = expanded_full_sessions


try:

    # ========================================================
    # OOS — MUST RUN FIRST
    # ========================================================

    print()
    print("=" * 78)
    print("RUNNING UNTOUCHED 2020-2023 HOLDOUT")
    print("A+ v1 SOURCE/PARAMETERS REMAIN FROZEN")
    print("=" * 78)

    holdout_result = run(
        source,
        params,
        RunConfig(
            start="2020-01-01",
            end="2024-01-01",
            quantity=settings.get("quantity", 1),
            commission=settings.get("commission", "0"),
            slippage=settings.get("slippage", 0),
            instrument="MNQ",
            timeframe="5m",
        ),
        data=expanded,
    )

    holdout_report = report(
        "O5 Break & Hold A+ v1 — 2020-2023 HOLDOUT",
        holdout_result,
    )


    # ========================================================
    # FULL 2020-2026
    # ========================================================

    print()
    print("Running full 2020-2026 robustness sample...")

    full_result = run(
        source,
        params,
        RunConfig(
            start="2020-01-01",
            end="2026-10-06",
            quantity=settings.get("quantity", 1),
            commission=settings.get("commission", "0"),
            slippage=settings.get("slippage", 0),
            instrument="MNQ",
            timeframe="5m",
        ),
        data=expanded,
    )

    full_report = report(
        "O5 Break & Hold A+ v1 — 2020-2026 FULL SAMPLE",
        full_result,
    )

finally:
    RunConfig.validate = original_validate
    ref.full_sessions = original_full_sessions


# ============================================================
# ORIGINAL DEVELOPMENT REPORT
# ============================================================

development_report = report(
    "O5 Break & Hold A+ v1 — 2024-2026 DEVELOPMENT",
    frozen_result,
)


# ============================================================
# SAVE IMMUTABLE-STYLE RESEARCH OUTPUT
# ============================================================

final = {
    "strategy": "O5 Break & Hold A+ v1",
    "frozen_artifact_run_id": frozen_root.name,
    "frozen_source_hash": frozen_config.get("source_hash"),
    "frozen_parameters": params,
    "development_reproduction_exact": True,
    "segments": {
        "holdout_2020_2023": holdout_report,
        "development_2024_2026": development_report,
        "full_2020_2026": full_report,
    },
    "degraded_weekdays_flagged_not_excluded": sorted(
        DEGRADED_WEEKDAYS
    ),
}

report_path = REPORT_DIR / "A_PLUS_V1_2020_2026_REPORT.json"

def json_safe(value):
    """Convert non-finite floats to JSON-safe strings without changing calculations."""
    if isinstance(value, float):
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        if math.isnan(value):
            return None

    if isinstance(value, dict):
        return {
            key: json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            json_safe(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            json_safe(item)
            for item in value
        ]

    return value


report_path.write_text(
    json.dumps(
        json_safe(final),
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    + "\n"
)


# ============================================================
# DISPLAY — HOLDOUT FIRST
# ============================================================

show(
    "2020-2023 UNTOUCHED HOLDOUT",
    holdout_report,
)

show(
    "2024-2026 FROZEN DEVELOPMENT REFERENCE",
    development_report,
)

show(
    "2020-2026 FULL ROBUSTNESS SAMPLE",
    full_report,
)

print()
print("=" * 78)
print("RESEARCH RUN COMPLETE")
print("=" * 78)
print(f"Report saved to:")
print(report_path)
print()
print("Existing engine files modified: NO")
print("Frozen strategy source modified: NO")
print("Frozen strategy parameters modified: NO")
print("2024-2026 exact reproduction: PASSED")
