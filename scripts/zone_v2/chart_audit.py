"""Deterministic engineering charts; no forward performance labels."""

from pathlib import Path
import sys, json

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image, ImageDraw
from engine.canonical import digest

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work/supply-demand-provider-v2"


def main():
    chart = OUT / "charts"
    chart.mkdir(exist_ok=True)
    bars = pd.read_parquet(OUT / "four_hour_bars.parquet")
    all_z = []
    for side in ["supply", "demand"]:
        all_z.extend(
            json.loads(x)
            for x in pd.read_parquet(OUT / f"detected_{side}_zones.parquet").payload
        )
    states = (
        pd.read_csv(OUT / "zone_lifecycle_audit.csv")
        .set_index("zone_id")
        .to_dict("index")
    )
    events = pd.read_parquet(
        OUT / "zone_events.parquet",
        columns=["zone_id", "event_type", "timestamp", "price"],
    )
    records = []
    for year in range(2020, 2024):
        for side in ["SUPPLY", "DEMAND"]:
            pool = [
                z
                for z in all_z
                if pd.Timestamp(z["availability_timestamp"])
                .tz_convert("America/New_York")
                .year
                == year
                and z["zone_type"] == side
            ]
            pool.sort(key=lambda z: digest([z["zone_id"], "visual-audit-v2"]))
            # Deterministic coverage of formation and observed lifecycle categories.
            selected = []
            seen = set()
            for z in pool:
                s = states[z["zone_id"]]
                keys = {
                    ("base", z["base_count"]),
                    ("pattern", z["pattern_type"]),
                    ("fvg", z["fvg"]),
                    ("active", s["active"]),
                    ("fresh", s["fresh"]),
                    ("mitigated", s["mitigated"]),
                }
                if keys - seen and len(selected) < 25:
                    selected.append(z)
                    seen |= keys
            selected += [z for z in pool if z not in selected][
                : max(0, 25 - len(selected))
            ]
            for z in selected:
                start = pd.Timestamp(z["formation_timestamp"])
                at = pd.Timestamp(z["availability_timestamp"])
                first = bars.index[bars.timestamp == start][0]
                confirm = bars.index[bars.availability_timestamp == at][0]
                part = bars.iloc[max(0, first - 3) : min(len(bars), confirm + 15)]
                origin = first - part.index[0]
                av = confirm - part.index[0] + 0.5
                fig, ax = plt.subplots(figsize=(12, 4))
                fig.patch.set_facecolor("#101821")
                ax.set_facecolor("#101821")
                for i, b in enumerate(part.itertuples()):
                    if pd.isna(b.open):
                        continue
                    color = "#55c4a2" if b.close >= b.open else "#e67982"
                    if not b.complete:
                        color = "#808080"
                    ax.vlines(i, b.low, b.high, color=color, lw=1)
                    ax.add_patch(
                        Rectangle(
                            (i - 0.27, min(b.open, b.close)),
                            0.54,
                            max(abs(b.close - b.open), 0.15),
                            facecolor=color,
                        )
                    )
                hue = "#e6a553" if side == "SUPPLY" else "#609fec"
                ax.add_patch(
                    Rectangle(
                        (origin - 0.4, z["bottom"]),
                        av - origin + 0.4,
                        z["width"],
                        facecolor=hue,
                        edgecolor=hue,
                        alpha=0.13,
                        hatch="///",
                    )
                )
                active_end = len(part) - 0.5
                invalidated_at = states[z["zone_id"]].get("invalidated_at")
                if pd.notna(invalidated_at):
                    invalidated_at = pd.Timestamp(invalidated_at)
                    ends = part.index[part.availability_timestamp == invalidated_at]
                    if len(ends):
                        active_end = ends[0] - part.index[0] + 0.5
                ax.add_patch(
                    Rectangle(
                        (av, z["bottom"]),
                        active_end - av,
                        z["width"],
                        facecolor=hue,
                        edgecolor=hue,
                        alpha=0.24,
                    )
                )
                ax.axvline(
                    av,
                    color="#eeeeee",
                    linestyle="--",
                    lw=1,
                    label="Available after departure close",
                )
                ax.text(
                    origin - 0.4,
                    z["top"],
                    " BASE ORIGIN (unavailable)",
                    fontsize=7,
                    color=hue,
                )
                zone_events = events[events.zone_id == z["zone_id"]]
                for kind, marker, color in [
                    ("ZONE_FIRST_TOUCH", "o", "#eee064"),
                    ("ZONE_REJECTION", "v", "#b586eb"),
                    ("ZONE_INVALIDATION", "x", "#ff5364"),
                ]:
                    rows = zone_events[zone_events.event_type == kind]
                    if rows.empty:
                        continue
                    e = rows.iloc[0]
                    stamp = pd.Timestamp(e.timestamp)
                    indices = part.index[
                        (part.timestamp < stamp)
                        & (part.availability_timestamp >= stamp)
                    ]
                    if len(indices):
                        ax.scatter(
                            indices[-1]
                            - part.index[0]
                            - 0.5
                            + (stamp - part.loc[indices[-1], "timestamp"])
                            / (
                                part.loc[indices[-1], "availability_timestamp"]
                                - part.loc[indices[-1], "timestamp"]
                            ),
                            e.price,
                            marker=marker,
                            c=color,
                            s=25,
                            label=kind,
                        )
                labels = [
                    t.tz_convert("America/New_York").strftime("%m/%d %H:%M")
                    for t in part.timestamp
                ]
                ax.set_xticks(
                    range(0, len(part), 3),
                    labels[::3],
                    rotation=25,
                    fontsize=6,
                    color="#cdd9e3",
                )
                ax.tick_params(axis="y", colors="#cdd9e3", labelsize=7)
                ax.grid(alpha=0.1)
                ax.set_title(
                    f'{year} {side} | {z["pattern_type"]} | base {z["base_count"]} | {z["zone_id"][:10]}\nENGINEERING ONLY — calendar gate unresolved | NY time | gray = incomplete',
                    color="white",
                    fontsize=9,
                )
                ax.legend(fontsize=6, loc="best")
                fig.tight_layout()
                path = chart / f'{year}_{side}_{z["zone_id"][:12]}.png'
                fig.savefig(path, dpi=110)
                plt.close(fig)
                bs = bars[
                    bars.timestamp.isin(pd.to_datetime(z["base_timestamps"], utc=True))
                ]
                expected_top = (
                    bs.high.max()
                    if side == "SUPPLY"
                    else bs[["open", "close"]].max(axis=1).max()
                )
                expected_bottom = (
                    bs[["open", "close"]].min(axis=1).min()
                    if side == "SUPPLY"
                    else bs.low.min()
                )
                records.append(
                    dict(
                        zone_id=z["zone_id"],
                        year=year,
                        side=side,
                        pattern=z["pattern_type"],
                        base_count=z["base_count"],
                        fvg=z["fvg"],
                        geometry_correct=expected_top == z["top"]
                        and expected_bottom == z["bottom"],
                        departure_excluded=not set(z["base_timestamps"])
                        & set(z["departure_timestamps"]),
                        availability_correct=bars.loc[confirm, "availability_timestamp"]
                        == at,
                        no_preavailability_event=all(
                            pd.Timestamp(t) > at for t in zone_events.timestamp
                        ),
                        fresh=states[z["zone_id"]]["fresh"],
                        mitigated=states[z["zone_id"]]["mitigated"],
                        invalidated=states[z["zone_id"]]["invalidated"],
                        chart=str(path.relative_to(OUT)),
                        visual_review="PENDING",
                        reviewer_notes="Mechanical checks only; source calendar not approved",
                    )
                )
            group = [r for r in records if r["year"] == year and r["side"] == side]
            for offset in range(0, len(group), 5):
                pack = group[offset : offset + 5]
                sheet = Image.new("RGB", (1200, 400 * len(pack)), "#101821")
                for i, r in enumerate(pack):
                    im = Image.open(OUT / r["chart"])
                    im.thumbnail((1200, 400))
                    sheet.paste(im, (0, 400 * i))
                sheet.save(
                    chart / f"CONTACT_{year}_{side}_{offset//5+1}.jpg", quality=90
                )
            print(year, side, len(group), flush=True)
    pd.DataFrame(records).to_csv(OUT / "development_chart_audit.csv", index=False)


if __name__ == "__main__":
    main()
