"""Independent causal arithmetic audit and deterministic chart samples; Development only."""

import sys, json, time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
import pandas as pd, numpy as np, duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from analyze import R, OLD, LEVELS, folder
from engine.research.study import read_bars
from engine.research.study2 import source
from engine.research.outcomes import label, PreparedMinutes

C = json.loads(Path(f"storage/event_studies/{OLD}/config.json").read_text())
bars = read_bars(C).set_index("timestamp_utc")
bars.index = pd.to_datetime(bars.index, utc=True)
raw = source(C)
raw.index = pd.to_datetime(raw.index, utc=True)
raw = raw[["open", "high", "low", "close"]].astype(float) / 1e9
assert raw.index.max() < pd.Timestamp("2024-01-01", tz="America/New_York")
minutes = {
    str(d): PreparedMinutes(g)
    for d, g in raw.groupby(raw.index.tz_convert("America/New_York").date)
}
sessions = {
    d: tuple(pd.Timestamp(t) for t in ts) for d, ts in C["calendar"]["sessions"].items()
}
prev = dict(zip(list(sessions)[1:], list(sessions)[:-1]))
catalog = pd.read_parquet(R / "swing_catalog.parquet").set_index("id")
coverage = pd.read_csv(R / "premarket_coverage.csv").set_index("date")
checks = []
charts = []
revisits = []
cache = {}


def level_expected(p):
    kind = p["level_type"]
    day = p["date"]
    key = (kind, day)
    if kind.startswith(("5m_", "4h_")):
        s = catalog.loc[p["level_id"]]
        assert pd.Timestamp(s.availability_timestamp) == pd.Timestamp(
            p["level_available_at"]
        )
        assert pd.Timestamp(s.formation_timestamp) < pd.Timestamp(
            s.availability_timestamp
        )
        return float(s.price)
    if key not in cache:
        if kind in ["PDH", "PDL"]:
            a, b = sessions[prev[day]]
        elif kind in ["O5H", "O5L"]:
            a = sessions[day][0]
            b = a + pd.Timedelta(minutes=5)
        else:
            assert coverage.loc[day, "available"]
            a = pd.Timestamp(day, tz="America/New_York")
            b = a + pd.Timedelta(hours=9, minutes=30)
        g = bars.loc[(bars.index >= a) & (bars.index < b)]
        assert g.is_complete_5m.all()
        assert len(g) == int((b - a).total_seconds() / 300)
        cache[key] = float(g.high.max() if kind.endswith("H") else g.low.min())
    return cache[key]


def render(p, root, path):
    at = pd.Timestamp(p["timestamp_utc"])
    start = pd.Timestamp(root["bar_start_utc"])
    left = min(start, at - pd.Timedelta(minutes=35))
    right = min(at + pd.Timedelta(minutes=35), pd.Timestamp(p["session_close"]))
    g = bars.loc[(bars.index >= left) & (bars.index < right)]
    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_facecolor("#101922")
    ax.set_facecolor("#101922")
    for i, (_, b) in enumerate(g.iterrows()):
        o, h, l, c = map(float, [b.open, b.high, b.low, b.close])
        color = "#39bc98" if c >= o else "#ec7272"
        ax.vlines(i, l, h, color=color, lw=1)
        ax.add_patch(
            Rectangle((i - 0.3, min(o, c)), 0.6, max(abs(c - o), 0.1), facecolor=color)
        )
        if g.index[i] == start:
            ax.axvspan(i - 0.45, i + 0.45, alpha=0.2, color="#eec966")
        if g.index[i] == pd.Timestamp(p["bar_start_utc"]):
            ax.annotate(
                "Confirmation close",
                xy=(i, c),
                xytext=(i, max(g.high.astype(float)) + 0.6),
                color="white",
                arrowprops={"arrowstyle": "->", "color": "white"},
                ha="center",
                fontsize=8,
            )
    known_x = max(
        -0.4,
        float(
            np.searchsorted(g.index.asi8, pd.Timestamp(p["level_available_at"]).value)
        )
        - 0.4,
    )
    ax.hlines(
        float(p["level_price"]),
        known_x,
        len(g) - 0.5,
        color="#69c6ff",
        label=f"{p['level_type']} {float(p['level_price']):.2f}",
    )
    future_x = np.searchsorted(g.index.asi8, at.value) - 0.5
    ax.axvspan(
        future_x, len(g) - 0.5, alpha=0.06, color="white", label="After confirmation"
    )
    ax.set_xticks(range(len(g)))
    ax.set_xticklabels(
        g.index.tz_convert("America/New_York").strftime("%H:%M"),
        rotation=60,
        fontsize=7,
    )
    ax.tick_params(colors="white")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.12)
    ax.legend(facecolor="#293640", labelcolor="white", fontsize=8)
    ax.set_title(
        f"{p['date']} • {p['level_type']} • {p['interaction_type']} • touch episode {p['touch_number']}\nAvailable {pd.Timestamp(p['level_available_at']).tz_convert('America/New_York')} | confirmed {at.tz_convert('America/New_York')}",
        color="white",
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=115)
    plt.close(fig)


