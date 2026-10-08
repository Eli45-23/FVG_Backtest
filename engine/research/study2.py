"""Version 2 causal feature research, streaming result writes and separate forward labels."""

from dataclasses import asdict
import json, hashlib, time, resource
from pathlib import Path
from decimal import Decimal as D
import pandas as pd
import pyarrow.parquet as pq
from engine.canonical import clean, digest, dumps
from engine.research.profiles import profile
from engine.research.study import read_bars, write_json
from engine.research.levels import SessionConfig, FIVE, NY, valid_bar
from engine.research.events import EventDetector
from engine.research.sequences import Sequences, SequenceConfig
from engine.research.statistics import StatisticsConfig
from engine.research.numeric import validate, accepts, NUMERIC
from engine.research.columnar import Writer, OUTCOME_SCHEMA
from engine.research.outcomes import label, PreparedMinutes, directional
from engine.research.analysis import volatility_bucket
from engine.features import FeatureHub
from engine.timeframes import aggregate, FrameConfig
from engine.research.indicators import IndicatorConfig
from engine.research.structure import StructureConfig
from engine.research.zones import ZoneConfig


def settings(value):
    allowed = {
        "frame",
        "indicators",
        "structure",
        "zones",
        "sequences",
        "numeric_filters",
        "statistics",
        "atr_thresholds",
    }
    if set(value) - allowed:
        raise ValueError("Unknown research settings")
    thresholds = value.get("atr_thresholds", [0.25, 0.5, 0.75, 1, 1.5, 2, 3])
    import math

    if (
        not thresholds
        or len(thresholds) > 20
        or any(not math.isfinite(v) or v <= 0 for v in thresholds)
        or thresholds != sorted(set(thresholds))
    ):
        raise ValueError("ATR thresholds require positive increasing finite values")
    frame = FrameConfig(**value.get("frame", {}))
    frame.validate()
    return dict(
        frame=asdict(frame),
        indicators=asdict(IndicatorConfig(**value.get("indicators", {}))),
        structure=asdict(StructureConfig(**value.get("structure", {}))),
        zones=asdict(ZoneConfig(**value.get("zones", {}))),
        sequences=asdict(SequenceConfig(**value.get("sequences", {}))),
        numeric_filters=validate(value.get("numeric_filters", {})),
        statistics=asdict(StatisticsConfig(**value.get("statistics", {}))),
        atr_thresholds=thresholds,
    )


def source(config, warmup=False):
    p = profile(config["dataset"])
    start = pd.Timestamp(config["start"], tz=NY) - pd.Timedelta(
        days=30 if warmup else 0
    )
    end = pd.Timestamp(config["end"], tz=NY)
    raw = pq.read_table(
        p.minutes,
        filters=[
            ("ts_event", ">=", start.tz_convert("UTC")),
            ("ts_event", "<", end.tz_convert("UTC")),
        ],
    ).to_pandas()
    return raw


