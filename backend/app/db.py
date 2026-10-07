"""SQLite metadata. Migration v1 is additive; source/config snapshots are immutable."""

import os
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    text,
    event,
    UniqueConstraint,
    create_engine,
    String,
    Integer,
    Text,
    JSON,
    ForeignKey,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

ROOT = Path(__file__).resolve().parents[2]
STORE = Path(os.environ.get("LAB_STORAGE", ROOT / "storage")).resolve()
STORE.mkdir(parents=True, exist_ok=True)
engine = create_engine(
    "sqlite:///" + str(STORE / "app.db"), connect_args={"check_same_thread": False}
)


@event.listens_for(engine, "connect")
def configure_sqlite(connection, record):
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")


Session = sessionmaker(engine, expire_on_commit=False)


def uid():
    return uuid4().hex


def now():
    return datetime.now(timezone.utc).isoformat()


class Base(DeclarativeBase):
    pass


class Migration(Base):
    __tablename__ = "schema_migrations"
    version: Mapped[int] = mapped_column(primary_key=True)


class Strategy(Base):
    __tablename__ = "strategies"
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    name: Mapped[str]
    description: Mapped[str] = mapped_column(default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    archived: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[str] = mapped_column(default=now)
    updated_at: Mapped[str] = mapped_column(default=now)
    current_version: Mapped[int] = mapped_column(default=1)


class Version(Base):
    __tablename__ = "strategy_versions"
    __table_args__ = (UniqueConstraint("strategy_id", "number"),)
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"))
    number: Mapped[int]
    source: Mapped[str] = mapped_column(Text)
    source_hash: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now)


class Variant(Base):
    __tablename__ = "variants"
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    strategy_version_id: Mapped[str] = mapped_column(ForeignKey("strategy_versions.id"))
    name: Mapped[str]
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[str] = mapped_column(default="")
    created_at: Mapped[str] = mapped_column(default=now)


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    name: Mapped[str]
    strategy_version_id: Mapped[str] = mapped_column(ForeignKey("strategy_versions.id"))
    variant_id: Mapped[str | None] = mapped_column(
        ForeignKey("variants.id"), nullable=True
    )
    config: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(default="queued")
    created_at: Mapped[str] = mapped_column(default=now)
    finished_at: Mapped[str | None] = mapped_column(nullable=True)
    duration: Mapped[float | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(nullable=True)
    notes: Mapped[str] = mapped_column(default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    progress: Mapped[str] = mapped_column(default="Queued")


class RunMetric(Base):
    __tablename__ = "run_metrics"
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)


class Artifact(Base):
    __tablename__ = "run_artifacts"
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"))
    kind: Mapped[str]
    path: Mapped[str]


class Sweep(Base):
    __tablename__ = "sweeps"
    id: Mapped[str] = mapped_column(primary_key=True, default=uid)
    name: Mapped[str]
    definition: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)


class SweepRun(Base):
    __tablename__ = "sweep_runs"
    sweep_id: Mapped[str] = mapped_column(ForeignKey("sweeps.id"), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), primary_key=True)
    value: Mapped[object] = mapped_column(JSON)


def migrate():
    Base.metadata.create_all(engine)
    with Session.begin() as s:
        if s.get(Migration, 1) is None:
            s.add(Migration(version=1))
        if s.get(Migration, 2) is None:
            s.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS strategy_version_unique ON strategy_versions(strategy_id, number)"
                )
            )
            s.add(Migration(version=2))


def encode(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}
