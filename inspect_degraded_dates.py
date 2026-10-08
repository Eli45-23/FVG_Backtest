import os
from pathlib import Path

import databento as db
import pandas as pd
from dotenv import load_dotenv


ROOT = Path(
    "/Users/DayTrade/Documents/Codex/2026-10-06/"
    "1-connect-to-databento-2-request"
)

DATA_DIR = ROOT / "outputs/data"

ONE_MIN = DATA_DIR / (
    "GLBX.MDP3_MNQ.v.0_ohlcv-1m_2020-01-01_2026-10-06.parquet"
)

FIVE_MIN = DATA_DIR / (
    "MNQ_5m_2020-01-01_2026-10-06.parquet"
)


# ============================================================
# DATABENTO CONDITIONS
# ============================================================

load_dotenv("/Users/DayTrade/.env")

api_key = os.getenv("DATABENTO_API_KEY")

if not api_key:
    raise RuntimeError("DATABENTO_API_KEY not found.")

client = db.Historical(api_key)

conditions = client.metadata.get_dataset_condition(
    dataset="GLBX.MDP3",
    start_date="2020-01-01",
    end_date="2023-12-31",
)


def get_value(item, key):
    """
    Databento may return dict-like rows or objects depending
    on SDK version. Support both.
    """
    if isinstance(item, dict):
        return item[key]

    return getattr(item, key)


problem_days = []

for row in conditions:

    condition = str(get_value(row, "condition"))

    if condition.lower() != "available":

        problem_days.append(
            {
                "date": str(get_value(row, "date")),
                "condition": condition,
            }
        )


# ============================================================
# LOAD LOCAL 1-MINUTE DATA
# ============================================================

print("Loading 1-minute master data...")

one = pd.read_parquet(ONE_MIN)

if one.index.name != "ts_event":
    raise RuntimeError("1m dataset index is not ts_event.")

if one.index.tz is None:
    raise RuntimeError("1m ts_event index is not timezone-aware.")

one = one.copy()

one["timestamp_ny"] = (
    one.index.tz_convert("America/New_York")
)

# FIX:
# Series datetime operations require .dt
one["ny_date"] = one["timestamp_ny"].dt.strftime("%Y-%m-%d")
one["ny_time"] = one["timestamp_ny"].dt.strftime("%H:%M")


# ============================================================
# LOAD LOCAL 5-MINUTE DATA
# ============================================================

print("Loading 5-minute data...")

five = pd.read_parquet(FIVE_MIN)

if "timestamp_ny" not in five.columns:
    raise RuntimeError("5m dataset missing timestamp_ny.")

five = five.copy()

five["date_str"] = (
    five["timestamp_ny"]
    .dt.strftime("%Y-%m-%d")
)

five["time_str"] = (
    five["timestamp_ny"]
    .dt.strftime("%H:%M")
)


# ============================================================
# REPORT
# ============================================================

print()
print("=" * 86)
print("DATABENTO NON-AVAILABLE / DEGRADED DAYS: 2020-2023")
print("=" * 86)

print(
    f"Total problem dates returned by metadata: "
    f"{len(problem_days)}"
)

print()


for item in problem_days:

    date = item["date"]
    condition = item["condition"]

    weekday = pd.Timestamp(date).day_name()

    # --------------------------------------------------------
    # 1-MINUTE DATA
    # --------------------------------------------------------

    d1 = one[
        one["ny_date"] == date
    ]

    morning_1m = d1[
        (d1["ny_time"] >= "09:30")
        & (d1["ny_time"] < "10:00")
    ]

    rth_1m = d1[
        (d1["ny_time"] >= "09:30")
        & (d1["ny_time"] < "16:00")
    ]


    # --------------------------------------------------------
    # 5-MINUTE DATA
    # --------------------------------------------------------

    d5 = five[
        five["date_str"] == date
    ]

    morning_5m = d5[
        (d5["time_str"] >= "09:30")
        & (d5["time_str"] < "10:00")
    ]

    rth_5m = d5[
        (d5["time_str"] >= "09:30")
        & (d5["time_str"] < "16:00")
    ]


    morning_complete = int(
        morning_5m["is_complete_5m"].sum()
    )

    rth_complete = int(
        rth_5m["is_complete_5m"].sum()
    )


    # --------------------------------------------------------
    # EXPECTED COUNTS
    # --------------------------------------------------------

    # Full 09:30-10:00 window:
    # 30 one-minute bars
    # 6 complete five-minute bars

    morning_ok = (
        len(morning_1m) == 30
        and len(morning_5m) == 6
        and morning_complete == 6
    )


    # Normal full trading session:
    # 390 one-minute bars
    # 78 five-minute bars
    #
    # NOTE:
    # Early-close sessions will correctly show CHECK here.
    # That does not automatically mean bad data.

    full_rth_ok = (
        len(rth_1m) == 390
        and len(rth_5m) == 78
        and rth_complete == 78
    )


    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print("-" * 86)

    print(
        f"{date} | "
        f"{weekday} | "
        f"condition={condition}"
    )

    print(
        f"  09:30-10:00:"
        f"  1m={len(morning_1m):3d}"
        f"  5m={len(morning_5m):2d}"
        f"  complete5m={morning_complete:2d}"
        f"  -> {'OK' if morning_ok else 'CHECK'}"
    )

    print(
        f"  09:30-16:00:"
        f"  1m={len(rth_1m):3d}"
        f"  5m={len(rth_5m):2d}"
        f"  complete5m={rth_complete:2d}"
        f"  -> {'FULL-RTH OK' if full_rth_ok else 'CHECK'}"
    )


    # --------------------------------------------------------
    # SHOW ANY INCOMPLETE 5-MINUTE BARS
    # --------------------------------------------------------

    incomplete = rth_5m[
        ~rth_5m["is_complete_5m"]
    ]

    if len(incomplete):

        print("  Incomplete RTH 5m bars:")

        for row in incomplete.itertuples():

            print(
                f"    {row.timestamp_ny}"
                f" | minute_count={row.minute_count}"
            )


print()
print("=" * 86)
print("DONE")
print("=" * 86)