def detect(config, root):
    started = time.monotonic()
    cfg = config["research_settings"]
    raw = source(config, True)
    bars = read_bars(config)
    frames = {
        "5m": bars,
        **{tf: aggregate(raw, tf, FrameConfig(**cfg["frame"])) for tf in ["15m", "4h"]},
    }
    hub = FeatureHub(
        frames,
        SessionConfig(**config["session"]),
        cfg,
        sessions={
            day: tuple(pd.Timestamp(t) for t in times)
            for day, times in config["calendar"]["sessions"].items()
        },
    )
    detector = EventDetector(hub.levels.config)
    sequences = Sequences(SequenceConfig(**cfg["sequences"]))
    writer = Writer(root / "v2_events.parquet")
    baseline = Writer(root / "v2_observations.parquet")
    count = 0
    try:
        for row in bars.itertuples(index=False):
            at = row.timestamp_utc
            day = str(at.tz_convert(NY).date())
            hub.advance(at)
            known = hub.active_levels(at)
            hub.advance(at + FIVE)
            session = hub.levels.sessions.get(day)
            feature = dict(hub.values.get("5m", {}))
            feature.pop("structure_events", None)
            feature.pop("new_zones", None)
            if not valid_bar(row):
                detector.update(row, known, session, feature)
                sequences.update(row, [])
                continue
            atr = feature.get("atr14")
            feature.update(volatility_bucket=volatility_bucket(atr))
            found = detector.update(row, known, session, feature)
            found += sequences.update(row, found, feature)
            if (
                not config["start"] <= day < config["end"]
                or not session
                or not session[0] <= at < session[1]
            ):
                continue
            now = at + FIVE
            ny = now.tz_convert(NY)
            common = dict(
                date=day,
                timestamp_utc=now,
                session_close=session[1],
                price_at_event=row.close,
                timestamp_ny=ny,
                year=ny.year,
                month=ny.month,
                weekday=ny.day_name(),
                time_bucket=ny.strftime("%H:") + ("00" if ny.minute < 30 else "30"),
                **feature,
            )
            # Structure events use their actual confirmation time, never pivot formation time.
            for tf in ("5m", "4h"):
                for ev in hub.values.get(tf, {}).get("structure_events", []):
                    if ev["timestamp"] != now:
                        continue
                    found.append(
                        dict(
                            **{
                                k: v
                                for k, v in clean(common).items()
                                if k
                                not in ("swing_displacement", "swing_displacement_atr")
                            },
                            event_id=digest(["structure", tf, str(now), ev]),
                            level_type=tf + "_STRUCTURE",
                            interaction_type=ev["event_type"],
                            direction=(
                                "UP"
                                if ev.get("direction") == "BULLISH"
                                or ev.get("swing_type") == "LOW"
                                else "DOWN"
                            ),
                            level_price=ev["price"],
                            level_id=ev.get("id", ev.get("swing_id")),
                            level_available_at=now,
                            bar_start_utc=at,
                            open=row.open,
                            high=row.high,
                            low=row.low,
                            close=row.close,
                            touch_number=0,
                            structure_event=ev,
                            swing_displacement=ev.get("displacement"),
                            swing_displacement_atr=ev.get("displacement_atr"),
                        )
                    )
            for e in found:
                e.update(clean(common))
                if e.get("structure_event"):
                    e["swing_displacement"] = e["structure_event"].get("displacement")
                    e["swing_displacement_atr"] = e["structure_event"].get(
                        "displacement_atr"
                    )
                e["chart_context"] = clean(
                    {
                        "levels": [
                            dict(
                                id=l.id,
                                type=l.level_type,
                                price=l.price,
                                available_at=l.availability_timestamp,
                            )
                            for l in known
                        ],
                        "zones": [
                            z for z in hub.zones["4h"].zones if z["status"] == "active"
                        ],
                        "indicators": {
                            k: feature.get(k) for k in ("ema9", "ema20", "vwap")
                        },
                    }
                )
                if e["interaction_type"] == "BREAK_ACCEPTANCE":
                    e["break_distance_points"] = abs(
                        float(row.close) - float(e["level_price"])
                    )
                    e["break_distance_atr"] = (
                        e["break_distance_points"] / atr if atr else None
                    )
                e["event_candle_range"] = float(row.high - row.low)
                e["body_ratio"] = (
                    abs(float(row.close - row.open)) / e["event_candle_range"]
                    if e["event_candle_range"]
                    else None
                )
                e["penetration_points"] = float(e.get("distance_through_level", 0))
                e["distance_open_to_level"] = (
                    float(e["level_price"]) - feature["rth_open"]
                    if feature.get("rth_open") is not None
                    else None
                )
                e["distance_to_next_level"] = (
                    min(
                        [
                            float(l.price - row.close)
                            for l in known
                            if l.price > row.close
                        ],
                        default=None,
                    )
                    if e["direction"] == "UP"
                    else min(
                        [
                            float(row.close - l.price)
                            for l in known
                            if l.price < row.close
                        ],
                        default=None,
                    )
                )
                e["zone_distance"] = (
                    abs(float(row.close) - float(e["level_price"]))
                    if e["level_type"] in ("SUPPLY", "DEMAND")
                    else None
                )
                for key, target in [
                    ("penetration_points", "penetration_atr"),
                    ("room_points", "room_atr"),
                    ("distance_open_to_level", "distance_open_to_level_atr"),
                    ("zone_distance", "zone_distance_atr"),
                ]:
                    e[target] = (
                        float(e[key]) / atr if e.get(key) is not None and atr else None
                    )
                if accepts(e, cfg["numeric_filters"]):
                    writer.add(clean(e))
                    count += 1
            baseline.add(
                clean(
                    {
                        **common,
                        "event_id": digest(["baseline", str(now)]),
                        "direction": "UNKNOWN",
                    }
                )
            )
    finally:
        writer.close()
        baseline.close()
    write_json(
        root / "detection_benchmark.json",
        dict(
            events=count,
            source_5m_rows=len(bars),
            runtime_seconds=time.monotonic() - started,
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        ),
    )
    if config["segment"] != "out-of-sample":
        labels(config, root)


