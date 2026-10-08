"""Additive execution input profiles; legacy identities remain byte-for-byte unchanged."""

import pyarrow.parquet as pq
import pandas as pd
from engine.data import dataset, identities
from engine.research.profiles import profile


def data_hashes(profile_id="legacy_2024_2026"):
    return (
        identities()
        if profile_id == "legacy_2024_2026"
        else {
            k: v["sha256"] for k, v in profile(profile_id).identity()["files"].items()
        }
    )


def source_identity(profile_id="legacy_2024_2026"):
    return profile(profile_id).identity()


def load_data(config, feature="bars"):
    if config.dataset_profile == "legacy_2024_2026":
        return dataset()
    p = profile(config.dataset_profile)
    # Keep prior observations for causal warmup; execution rows restricted to requested dates.
    start = pd.Timestamp(config.start, tz="America/New_York").tz_convert("UTC")
    end = pd.Timestamp(config.end, tz="America/New_York").tz_convert("UTC")
    bars = pq.read_table(
        p.bars,
        filters=[
            ("timestamp_utc", ">=", start - pd.Timedelta(days=30)),
            ("timestamp_utc", "<", end),
        ],
    ).to_pandas()
    raw = pq.read_table(
        p.minutes,
        filters=[
            (
                "ts_event",
                ">=",
                (
                    start - pd.Timedelta(days=30)
                    if config.execution_mode == "extended_v1"
                    or config.timeframe != "5m"
                    or config.max_trades_per_day != 1
                    or config.sizing_mode != "FIXED_QUANTITY"
                    else start
                ),
            ),
            ("ts_event", "<", end),
        ],
    ).to_pandas()
    result = {"bars": bars, "minutes": raw}
    if feature == "fvg_second":
        # Same validated detector, in memory only; no derived market file is written.
        from detect_fvgs import detect

        result["fvgs"] = detect(bars)
    return result
