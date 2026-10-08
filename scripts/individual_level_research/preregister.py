from pathlib import Path
import json, hashlib, datetime, sqlite3

R = (
    Path(__file__).resolve().parents[2]
    / "work"
    / "mnq-individual-level-master-research"
)
R.mkdir(parents=True, exist_ok=True)
levels = [
    "PDH",
    "PDL",
    "PMH",
    "PML",
    "O5H",
    "O5L",
    "5m_SWING_HIGH",
    "5m_SWING_LOW",
    "4h_SWING_HIGH",
    "4h_SWING_LOW",
    "SUPPLY",
    "DEMAND",
]
kinds = [
    "TOUCH",
    "REJECTION",
    "SWEEP_RECLAIM",
    "BREAK_ACCEPTANCE",
    "BREAK_NEXT_CANDLE_CLOSE_HOLD",
    "BREAK_NEXT_CANDLE_FULL_HOLD",
    "BREAK_FAILED_HOLD",
    "RETEST",
    "BREAK_RETEST",
    "BREAK_RETEST_HOLD",
    "BREAK_RETEST_FULL_HOLD",
    "BREAK_RETEST_FAIL",
    "REJECTION_CONFIRMATION",
    "SWEEP_RECLAIM_CONFIRMATION",
]
protocol = dict(
    registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    segment="development",
    start="2020-01-01",
    end_exclusive="2024-01-01",
    levels=levels,
    interactions=kinds,
    primary=dict(
        horizon="30",
        atr_target=1,
        measured_directions=["UP", "DOWN"],
        approach_strata=["UP", "DOWN"],
        family="all levels x interactions x stored approach direction x measured direction; unavailable cells p=1; one global BH",
        estimand="equal NY-date weighted probability difference against year x confirmation half-hour x fixed causal ATR14 bucket ordinary RTH observations",
        iterations=2000,
        seed=1729,
        minimum_dates=10,
    ),
    secondary=dict(
        horizons=["5", "10", "15", "30", "60", "session_close"],
        atr_targets=[0.25, 0.5, 0.75, 1, 1.5, 2, 3],
        point_targets=[10, 25, 50, 75, 100],
        contexts=[
            "year",
            "time",
            "touch",
            "volatility",
            "EMA",
            "VWAP",
            "structure",
            "efficiency",
        ],
        classification="exploratory; no filter optimization",
    ),
    premarket=dict(
        start="00:00",
        end="09:30",
        timezone="America/New_York",
        coverage="all 114 actual complete five-minute candles; otherwise unavailable",
    ),
    classification=dict(
        strong="primary q<=.05, effect>=.05, >=100 dates, positive effect in all 4 years each >=10 dates, and favorable/adverse balance reviewed; still Development only",
        promising="primary q<=.10, effect>=.03, >=30 dates, positive in >=3 years; or descriptive secondary result explicitly exploratory",
        negative="primary q<=.05 and effect<=-.03",
        insufficient="fewer than30 matched dates or blocked detector",
        other="NO MEANINGFUL EVIDENCE",
    ),
    prior_knowledge="PDH/PDL outcomes and candidate previously inspected; this registration is prospective to this expanded comparison, not universally untouched discovery",
)
p = R / "preregistered_protocol.json"
if not p.exists():
    p.write_text(json.dumps(protocol, indent=2) + "\n")
(R / "protocol_sha256.txt").write_text(
    hashlib.sha256(p.read_bytes()).hexdigest() + "\n"
)
