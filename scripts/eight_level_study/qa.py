"""Source/population invariants and deterministic representative chart audits."""

import sys, json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
import pyarrow.parquet as pq
from scripts.eight_level_study.detect import P, PM, LEVELS, sha, write, NY


def main():
    identity = json.loads((P / "source_identity.json").read_text())
    for path, h in identity["source_hashes"].items():
        assert sha(ROOT / path) == h, path
    ev = pd.read_parquet(P / "entry_events.parquet")
    src = pd.read_parquet(P / "source_events.parquet")
    cov = pd.read_csv(P / "level_coverage.csv")
    j = ev.merge(
        cov,
        left_on=["date", "level_type"],
        right_on=["date", "level"],
        validate="many_to_one",
    )
    assert j.available.all() and (j.level_price.astype(float) == j.price).all()
    assert (
        pd.to_datetime(j.level_available_at, utc=True)
        == pd.to_datetime(j.availability, utc=True)
    ).all()
    assert src.event_id.is_unique
    assert (
        pd.to_datetime(ev.timestamp_utc, utc=True)
        >= pd.to_datetime(ev.level_available_at, utc=True) + pd.Timedelta(minutes=5)
    ).all()
    cfg = json.loads((ROOT / "storage/event_studies" / PM / "config.json").read_text())
    start = pd.Timestamp("2020-01-01", tz=NY).tz_convert("UTC")
    end = pd.Timestamp("2024-01-01", tz=NY).tz_convert("UTC")
    bars = (
        pq.read_table(
            ROOT / "outputs/data" / cfg["dataset_identity"]["files"]["bars"]["name"],
            filters=[("timestamp_utc", ">=", start), ("timestamp_utc", "<", end)],
        )
        .to_pandas()
        .sort_values("timestamp_utc")
        .set_index("timestamp_utc")
    )
    bars[["open", "high", "low", "close"]] = bars[
        ["open", "high", "low", "close"]
    ].astype(float)
    bars.index = bars.index.as_unit("ns")
    stamps = pd.DatetimeIndex(pd.to_datetime(src.timestamp_utc, utc=True) - pd.Timedelta(minutes=5)).as_unit("ns")
    positions = bars.index.get_indexer(stamps)
    assert (positions >= 0).all()
    print("QA level/source mapping passed", flush=True)
    for k in ["open", "high", "low", "close"]:
        assert (
            bars[k].to_numpy()[positions] == src[k].astype(float).to_numpy()
        ).all(), k
    # Independent O15 reduction from actual 1m fixed-point source.
    raw = pq.read_table(
        ROOT / "outputs/data" / cfg["dataset_identity"]["files"]["minutes"]["name"],
        columns=["ts_event", "high", "low"],
        filters=[("ts_event", ">=", start), ("ts_event", "<", end)],
    ).to_pandas()
    if "ts_event" in raw:
        raw = raw.set_index("ts_event")
    raw.index = raw.index.as_unit("ns")
    print("QA exact source OHLC passed", flush=True)
    checked = 0
    for r in cov[(cov.level == "O15H") & cov.available].itertuples():
        op = pd.Timestamp(r.date + " 09:30", tz=NY).tz_convert("UTC")
        idx = pd.date_range(op, periods=15, freq="min").as_unit("ns")
        assert (raw.index.get_indexer(idx) >= 0).all()
        v = raw.iloc[raw.index.get_indexer(idx)]
        assert float(v.high.max() / 1e9) == r.price
        low = cov[(cov.date == r.date) & (cov.level == "O15L")].price.iloc[0]
        assert float(v.low.min() / 1e9) == low
        checked += 1
    charts = P / "charts"
    charts.mkdir(exist_ok=True)
    audits = []
    for level in LEVELS:
        for entry in [
            "BREAK_NEXT_FULL_HOLD",
            "RETEST_CLOSE_HOLD",
            "REJECTION_CLOSE",
            "FAILED_BREAK_CLOSE",
        ]:
            sample = (
                ev[(ev.level_type == level) & (ev.entry_kind == entry)]
                .sort_values(["timestamp_utc", "event_id"])
                .head(1)
            )
            if sample.empty:
                continue
            e = sample.iloc[0]
            at = pd.Timestamp(e.timestamp_utc)
            op = pd.Timestamp(e.date + " 09:30", tz=NY).tz_convert("UTC")
            cl = pd.Timestamp(e.session_close)
            a = max(op, at - pd.Timedelta(minutes=40))
            b = min(cl, at + pd.Timedelta(minutes=30))
            g = bars.loc[(bars.index >= a) & (bars.index < b)]
            price = float(e.level_price)
            lo = min(g.low.min(), price)
            hi = max(g.high.max(), price)
            pad = max((hi - lo) * 0.1, 2)
            lo -= pad
            hi += pad
            xx = lambda t: 65 + (t - a).total_seconds() / (b - a).total_seconds() * 900
            yy = lambda p: 315 - (p - lo) / (hi - lo) * 240
            title = f'{level} · {entry} · {at.tz_convert(NY).strftime("%Y-%m-%d %H:%M %Z")} · {e.direction}'
            svg = [
                f'<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="420" viewBox="0 0 1040 420"><rect width="1040" height="420" fill="#101923"/><g font-family="Arial" fill="#e1eaf1"><text x="25" y="28" font-size="17">{html.escape(title)}</text><text x="25" y="52" font-size="12">Level available {pd.Timestamp(e.level_available_at).tz_convert(NY).strftime("%Y-%m-%d %H:%M %Z")} · Forward measurement starts at dashed line</text>'
            ]
            svg.append(
                f'<rect x="{xx(at)}" y="65" width="{965-xx(at)}" height="260" fill="#162b39"/>'
            )
            for t, r in g.iterrows():
                x = xx(t + pd.Timedelta(minutes=2.5))
                color = "#58c9ae" if r.close >= r.open else "#f08a8a"
                svg.append(
                    f'<line x1="{x}" x2="{x}" y1="{yy(r.high)}" y2="{yy(r.low)}" stroke="{color}"/><rect x="{x-8}" y="{yy(max(r.open,r.close))}" width="16" height="{max(1,abs(yy(r.open)-yy(r.close)))}" fill="{color}"/>'
                )
                svg.append(
                    f'<text x="{x}" y="346" font-size="10" text-anchor="middle">{t.tz_convert(NY).strftime("%H:%M")}</text>'
                )
            available = max(a, pd.Timestamp(e.level_available_at))
            svg.append(
                f'<line x1="{xx(available)}" x2="965" y1="{yy(price)}" y2="{yy(price)}" stroke="#efc875"/><text x="970" y="{yy(price)}" font-size="11">{price:.2f}</text><line x1="{xx(at)}" x2="{xx(at)}" y1="65" y2="325" stroke="#88b8ff" stroke-dasharray="5 4"/><text x="25" y="378" font-size="12">Blue area: subsequent candles, excluded from event detection. Times are New York bar starts; confirmation is bar end.</text></g></svg>'
            )
            path = charts / f"{level}_{entry}.svg"
            path.write_text("".join(svg))
            audits.append(
                dict(
                    level=level,
                    entry_kind=entry,
                    event_id=e.event_id,
                    root_id=e.root_id,
                    confirmation=str(at),
                    source_candle_exact=True,
                    level_price_exact=True,
                    availability_causal=True,
                    chart=path.relative_to(P).as_posix(),
                )
            )
    write("chart_audit.csv", pd.DataFrame(audits))
    result = dict(
        status="PASS",
        entry_records=len(ev),
        unique_entry_ids=ev.event_id.nunique(),
        source_event_records=len(src),
        exact_source_ohlc_checks=len(src) * 4,
        opening15_dates_checked_against_1m=checked,
        charts=len(audits),
        source_hashes_unchanged=True,
        validation_oos_outcomes_read=False,
    )
    (P / "quality_verification.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n"
    )
    print(result, flush=True)


if __name__ == "__main__":
    main()
