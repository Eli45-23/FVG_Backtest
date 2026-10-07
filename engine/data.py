"""Read-only Parquet source and causal feature providers."""

from functools import lru_cache
from decimal import Decimal as D
import pandas as pd
import pyarrow.parquet as pq
from engine.legacy import reference as ref
from engine.strategy import Bar, Context, FVG


@lru_cache(maxsize=1)
def dataset():
    return {k: pq.read_table(p).to_pandas() for k, p in ref.INPUTS.items()}


def identities():
    return {k: ref.sha(p) for k, p in ref.INPUTS.items()}


def candle(row):
    return Bar(
        row.timestamp_utc,
        row.open,
        row.high,
        row.low,
        row.close,
        int(getattr(row, "volume", 0)),
    )


def contexts(data, feature):
    bars = data["bars"].sort_values("timestamp_utc")
    rows = list(bars.itertuples(index=False))
    lookup = {r.timestamp_utc: i for i, r in enumerate(rows)}
    if feature == "fvg_second":
        events = []
        for f in (
            data["fvgs"]
            .sort_values(["formation_bar_start_utc", "fvg_id"])
            .itertuples(index=False)
        ):
            keys = [f.formation_bar_start_utc + j * ref.FIVE for j in [-2, -1, 0, 1, 2]]
            if any(k not in lookup for k in keys):
                continue
            cs = [rows[lookup[k]] for k in keys]
            if not all(
                c.is_complete_5m and c.timestamp_ny.date() == f.formation_date_ny
                for c in cs
            ):
                continue
            at = keys[-1] + ref.FIVE
            if at.tz_convert("America/New_York").date() != f.formation_date_ny:
                continue
            a, b = map(candle, cs[3:])
            feature_obj = FVG(
                f.fvg_id,
                f.direction,
                f.top,
                f.bottom,
                f.formation_bar_start_utc,
                f.opening_exception,
            )
            ctx = Context(at, b, a, tuple(map(candle, cs)), feature_obj, a, b)
            events.append(ctx)
        yield from sorted(
            events, key=lambda c: (c.timestamp, c.fvg.formation, c.fvg.id)
        )
    else:
        history = []
        for row in rows:
            if not row.is_complete_5m:
                history = []
                continue
            b = candle(row)
            if history and b.timestamp - history[-1].timestamp != ref.FIVE:
                history = []
            previous = history[-1] if history else None
            history.append(b)
            history = history[-256:]
            yield Context(
                b.timestamp + ref.FIVE,
                b,
                previous,
                tuple(history),
                bar1=previous or b,
                bar2=b,
            )


def execution_days(raw):
    m = raw.copy()
    if "ts_event" not in m:
        m = m.reset_index()
    if m.ts_event.duplicated().any():
        raise ValueError("Duplicate execution minutes")
    for col in ["open", "high", "low", "close"]:
        m[col] = m[col].map(lambda v: D(int(v)).scaleb(-9))
    return {
        day: g.set_index("ts_event", drop=False)
        for day, g in m.groupby(m.ts_event.dt.tz_convert("America/New_York").dt.date)
    }
