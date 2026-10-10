"""Verified local Development exports only; no database or master market-data access."""

import json, hashlib, re
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from engine.legacy import ROOT

P = ROOT / "work/simple-strategy-discovery-v1"
router = APIRouter(prefix="/api/research/simple-discovery", tags=["research"])


def manifest():
    p = P / "reproducibility_manifest.json"
    if not p.exists():
        raise HTTPException(409, "Verification pending")
    m = json.loads(p.read_text())
    if m.get("status") != "PASS" or m.get("segment") != "development":
        raise HTTPException(409, "Verified Development study required")
    return m


@router.get("")
def status():
    try:
        m = manifest()
    except HTTPException:
        return dict(ready=False)
    return dict(ready=True, events=m["entry_records"])


@router.get("/files/{name:path}")
def file(name: str):
    m = manifest()
    if name not in m["artifacts"]:
        raise HTTPException(404, "Unknown artifact")
    p = (P / name).resolve()
    if not p.is_relative_to(P.resolve()) or not p.is_file():
        raise HTTPException(404, "Artifact unavailable")
    with p.open("rb") as f:
        actual = hashlib.file_digest(f, "sha256").hexdigest()
    if actual != m["artifacts"][name]["sha256"]:
        raise HTTPException(409, "Artifact changed")
    return FileResponse(
        p,
        media_type="text/html" if name.endswith(".html") else None,
        filename=None if name.endswith(".html") else p.name,
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/chart/{signal_id}")
def chart(signal_id: str, mode: str, ticks: int = 1):
    import pandas as pd
    import pyarrow.parquet as pq

    if not re.fullmatch("[a-f0-9]{64}", signal_id):
        raise HTTPException(404, "Unknown trade")
    file("trades.csv")
    file("chart_bars.parquet")
    t = pd.read_csv(P / "trades.csv")
    t = t[(t.signal_id == signal_id) & (t["mode"] == mode) & (t.ticks == ticks)]
    if len(t) != 1:
        raise HTTPException(404, "Unknown trade")
    r = t.iloc[0]
    if not "2020-01-01" <= r.date < "2024-01-01":
        raise HTTPException(409, "Development only")
    g = pq.read_table(
        P / "chart_bars.parquet", filters=[("date", "=", r.date)]
    ).to_pandas()
    bars = [
        dict(
            timestamp_utc=b.timestamp_utc.isoformat(),
            **{k: float(getattr(b, k)) for k in ["open", "high", "low", "close"]}
        )
        for b in g.itertuples()
    ]
    keys = [
        "hypothesis",
        "direction",
        "entry_time_utc",
        "entry_time_ny",
        "entry_price",
        "stop_price",
        "target_price",
        "exit_time_utc",
        "exit_price",
    ]
    return JSONResponse(
        dict(
            trade={k: r[k].item() if hasattr(r[k], "item") else r[k] for k in keys},
            bars=bars,
        )
    )
