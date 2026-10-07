"""Immutable source history, comparison and append-only restoration."""

import difflib
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from backend.app import db, services

router = APIRouter(prefix="/api/versions")


def require(s, id):
    v = s.get(db.Version, id)
    if not v:
        raise HTTPException(404, "Source version not found")
    return v


@router.get("/{id}")
def detail(id: str):
    with db.Session() as s:
        v = require(s, id)
        return {
            **db.encode(v),
            "runs": [
                db.encode(r)
                for r in s.scalars(
                    select(db.Run).where(db.Run.strategy_version_id == id)
                )
            ],
            "variants": [
                db.encode(r)
                for r in s.scalars(
                    select(db.Variant).where(db.Variant.strategy_version_id == id)
                )
            ],
        }


@router.get("/{left}/diff/{right}")
def diff(left: str, right: str):
    with db.Session() as s:
        a = require(s, left)
        b = require(s, right)
        return {
            "original": db.encode(a),
            "modified": db.encode(b),
            "unified_diff": "".join(
                difflib.unified_diff(
                    a.source.splitlines(True),
                    b.source.splitlines(True),
                    fromfile=f"v{a.number}",
                    tofile=f"v{b.number}",
                )
            ),
        }


class CloneBody(BaseModel):
    name: str = Field(min_length=1, max_length=160)


@router.post("/{id}/clone")
def clone(id: str, body: CloneBody):
    with db.Session.begin() as s:
        v = require(s, id)
        st = db.Strategy(
            name=body.name,
            description=f"Cloned source version {v.number}",
            tags=["historical-clone"],
        )
        s.add(st)
        s.flush()
        new = services.version(s, st, v.source)
        return {"strategy_id": st.id, "version_id": new.id}


@router.post("/{id}/restore")
def restore(id: str):
    with db.Session.begin() as s:
        v = require(s, id)
        st = s.get(db.Strategy, v.strategy_id)
        new = services.version(s, st, v.source, force=True)
        return {
            "strategy_id": st.id,
            "version_id": new.id,
            "number": new.number,
            "restored_from": v.id,
        }
