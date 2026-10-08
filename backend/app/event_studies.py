"""Additive local research service. All outcome access goes through the reveal gate."""

from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
from typing import Literal
import csv, io, json, os, subprocess, sys, threading
import pandas as pd
import pyarrow.parquet as pq
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from backend.app import db
from engine.canonical import clean, dumps, digest
from engine.research.profiles import profile, SEGMENTS
from engine.research.study import snapshot, write_json, version
from engine.research.analysis import select_events, describe, FILTERS

router = APIRouter(prefix="/api/level-research", tags=["Level research"])
pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="event-study")
lock = threading.RLock()
processes = {}


class StudyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(default="Level event study", min_length=1, max_length=160)
    dataset: Literal["legacy_2024_2026", "research_2020_2026"] = "research_2020_2026"
    segment: Literal["development", "validation", "out-of-sample"] = "development"
    start: str = "2020-01-01"
    end: str = "2020-02-01"
    session: dict = Field(default_factory=dict)
    research_version: Literal[1, 2] = 1
    research_settings: dict = Field(default_factory=dict)


def root(id):
    # Only called after finding a database record; user input never selects arbitrary paths.
    return db.STORE / "event_studies" / id


def require(s, id):
    r = s.get(db.EventStudy, id)
    if not r:
        raise HTTPException(404, "Event study not found")
    return r


def detail(s, r):
    return {
        **db.encode(r),
        "oos_revealed": s.get(db.EventReveal, r.id) is not None,
        "reveal": (
            db.encode(s.get(db.EventReveal, r.id))
            if s.get(db.EventReveal, r.id)
            else None
        ),
        "outcomes_available": r.status == "completed"
        and (
            r.config["segment"] != "out-of-sample"
            or s.get(db.EventReveal, r.id) is not None
        ),
    }


def gate(id, outcomes=False):
    with db.Session() as s:
        r = detail(s, require(s, id))
    if outcomes and not r["outcomes_available"]:
        raise HTTPException(
            409, "Outcomes unavailable: study incomplete or OOS is sealed"
        )
    return r


@lru_cache(maxsize=12)
def _load(path, mtime):
    return json.loads(Path(path).read_text())


def load(id, name):
    p = root(id) / name
    if not p.exists():
        raise HTTPException(409, "Study artifact is not ready")
    return _load(str(p), p.stat().st_mtime_ns)


