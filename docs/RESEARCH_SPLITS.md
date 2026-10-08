# Development, Validation and Out-of-Sample

Experiments provide a local workflow safeguard, not a security boundary or mathematical
protection from overfitting. Raw OOS files remain accessible and ordinary ad-hoc research
can inspect dates. Official experiment results require a captured source/config and reveal.

## Dates and profiles
All ranges use NY calendar dates, start inclusive and **end exclusive**, matching v1 runs.
For contiguous ranges corresponding to the user's example, enter:

| Segment | Start | End (exclusive) |
|---|---|---|
| Development | 2024-01-01 | 2026-01-01 |
| Validation | 2026-01-01 | 2026-07-01 |
| Out-of-Sample | 2026-07-01 | 2026-10-06 |

A one-date segment ends on the following date. Empty/reversed intervals, overlaps,
wrong order and requests outside the existing coverage contract are rejected. Gaps are
allowed with warnings. Entering 2025-12-31 as an exclusive Development end leaves that date
out; the UI makes the convention explicit. The final available NY date is partial.
Profiles are append-only; create another to intentionally redefine research use.

## Workflow
1. Open/save a strategy version; select its inputs and execution settings in the editor.
2. Experiments → Create Research Split, or choose an existing profile.
3. Create experiment snapshot. Source/version/hash, resolved inputs, variant, instrument,
   timeframe, quantity/costs, execution/session rules, ranges, data and engine identities
   are captured. Snapshot config is immutable even while Development/Validation run.
4. Run Development, inspect. Then run Validation, inspect.
5. Freeze for Out-of-Sample requires both stages completed and unchanged engine/data identity.
6. Explicitly choose Run / Reveal OOS. The confirmation records the exposure and run
   timestamps. No official OOS backtest or performance is generated beforehand.
7. Inspect separate segment rows or the clearly labeled combined revealed-segment result.

Source/input changes require a new experiment. Old source/config remains immutable.
Freeze is idempotent; repeated Run buttons return an existing active/completed segment run.
Failed/cancelled attempts may be retried with the same identity and retain their relationships.
Official OOS records retain experiment_snapshot_id and snapshot hash. Database triggers
protect historical config/relationships. Engine/data changes require a new snapshot, not
silent execution against a different implementation. The platform does not retain runnable
old engine environments; the old Git version and pinned dependencies remain recoverable.

## Sweeps and comparisons
Sweeps default to Development. Selecting a profile supplies that segment's dates. Validation
requires an explicit advanced checkbox/API flag and records it. Official OOS sweeps are
rejected server-side. Unscoped sweeps are retained for v1 compatibility but are blocked when
their date range overlaps frozen OOS. To research former OOS later, create/select a NEW profile
that honestly labels those dates Development/Validation. Do not present it as untouched OOS.

Standalone out-of-sample-labeled submissions are rejected: use frozen experiments. Full-sample
and ad-hoc runs remain available. Old v1 segment labels remain readable as historical labels.
Cloning an official run creates an ad-hoc run, not a new official OOS evaluation. Comparisons
warn on dates/settings, segment, split, source, management, engine and data differences.

## Persistence / API
Migration 3 adds research_splits, experiment_snapshots and experiment_runs; no existing table
is reset. The immutable snapshot includes all three ranges and a canonical hash; audit columns
store created, frozen, OOS-run and OOS-reveal times. Management logs remain run artifacts.

Endpoints: GET/POST /api/research-splits; GET/POST /api/experiments;
GET /api/experiments/{id}; POST .../{id}/run with segment;
POST .../{id}/freeze; GET .../{id}/combined.
There is no endpoint to rewrite historical snapshots or source versions.
