from pathlib import Path
import hashlib

import databento as db
import pandas as pd


DATA_DIR = Path(
    "/Users/DayTrade/Documents/Codex/2026-10-06/"
    "1-connect-to-databento-2-request/outputs/data"
)

OLD_FILE = DATA_DIR / (
    "GLBX.MDP3_MNQ.v.0_ohlcv-1m_2024-01-01_2026-10-06.parquet"
)

OUTPUT_FILE = DATA_DIR / (
    "GLBX.MDP3_MNQ.v.0_ohlcv-1m_2020-01-01_2026-10-06.parquet"
)

YEARS = ["2020", "2021", "2022", "2023"]

COLUMNS = [
    "rtype",
    "publisher_id",
    "instrument_id",
    "open",
    "high",
    "low",
    "close",
    "volume",
]


def sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


# ============================================================
# SAFETY
# ============================================================

if not OLD_FILE.exists():
    raise FileNotFoundError(
        f"Validated 2024-2026 source not found:\n{OLD_FILE}"
    )

if OUTPUT_FILE.exists():
    raise FileExistsError(
        f"Master output already exists:\n{OUTPUT_FILE}\n"
        "Refusing to overwrite it."
    )


# ============================================================
# LOAD 2020-2023 DATABENTO FILES
# ============================================================

frames = []

for year in YEARS:

    path = DATA_DIR / (
        f"GLBX.MDP3_MNQ.v.0_ohlcv-1m_{year}.dbn.zst"
    )

    if not path.exists():
        raise FileNotFoundError(path)

    print(f"Loading {year}...")

    store = db.DBNStore.from_file(path)

    df = store.to_df(
        price_type="fixed",
        pretty_ts=True,
    )

    # Databento normally places ts_event in the index.
    if df.index.name != "ts_event":

        if "ts_event" in df.columns:
            df = df.set_index("ts_event")

        else:
            raise RuntimeError(
                f"{year}: ts_event not found"
            )

    # Keep EXACTLY the same raw columns used by the
    # validated 2024-2026 parquet.
    missing = [
        col for col in COLUMNS
        if col not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"{year}: missing columns: {missing}"
        )

    df = df[COLUMNS].copy()

    frames.append(df)

    print(
        f"{year}: "
        f"{len(df):,} rows | "
        f"{df.index.min()} -> {df.index.max()}"
    )


# ============================================================
# LOAD VALIDATED 2024-2026 SOURCE
# ============================================================

print()
print("Loading validated 2024-2026 source...")

old_hash_before = sha256(OLD_FILE)

old = pd.read_parquet(OLD_FILE)

if old.index.name != "ts_event":
    raise RuntimeError(
        "Validated 2024-2026 parquet index is not ts_event."
    )

if list(old.columns) != COLUMNS:
    raise RuntimeError(
        "Validated source columns differ from expected schema.\n"
        f"Found: {list(old.columns)}"
    )

frames.append(old)

print(
    f"2024-2026: "
    f"{len(old):,} rows | "
    f"{old.index.min()} -> {old.index.max()}"
)


# ============================================================
# CONCATENATE
# ============================================================

print()
print("Combining datasets...")

master = pd.concat(
    frames,
    axis=0,
)

master = master.sort_index()


# ============================================================
# VALIDATION
# ============================================================

duplicates = master.index.duplicated().sum()

if duplicates:
    raise RuntimeError(
        f"Master contains {duplicates:,} duplicate timestamps."
    )

if not master.index.is_monotonic_increasing:
    raise RuntimeError(
        "Master timestamp index is not monotonic."
    )

missing_ohlc = master[
    ["open", "high", "low", "close"]
].isna().any(axis=1).sum()

invalid_ohlc = (
    (master["high"] < master["low"])
    | (master["open"] > master["high"])
    | (master["open"] < master["low"])
    | (master["close"] > master["high"])
    | (master["close"] < master["low"])
).sum()

if missing_ohlc:
    raise RuntimeError(
        f"Master has {missing_ohlc:,} missing OHLC rows."
    )

if invalid_ohlc:
    raise RuntimeError(
        f"Master has {invalid_ohlc:,} invalid OHLC rows."
    )


# ============================================================
# VERIFY OLD DATA SURVIVED BYTE-FOR-BYTE LOGICALLY
# ============================================================

master_old_period = master.loc[
    old.index.min():old.index.max()
]

if not master_old_period.equals(old):
    raise RuntimeError(
        "2024-2026 portion of master does NOT exactly equal "
        "the validated original dataframe."
    )

old_hash_after = sha256(OLD_FILE)

if old_hash_before != old_hash_after:
    raise RuntimeError(
        "Validated original file hash changed unexpectedly."
    )


# ============================================================
# SAVE NEW MASTER
# ============================================================

print()
print("Writing new master parquet...")

master.to_parquet(
    OUTPUT_FILE,
    engine="pyarrow",
    compression="zstd",
)


# ============================================================
# READ-BACK VERIFICATION
# ============================================================

check = pd.read_parquet(OUTPUT_FILE)

if not check.equals(master):
    raise RuntimeError(
        "Saved master does not match in-memory master."
    )


# ============================================================
# REPORT
# ============================================================

print()
print("=" * 72)
print("MNQ 2020-2026 MASTER DATASET COMPLETE")
print("=" * 72)

print(f"Rows: {len(master):,}")
print(f"First timestamp: {master.index.min()}")
print(f"Last timestamp:  {master.index.max()}")

print(f"Duplicate timestamps: {duplicates:,}")
print(f"Missing OHLC rows: {missing_ohlc:,}")
print(f"Invalid OHLC rows: {invalid_ohlc:,}")

print()
print("Rows by calendar year:")

year_counts = (
    master.groupby(master.index.year)
    .size()
)

for year, count in year_counts.items():
    print(f"  {year}: {count:,}")

print()
print(f"Master file:")
print(OUTPUT_FILE)

print()
print(f"Master SHA256:")
print(sha256(OUTPUT_FILE))

print()
print("Validated 2024-2026 original SHA256:")
print(old_hash_after)

print()
print("2024-2026 portion matches original exactly: YES")

print()
print("MASTER BUILD VERIFIED")
