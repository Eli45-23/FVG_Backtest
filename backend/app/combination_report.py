"""Read-only access to the completed Development study. No DB or execution writes."""

import json, hashlib
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from engine.legacy import ROOT

P = ROOT / "work/level-combination-study-v1"
router = APIRouter(prefix="/api/research/level-combinations", tags=["research"])


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
            name="Eight-level combinations",
            segment="development",
        )
    return dict(
        ready=True,
        name="Eight-level combinations",
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