def labels(config, root):
    raw = source(config)
    if "ts_event" in raw:
        raw = raw.set_index("ts_event")
    if raw.index.duplicated().any():
        raise ValueError("Duplicate execution minutes")
    raw = raw.sort_index()
    for key in ["open", "high", "low", "close"]:
        raw[key] = raw[key].astype(float) / 1e9
    days = {
        str(day): PreparedMinutes(frame)
        for day, frame in raw.groupby(raw.index.tz_convert(NY).date)
    }
    empty = PreparedMinutes(raw.iloc[:0])
    writer = Writer(root / "v2_outcomes.parquet", OUTCOME_SCHEMA)
    try:
        for kind, path in [
            ("event", "v2_events.parquet"),
            ("baseline", "v2_observations.parquet"),
        ]:
            for batch in pq.ParquetFile(root / path).iter_batches(batch_size=512):
                for obs in batch.to_pylist():
                    frame = days.get(obs["date"])
                    outcomes = label(obs, frame if frame is not None else empty)
                    for horizon, out in outcomes.items():
                        atr = obs["atr14"]
                        mfe, mae = directional(out, obs.get("direction"))
                        out.update(mfe=mfe, mae=mae)
                        if out["complete"]:
                            for key, value in [
                                ("forward_close_change", out["forward_close_change"]),
                                ("mfe", mfe),
                                ("mae", mae),
                            ]:
                                out[key + "_atr"] = (
                                    value / atr if atr and value is not None else None
                                )
                            out["atr_thresholds"] = {}
                            if atr:
                                at = pd.Timestamp(obs["timestamp_utc"])
                                stop = (
                                    pd.Timestamp(obs["session_close"])
                                    if horizon == "session_close"
                                    else at + pd.Timedelta(minutes=int(horizon))
                                )
                                import numpy as np

                                a, b = np.searchsorted(
                                    frame.times, [at.value, stop.value]
                                )
                                values = frame.values[a:b]
                                reference = obs["price_at_event"]
                                for sign, exc in [
                                    ("up", values[:, 1] - reference),
                                    ("down", reference - values[:, 2]),
                                ]:
                                    for x in config["research_settings"][
                                        "atr_thresholds"
                                    ]:
                                        hits = np.flatnonzero(exc >= x * atr)
                                        out["atr_thresholds"][f"{sign}_{x}"] = {
                                            "reached": bool(len(hits)),
                                            "minutes": (
                                                int(hits[0]) + 1 if len(hits) else None
                                            ),
                                        }
                        row = {k: out.get(k) for k in OUTCOME_SCHEMA.names}
                        row.update(
                            event_id=obs["event_id"],
                            kind=kind,
                            horizon=horizon,
                            payload=dumps(out),
                        )
                        for sign in ["up", "down"]:
                            for n in [10, 25, 50, 75, 100]:
                                row[f"{sign}_{n}"] = (
                                    out.get("thresholds", {})
                                    .get(f"{sign}_{n}", {})
                                    .get("reached")
                                )
                        writer.add(row)
    finally:
        writer.close()
