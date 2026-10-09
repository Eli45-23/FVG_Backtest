"""Mechanical schedule/coverage charts, never forward outcome research."""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image
from scripts.calendar_foundation.audit import OUT
from engine.session_calendar.mnq_v1 import nth, NY


def main():
    b = pd.read_parquet(OUT / "four_hour_bar_inventory.parquet")
    out = OUT / "charts"
    out.mkdir(exist_ok=True)
    dates = [
        "2020-01-06",
        "2020-03-16",
        "2021-04-02",
        "2023-04-07",
        "2023-07-03",
        "2023-11-24",
        "2021-06-25",
        "2021-06-28",
        "2023-06-19",
    ]
    for y in range(2020, 2024):
        for month, n in [(3, 2), (11, 1)]:
            dates.append(str(nth(y, month, 6, n) + pd.Timedelta(days=1)))
    records = []
    for date in dates:
        date = date[:10]
        ix = b.index[b.session_date == date]
        rows = b.iloc[max(0, ix[0] - 6) : min(len(b), ix[-1] + 7)]
        fig, (ax, cov) = plt.subplots(
            2, 1, figsize=(14, 6), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
        )
        for j, (_, r) in enumerate(rows.iterrows()):
            color = "#2f9c85" if r.complete else "#888888"
            if not r.full:
                color = "#c78b25"
            if not r.schedule_resolved:
                color = "#a661a2"
            if np.isfinite(r.open):
                ax.plot([j, j], [r.low, r.high], color=color)
                ax.add_patch(
                    Rectangle(
                        (j - 0.3, min(r.open, r.close)),
                        0.6,
                        max(0.25, abs(r.close - r.open)),
                        color=color,
                        alpha=0.75,
                    )
                )
            if r.session_date == date:
                ax.axvspan(j - 0.5, j + 0.5, color="lightblue", alpha=0.08)
            cov.bar(j, r.minute_count, color=color)
            if r.schedule_resolved:
                cov.plot([j - 0.4, j + 0.4], [r.expected_minutes] * 2, color="black")
            else:
                cov.text(j, 245, "?", ha="center", color=color)
        ax.set_title(
            f"{date} · NY session anchor / raw OHLC audit\nGreen=complete, gray=incomplete, amber=shortened, purple=UNRESOLVED EXCLUDED"
        )
        cov.set_ylabel("Source minutes\nblack=official expected")
        cov.set_xticks(range(len(rows)))
        cov.set_xticklabels(
            [
                r.timestamp.tz_convert(NY).strftime("%m/%d %H:%M")
                for r in rows.itertuples()
            ],
            rotation=60,
            ha="right",
            fontsize=7,
        )
        ax.grid(alpha=0.2)
        fig.tight_layout()
        path = out / f"{date}.png"
        fig.savefig(path, dpi=110)
        plt.close(fig)
        records.append(
            dict(
                date=date,
                chart=str(path.relative_to(OUT)),
                bars=len(rows),
                resolved_bars=int(rows.schedule_resolved.sum()),
                excluded_bars=int((~rows.complete).sum()),
                mechanical_pass=True,
                visual_review="PENDING",
                notes="Unknown nominal buckets shown only for diagnosis; not accepted candles",
            )
        )
    pd.DataFrame(records).to_csv(OUT / "chart_audit.csv", index=False)
    for k in range(0, len(records), 4):
        canvas = Image.new("RGB", (1400, 2400), "white")
        for j, r in enumerate(records[k : k + 4]):
            im = Image.open(OUT / r["chart"])
            im.thumbnail((1400, 600))
            canvas.paste(im, (0, j * 600))
        canvas.save(out / f"CONTACT_{k//4+1}.jpg", quality=90)
    print(len(records), "charts")


if __name__ == "__main__":
    main()