def execute(id, mode):
    with lock, db.Session.begin() as s:
        r = require(s, id)
        if r.status == "cancelled":
            return
        r.status = "running"
    try:
        with (root(id) / f"{mode}.log").open("w") as log:
            env = {
                k: v
                for k, v in os.environ.items()
                if k in ("PATH", "HOME", "LANG", "TMPDIR", "VIRTUAL_ENV")
            }
            p = subprocess.Popen(
                [sys.executable, "-m", "backend.app.event_worker", str(root(id)), mode],
                cwd=db.ROOT,
                env=env,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
            with lock:
                processes[id] = p
                with db.Session() as s:
                    if require(s, id).status == "cancelled":
                        p.terminate()
            try:
                code = p.wait(timeout=3600)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
                raise ValueError("Research worker exceeded one hour")
            if code:
                raise ValueError("Research worker failed; see local study log")
        with lock, db.Session.begin() as s:
            r = require(s, id)
            if r.status != "cancelled":
                r.status = (
                    "sealed"
                    if mode == "detect" and r.config["segment"] == "out-of-sample"
                    else "completed"
                )
    except Exception as e:
        with db.Session.begin() as s:
            r = require(s, id)
            if r.status != "cancelled":
                r.status = "failed"
                r.error = str(e)
    finally:
        with lock:
            processes.pop(id, None)


@router.get("/profiles")
def profiles():
    result = []
    for id in ["legacy_2024_2026", "research_2020_2026"]:
        p = profile(id)
        result.append({**p.identity(), "segments": SEGMENTS, "status": "available"})
    return result


@router.post("/studies")
def create(body: StudyBody):
    config = snapshot(body.model_dump(exclude={"name"}))
    with db.Session.begin() as s:
        r = db.EventStudy(name=body.name, config=config, config_hash=digest(config))
        s.add(r)
        s.flush()
        id = r.id
    root(id).mkdir(parents=True, exist_ok=False)
    write_json(root(id) / "config.json", config)
    pool.submit(execute, id, "detect")
    return {"id": id}


@router.get("/studies")
def studies():
    with db.Session() as s:
        return [
            detail(s, r)
            for r in s.scalars(
                select(db.EventStudy).order_by(db.EventStudy.created_at.desc())
            )
        ]


@router.get("/studies/{id}")
def study(id: str):
    return gate(id)


@router.post("/studies/{id}/cancel")
def cancel(id: str):
    with lock, db.Session.begin() as s:
        r = require(s, id)
        if r.status not in ("queued", "running"):
            raise ValueError("Only active studies can be cancelled")
        r.status = "cancelled"
        if id in processes:
            processes[id].terminate()
    return {"id": id, "status": "cancelled"}


@router.post("/studies/{id}/reveal")
def reveal(id: str):
    with lock, db.Session.begin() as s:
        r = require(s, id)
        if s.get(db.EventReveal, id):
            return {"id": id, "status": r.status}
        if r.config["segment"] != "out-of-sample" or r.status != "sealed":
            raise ValueError(
                "Only a completed sealed OOS detection can be explicitly revealed"
            )
        if (
            r.config["dataset_identity"] != profile(r.config["dataset"]).identity()
            or r.config["research_engine_version"] != version()
        ):
            raise ValueError("Frozen research identity changed; create a new study")
        s.add(db.EventReveal(study_id=id, config_hash=r.config_hash))
        r.status = "queued"
    pool.submit(execute, id, "label")
    return {"id": id, "status": "queued"}


def filtered(id, filters):
    gate(id)
    return select_events(load(id, "events.json"), filters)


@router.get("/studies/{id}/events")
def events(
    id: str,
    level_type: str = "",
    interaction_type: str = "",
    direction: str = "",
    touch_number: str = "",
    time_bucket: str = "",
    year: str = "",
    weekday: str = "",
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    filters = {k: v for k, v in locals().copy().items() if k in FILTERS}
    meta = gate(id)
    if meta["config"].get("research_version") == 2:
        from engine.research.queries import page

        return page(root(id), filters, offset=offset, limit=limit)
    rows = filtered(id, filters)
    return {"count": len(rows), "events": rows[offset : offset + limit]}


@router.get("/studies/{id}/summary")
def summary(
    id: str,
    horizon: Literal["5", "10", "15", "30", "60", "session_close"] = "30",
    interpretation: Literal["continuation", "rejection"] = "continuation",
    level_type: str = "",
    interaction_type: str = "",
    direction: str = "",
    touch_number: str = "",
    time_bucket: str = "",
    year: str = "",
    weekday: str = "",
):
    gate(id, True)
    filters = {k: v for k, v in locals().copy().items() if k in FILTERS}
    rows = filtered(id, filters)
    labels = load(id, "outcomes.json")
    base = load(id, "observations.json")
    bl = load(id, "baseline_outcomes.json")
    result = describe(rows, labels, base, bl, horizon, interpretation)
    groups = {}
    for key in [
        "year",
        "time_bucket",
        "level_type",
        "interaction_type",
        "touch_number",
    ]:
        groups[key] = [
            {
                key: value,
                **describe(
                    [e for e in rows if e[key] == value],
                    labels,
                    base,
                    bl,
                    horizon,
                    interpretation,
                ),
            }
            for value in sorted({e[key] for e in rows}, key=str)
        ]
    return {
        "overall": result,
        "groups": groups,
        "horizon": horizon,
        "interpretation": interpretation,
    }


@router.get("/studies/{id}/export")
def export(id: str, format: Literal["json", "csv"] = "json"):
    meta = gate(id, True)
    if meta["config"].get("research_version") == 2:
        from engine.research.columnar import export_rows

        def stream():
            if format == "json":
                yield '{"config":' + dumps(meta["config"]) + ',"config_hash":' + dumps(
                    meta["config_hash"]
                )
                for kind in ("events", "observations", "outcomes"):
                    yield ',"' + kind + '":['
                    first = True
                    for payload in export_rows(root(id), kind):
                        yield ("" if first else ",") + payload
                        first = False
                    yield "]"
                yield "}"
            else:
                out = io.StringIO()
                writer = csv.writer(out)
                writer.writerow(["event_id", "event_json"])
                yield out.getvalue()
                out.seek(0)
                out.truncate(0)
                for payload in export_rows(root(id), "events"):
                    writer.writerow([json.loads(payload)["event_id"], payload])
                    yield out.getvalue()
                    out.seek(0)
                    out.truncate(0)

        return StreamingResponse(
            stream(),
            media_type="application/json" if format == "json" else "text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="event-study-{id}.{format}"'
            },
        )
    rows = load(id, "events.json")
    labels = load(id, "outcomes.json")
    if format == "json":
        content = dumps(
            {
                "config": meta["config"],
                "config_hash": meta["config_hash"],
                "events": rows,
                "outcomes": labels,
                "baseline_observations": load(id, "observations.json"),
                "baseline_outcomes": load(id, "baseline_outcomes.json"),
            }
        )
        mime = "application/json"
    else:
        flat = [{**e, "outcomes_json": dumps(labels[e["event_id"]])} for e in rows]
        out = io.StringIO()
        writer = csv.DictWriter(
            out, fieldnames=list(flat[0]) if flat else ["event_id", "outcomes_json"]
        )
        writer.writeheader()
        writer.writerows(flat)
        content = out.getvalue()
        mime = "text/csv"
    return Response(
        content,
        media_type=mime,
        headers={
            "Content-Disposition": f'attachment; filename="event-study-{id}.{format}"'
        },
    )


@router.get("/studies/{id}/events/{event_id}/chart")
def chart(id: str, event_id: str):
    meta = gate(id)
    if (
        meta["config"]["dataset_identity"]
        != profile(meta["config"]["dataset"]).identity()
    ):
        raise HTTPException(
            409, "Dataset changed since study; original chart cannot be reconstructed"
        )
    if meta["config"].get("research_version") == 2:
        from engine.research.columnar import query

        found = query(
            root(id), "SELECT payload FROM events WHERE event_id=?", [event_id]
        )
        event = json.loads(found[0]["payload"]) if found else None
    else:
        event = next(
            (e for e in load(id, "events.json") if e["event_id"] == event_id), None
        )
    if not event:
        raise HTTPException(404, "Event not found")
    at = pd.Timestamp(event["timestamp_utc"])
    start = at - pd.Timedelta(minutes=60)
    # Sealed OOS charts end at confirmation; no predictive future candle data.
    end = (
        min(at + pd.Timedelta(minutes=60), pd.Timestamp(event["session_close"]))
        if meta["outcomes_available"]
        else at
    )
    bars = pq.read_table(
        profile(meta["config"]["dataset"]).bars,
        filters=[
            ("timestamp_utc", ">=", start.to_pydatetime()),
            ("timestamp_utc", "<", end.to_pydatetime()),
        ],
    ).to_pylist()
    from engine.research.chart_context import annotations

    extra_annotations = annotations(event, start, end)
    return {
        "event": event,
        "candles": clean(bars),
        "future_hidden": not meta["outcomes_available"],
        "annotations": [
            {
                "type": "horizontal_line",
                "price": float(event["level_price"]),
                "start_time": str(
                    max(start, pd.Timestamp(event["level_available_at"]))
                ),
                "end_time": str(end),
                "label": event["level_type"],
                "color": "#f5bf5b",
                "category": "level",
            },
            {
                "type": "vertical_marker",
                "start_time": event["timestamp_utc"],
                "label": event["interaction_type"],
                "color": "#65b9ef",
                "category": "event",
            },
        ]
        + extra_annotations,
    }


def recover_interrupted():
    """A service restart never silently reruns a paid-in-time historical study."""
    with db.Session.begin() as s:
        for row in s.scalars(
            select(db.EventStudy).where(db.EventStudy.status.in_(["queued", "running"]))
        ):
            row.status = "failed"
            row.error = (
                "Service restarted before study completed; create a new immutable study"
            )


def cancel_active():
    with db.Session() as s:
        ids = [
            row.id
            for row in s.scalars(
                select(db.EventStudy).where(
                    db.EventStudy.status.in_(["queued", "running"])
                )
            )
        ]
    for id in ids:
        try:
            cancel(id)
        except ValueError:
            pass


class ResearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filters: dict[str, str] = Field(default_factory=dict)
    numeric: dict = Field(default_factory=dict)
    group: str = "year"
    horizon: Literal["5", "10", "15", "30", "60", "session_close"] = "30"
    interpretation: Literal["continuation", "rejection"] = "continuation"
    threshold: Literal[10, 25, 50, 75, 100] = 50
    threshold_atr: float | None = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)
    sort: str = "timestamp_utc"
    descending: bool = False


@router.post("/studies/{id}/query")
def research_query(id: str, body: ResearchQuery):
    meta = gate(id)
    if meta["config"].get("research_version") != 2:
        raise ValueError("Use the legacy query for a JSON v1 study")
    from engine.research.queries import page

    return page(
        root(id),
        body.filters,
        body.numeric,
        body.offset,
        body.limit,
        body.sort,
        body.descending,
    )


@router.post("/studies/{id}/statistics")
def research_statistics(id: str, body: ResearchQuery):
    meta = gate(id, True)
    if meta["config"].get("research_version") != 2:
        raise ValueError("Confidence statistics require a v2 study")
    from engine.research.queries import summary

    return summary(
        root(id),
        meta["config"],
        body.filters,
        body.numeric,
        body.group,
        body.horizon,
        body.threshold,
        body.interpretation,
        body.threshold_atr,
    )


@router.get("/fields")
def research_fields():
    from engine.research.numeric import NUMERIC, CATEGORIES

    return {"numeric": NUMERIC, "categorical": CATEGORIES}
