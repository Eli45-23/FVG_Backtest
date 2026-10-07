"""Typed response contracts. Metrics keep extensible nested research groups."""

from typing import Any, Literal
from pydantic import BaseModel, Field


class StrategyResponse(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str]
    archived: bool
    created_at: str
    updated_at: str
    current_version: int
    version_id: str
    source: str
    source_hash: str


class VersionResponse(BaseModel):
    run_count: int = 0
    variant_count: int = 0
    id: str
    strategy_id: str
    number: int
    source: str
    source_hash: str
    created_at: str


class VariantResponse(BaseModel):
    id: str
    strategy_version_id: str
    name: str
    parameters: dict[str, Any]
    config: dict[str, Any]
    notes: str
    created_at: str


class ValidationResponse(BaseModel):
    management: dict[str, Any] = Field(default_factory=dict)
    valid: bool
    name: str | None = None
    inputs: list[dict[str, Any]] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    line: int | None = None


class RunResponse(BaseModel):
    run_type: str = "AD_HOC"
    experiment_snapshot_id: str | None = None
    id: str
    name: str
    strategy_version_id: str
    variant_id: str | None
    config: dict[str, Any]
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    created_at: str
    finished_at: str | None
    duration: float | None
    error: str | None
    notes: str
    tags: list[str]
    progress: str
    metrics: dict[str, Any] | None


class Submitted(BaseModel):
    id: str
