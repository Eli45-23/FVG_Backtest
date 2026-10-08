"""Research orchestration; detection pass is completed before forward labels exist."""

from dataclasses import asdict
from pathlib import Path
import json
import hashlib
import pandas as pd
import pyarrow.parquet as pq
from engine.canonical import clean, dumps, digest
from engine.research.profiles import profile, validate_segment
from engine.research.levels import (
    LevelEngine,
    SessionConfig,
    NY,
    FIVE,
    valid_bar,
    schedule,
)
from engine.research.events import EventDetector
from engine.research.analysis import volatility_bucket
from engine.research.outcomes import label, PreparedMinutes, directional


def version():
    return digest(
        {
            str(p.relative_to(Path(__file__).parents[1])): hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
            for p in sorted(
                [
                    *Path(__file__).parent.glob("*.py"),
                    Path(__file__).parents[1] / "features.py",
                    Path(__file__).parents[1] / "timeframes.py",
                ]
            )
        }
    )


def snapshot(config):
    validate_segment(
        config["dataset"], config["segment"], config["start"], config["end"]
    )
    session = SessionConfig(**config.get("session", {}))
    import exchange_calendars

    calendar = {day: [str(op), str(cl)] for day, (op, cl) in schedule().items()}
    additions = {}
    if config.get("research_version", 1) == 2:
        from engine.research.study2 import settings

        additions = {
            "research_settings": settings(config.get("research_settings", {})),
            "artifact_format": "parquet-v2",
        }
    return {
        **config,
        **additions,
        "calendar": {
            "name": "XNYS",
            "package_version": exchange_calendars.__version__,
            "sessions": calendar,
            "sha256": digest(calendar),
        },
        "session": asdict(session),
        "dataset_identity": profile(config["dataset"]).identity(),
        "research_engine_version": version(),
        "baseline": "all_RTH_confirmed_5m/year/half_hour/fixed_ATR14_bucket/v1",
        "outcome_resolution": "1m_after_confirmed_close",
    }


def read_bars(config, warmup=True):
    p = profile(config["dataset"])
    start = pd.Timestamp(config["start"], tz=NY) - (
        pd.Timedelta(days=14) if warmup else pd.Timedelta(0)
    )
    end = pd.Timestamp(config["end"], tz=NY)
    bars = pq.read_table(
        p.bars,
        filters=[
            ("timestamp_utc", ">=", start.tz_convert("UTC").to_pydatetime()),
            ("timestamp_utc", "<", end.tz_convert("UTC").to_pydatetime()),
        ],
    ).to_pandas()
    if bars.timestamp_utc.duplicated().any():
        raise ValueError("Duplicate research bars")
    return bars.sort_values("timestamp_utc")


def detect(config):
    engine = LevelEngine(
        SessionConfig(**config["session"]),
        sessions={
            day: tuple(pd.Timestamp(t) for t in times)
            for day, times in config["calendar"]["sessions"].items()
        },
    )
    detector = EventDetector(engine.config)
    events, baseline = [], []
    for row in read_bars(config).itertuples(index=False):
        engine.update(row)
        day = str(row.timestamp_utc.tz_convert(NY).date())
        session = engine.sessions.get(day)
        context = {
            "atr14": engine.atr,
            "volatility_bucket": volatility_bucket(engine.atr),
            "opening_range_size": engine.opening_range,
            "premarket_range_size": engine.premarket_range,
        }
        found = detector.update(row, engine.active(row.timestamp_utc), session, context)
        if not config["start"] <= day < config["end"]:
            continue
        events.extend(found)
        if valid_bar(row) and session and session[0] <= row.timestamp_utc < session[1]:
            at = row.timestamp_utc + FIVE
            ny = at.tz_convert(NY)
            baseline.append(
                clean(
                    {
                        "event_id": digest(["baseline", str(at)]),
                        "timestamp_utc": at,
                        "price_at_event": row.close,
                        "session_close": session[1],
                        "date": day,
                        "year": ny.year,
                        "time_bucket": ny.strftime("%H:")
                        + ("00" if ny.minute < 30 else "30"),
                        "direction": "UNKNOWN",
                        "volatility_bucket": volatility_bucket(engine.atr),
                    }
                )
            )
    return events, baseline


def write_json(path, value):
    with path.open("x") as f:
        f.write(dumps(value))


def run_detection(config, root):
    if (
        config["dataset_identity"] != profile(config["dataset"]).identity()
        or config["research_engine_version"] != version()
    ):
        raise ValueError("Research identity changed; create a new study")
    if config.get("research_version", 1) == 2:
        from engine.research.study2 import detect as detect_v2

        return detect_v2(config, root)
    events, baseline = detect(config)
    write_json(root / "events.json", events)
    write_json(root / "observations.json", baseline)
    if config["segment"] != "out-of-sample":
        run_labels(config, root)


def run_labels(config, root):
    if (
        config["dataset_identity"] != profile(config["dataset"]).identity()
        or config["research_engine_version"] != version()
    ):
        raise ValueError("Research identity changed; create a new study")
    if config.get("research_version", 1) == 2:
        from engine.research.study2 import labels

        return labels(config, root)
    events = json.loads((root / "events.json").read_text())
    baseline = json.loads((root / "observations.json").read_text())
    p = profile(config["dataset"])
    start = pd.Timestamp(config["start"], tz=NY).tz_convert("UTC")
    end = pd.Timestamp(config["end"], tz=NY).tz_convert("UTC")
    raw = pq.read_table(
        p.minutes,
        filters=[
            ("ts_event", ">=", start.to_pydatetime()),
            ("ts_event", "<", end.to_pydatetime()),
        ],
    ).to_pandas()
    if "ts_event" in raw:
        raw = raw.set_index("ts_event")
    if raw.index.duplicated().any():
        raise ValueError("Duplicate research execution minutes")
    raw = raw.sort_index()
    # Integer scaling is identical to source encoding; outcomes use float for descriptive stats.
    for k in ["open", "high", "low", "close"]:
        raw[k] = raw[k].astype(float) / 1e9
    days = {
        str(day): PreparedMinutes(group)
        for day, group in raw.groupby(raw.index.tz_convert(NY).date)
    }
    empty = PreparedMinutes(raw.iloc[:0])
    cache = {}

    def outcomes(obs):
        key = (obs["timestamp_utc"], str(obs["price_at_event"]))
        if key not in cache:
            cache[key] = label(
                {**obs, "direction": "UNKNOWN"}, days.get(obs["date"], empty)
            )
        # Directional views are derived at query time; shared cache has no strategy direction.
        return cache[key]

    event_labels = {
        e["event_id"]: {
            horizon: {
                **outcome,
                "mfe": directional(outcome, e["direction"])[0],
                "mae": directional(outcome, e["direction"])[1],
            }
            for horizon, outcome in outcomes(e).items()
        }
        for e in events
    }
    baseline_labels = {e["event_id"]: outcomes(e) for e in baseline}
    write_json(root / "outcomes.json", event_labels)
    write_json(root / "baseline_outcomes.json", baseline_labels)
