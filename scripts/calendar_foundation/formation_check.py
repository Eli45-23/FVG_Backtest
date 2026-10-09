"""Independent deterministic structural checks, not discretionary acceptance."""

import json
from dataclasses import asdict
import pandas as pd
from engine.zone_v2.provider import ProviderConfig
from scripts.calendar_foundation.audit import OUT


def main():
    bars = pd.read_parquet(OUT / "four_hour_bar_inventory.parquet").set_index(
        "timestamp"
    )
    zones = []
    for side in ("supply", "demand"):
        zones.extend(
            json.loads(x)
            for x in pd.read_parquet(OUT / f"detected_{side}_zones.parquet").payload
        )
    rows = []
    for z in zones:
        base = bars.loc[pd.to_datetime(z["base_timestamps"])]
        dep = bars.loc[pd.to_datetime(z["departure_timestamps"])]
        full = pd.concat([base, dep])
        if z["zone_type"] == "SUPPLY":
            top, bottom = base.high.max(), base[["open", "close"]].min().min()
        else:
            top, bottom = base[["open", "close"]].max().max(), base.low.min()
        rows.append(
            dict(
                zone_id=z["zone_id"],
                zone_type=z["zone_type"],
                boundaries_exact=bool((top, bottom) == (z["top"], z["bottom"])),
                all_source_bars_accepted=bool(
                    (full.complete & full.full & full.schedule_resolved).all()
                ),
                base_departure_disjoint=not bool(set(base.index) & set(dep.index)),
                adjacent=all(
                    full.availability_timestamp.iloc[i] == full.index[i + 1]
                    for i in range(len(full) - 1)
                ),
                availability_exact=dep.availability_timestamp.iloc[-1]
                == pd.Timestamp(z["availability_timestamp"]),
                base_atr_exact=base.atr14.iloc[-1] == z["atr14"],
                thresholds_unchanged=z["configuration"] == asdict(ProviderConfig()),
            )
        )
    df = pd.DataFrame(rows)
    assert df.drop(columns=["zone_id", "zone_type"]).all().all()
    df.to_csv(OUT / "formation_audit.csv", index=False)
    print(
        len(df),
        "formations: exact boundaries, timing, adjacency, ATR and frozen config",
    )


if __name__ == "__main__":
    main()