if __name__ == "__main__":
    for level in LEVELS[:10]:
        while not (folder(level) / "events.parquet").exists():
            time.sleep(5)
        ev = pd.read_parquet(folder(level) / "events.parquet")
        ps = [json.loads(x) for x in ev.payload]
        lookup = {p["event_id"]: p for p in ps}
        bad = []
        nlabel = 0
        for p in ps:
            try:
                at = pd.Timestamp(p["timestamp_utc"])
                bs = pd.Timestamp(p["bar_start_utc"])
                avail = pd.Timestamp(p["level_available_at"])
                b = bars.loc[bs]
                assert (
                    bs + pd.Timedelta(minutes=5) == at
                    and avail <= bs
                    and b.is_complete_5m
                )
                assert sessions[p["date"]][0] <= bs < at <= sessions[p["date"]][1]
                assert all(
                    float(p[k]) == float(b[k]) for k in ["open", "high", "low", "close"]
                )
                assert float(p["level_price"]) == level_expected(p)
                root = lookup[p.get("root_event_id", p["event_id"])]
                kind = p["interaction_type"]
                sign = 1 if p["direction"] == "UP" else -1
                price = float(p["level_price"])
                c = float(p["close"])
                if "NEXT_CANDLE" in kind:
                    assert pd.Timestamp(root["timestamp_utc"]) == bs
                if kind == "BREAK_ACCEPTANCE":
                    assert (c - price) * sign > 0
                if kind == "BREAK_FAILED_NEXT_CANDLE_HOLD":
                    assert (c - price) * sign < 0
                if kind in ["BREAK_NEXT_CANDLE_CLOSE_HOLD", "BREAK_RETEST_HOLD"]:
                    assert (c - price) * sign > 0
                if kind == "BREAK_RETEST_FAIL":
                    assert (c - price) * sign < 0
                if kind in ["BREAK_NEXT_CANDLE_FULL_HOLD", "BREAK_RETEST_FULL_HOLD"]:
                    assert (
                        float(p["low"]) > price
                        if sign == 1
                        else float(p["high"]) < price
                    )
                if kind in ["TOUCH", "SWEEP_RECLAIM", "REJECTION", "RETEST"]:
                    assert float(p["low"]) <= price <= float(p["high"])
                if kind in ["REJECTION", "SWEEP_RECLAIM"]:
                    assert (c - price) * sign < 0
                if kind in ["REJECTION_CONFIRMATION", "SWEEP_RECLAIM_CONFIRMATION"]:
                    assert pd.Timestamp(root["timestamp_utc"]) == bs
                    assert (
                        c - float(root["high"] if sign == 1 else root["low"])
                    ) * sign > 0
                for component in p.get("component_event_ids", []):
                    assert (
                        component in lookup
                        and pd.Timestamp(lookup[component]["timestamp_utc"]) <= at
                    )
            except Exception as exc:
                bad.append({"event_id": p["event_id"], "error": repr(exc)})
        # Touch count resets per level/date; compounds inherit the root/retest episode, not the confirmation candle.
        touches = ev[ev.interaction_type == "TOUCH"].sort_values(
            ["timestamp_utc", "event_id"]
        )
        for _, g in touches.groupby(["date", "level_id"]):
            if list(pd.to_numeric(g.touch_number)) != list(range(1, len(g) + 1)):
                bad.append(
                    {"event_id": g.iloc[0].event_id, "error": "Touch count sequence"}
                )
        out = folder(level)
        (out / "chart_audit").mkdir(exist_ok=True)
        chosen = (
            ev.sort_values(["timestamp_utc", "event_id"])
            .groupby("interaction_type", sort=True)
            .head(1)
        )
        later = (
            ev[pd.to_numeric(ev.touch_number) >= 3]
            .sort_values(["timestamp_utc", "event_id"])
            .head(1)
        )
        chosen = pd.concat([chosen, later]).drop_duplicates("event_id")
        for row in chosen.itertuples():
            p = lookup[row.event_id]
            root = lookup[p.get("root_event_id", p["event_id"])]
            path = (
                out
                / "chart_audit"
                / f'{p["interaction_type"]}_{p["event_id"][:10]}.png'
            )
            render(p, root, path)
            measured = label(p, minutes[p["date"]])
            id = json.loads((out / "configuration.json").read_text())["study_id"]
            con = duckdb.connect()
            saved = con.execute(
                "select * from read_parquet(?) where event_id=?",
                [f"storage/event_studies/{id}/v2_outcomes.parquet", p["event_id"]],
            ).df()
            con.close()
            for x in saved.itertuples():
                y = measured[x.horizon]
                assert x.complete == y["complete"]
                if x.complete:
                    for k in [
                        "forward_close_change",
                        "maximum_high_excursion",
                        "maximum_low_excursion",
                    ]:
                        assert getattr(x, k) == y[k]
            nlabel += len(saved)
            charts.append(
                dict(
                    level=level,
                    event_id=p["event_id"],
                    interaction=p["interaction_type"],
                    touch=p["touch_number"],
                    date=p["date"],
                    chart=str(path.relative_to(R)),
                    source_id=id,
                    mechanical_audit="PASS" if not bad else "FAIL",
                )
            )
        # Full-population revisit times after confirmation; complete-window eligibility remains in outcome tables.
        for p in ps:
            m = minutes[p["date"]]
            at = pd.Timestamp(p["timestamp_utc"]).value
            end = pd.Timestamp(p["session_close"]).value
            left = np.searchsorted(m.times, at)
            right = np.searchsorted(m.times, end)
            levelprice = float(p["level_price"])
            v = m.values[left:right]
            hits = np.flatnonzero((v[:, 2] <= levelprice) & (v[:, 1] >= levelprice))
            first = (m.times[left + hits[0]] - at) / 60e9 + 1 if len(hits) else np.nan
            revisits.append(
                dict(
                    level=level,
                    event_id=p["event_id"],
                    first_post_confirmation_level_revisit_minutes=first,
                )
            )
        checks.append(
            dict(
                level=level,
                events_checked=len(ev),
                failures=len(bad),
                charts=len(chosen),
                independent_outcome_labels_checked=nlabel,
            )
        )
        (out / "causal_audit_failures.json").write_text(json.dumps(bad, indent=2))
        print(checks[-1], flush=True)
    pd.DataFrame(checks).to_csv(R / "causal_audit.csv", index=False)
    pd.DataFrame(charts).to_csv(R / "chart_audit_index.csv", index=False)
    pd.DataFrame(revisits).to_parquet(R / "level_revisits.parquet", index=False)
