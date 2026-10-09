"""Read-only access to the completed Development study. No DB or execution writes."""

import json, hashlib
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from engine.legacy import ROOT

P = ROOT / "work/o15l-clear-hold-sequential-v1"
router = APIRouter(prefix="/api/research/o15l-clear-hold", tags=["research"])


def manifest():
    path = P / "reproducibility_manifest.json"
    if not path.exists():
        raise HTTPException(409, "Study verification is not complete")
    value = json.loads(path.read_text())
    if value.get("status") != "PASS" or value.get("segment") != "development":
        raise HTTPException(409, "Verified Development study required")
    return value


@router.get("")
def status():
    try:
        m = manifest()
    except HTTPException:
        return dict(
            ready=False,
            name="O15L clearance-and-hold · 1R",
            segment="development",
        )
    return dict(
        ready=True,
        name="O15L clearance-and-hold · 1R",
        segment="development",
        events=m["entry_records"],
        start="2020-01-01",
        end_exclusive="2024-01-01",
    )


@router.get("/files/{name:path}")
def file(name: str):
    m = manifest()
    if name not in m["artifacts"]:
        raise HTTPException(404, "Unknown study artifact")
    path = (P / name).resolve()
    if not path.is_relative_to(P.resolve()) or not path.is_file():
        raise HTTPException(404, "Artifact unavailable")
    expected = m["artifacts"][name]["sha256"]
    with path.open("rb") as f:
        actual = hashlib.file_digest(f, "sha256").hexdigest()
    if actual != expected:
        raise HTTPException(409, "Artifact differs from verified study")
    media = (
        "text/html"
        if name.endswith(".html")
        else "image/svg+xml" if name.endswith(".svg") else None
    )
    return FileResponse(
        path,
        media_type=media,
        filename=None if media else path.name,
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/chart/{signal_id}")
def chart(signal_id: str):
    """Retrospective view of one verified Development trade; no market master reads."""
    import re
    import pandas as pd
    import pyarrow.parquet as pq
    from fastapi.responses import JSONResponse

    if not re.fullmatch(r"[a-f0-9]{64}", signal_id):
        raise HTTPException(404, "Unknown trade")
    # Reuse the file guard, including full artifact hash verification.
    file("trades_1tick.csv")
    file("chart_bars.parquet")
    trades = pd.read_csv(P / "trades_1tick.csv")
    selected = trades[trades.signal_id.eq(signal_id)]
    if len(selected) != 1:
        raise HTTPException(404, "Unknown trade")
    trade = selected.iloc[0]
    if not "2020-01-01" <= trade["date"] < "2024-01-01":
        raise HTTPException(409, "Development trade required")
    bars = pq.read_table(
        P / "chart_bars.parquet", filters=[("date", "=", trade["date"])]
    ).to_pandas()
    rows = []
    for r in bars.itertuples():
        rows.append(
            dict(
                timestamp_utc=r.timestamp_utc.isoformat(),
                open=float(r.open),
                high=float(r.high),
                low=float(r.low),
                close=float(r.close),
                complete=bool(r.is_complete_5m),
            )
        )
    keys = [
        "signal_id",
        "direction",
        "entry_time_utc",
        "entry_time_ny",
        "entry_price",
        "stop_price",
        "target_price",
        "exit_time_utc",
        "exit_price",
        "opening_high",
        "opening_low",
        "level_available_at",
        "net_pnl_usd",
        "barrier_price",
        "root_confirmation",
        "clearance_confirmation",
    ]
    return JSONResponse(
        dict(
            trade={
                k: trade[k].item() if hasattr(trade[k], "item") else trade[k]
                for k in keys
            },
            bars=rows,
        )
    )
