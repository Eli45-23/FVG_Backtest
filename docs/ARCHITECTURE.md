# Strategy Research Lab: audit and staged migration

## Phase 0 audit (before implementation)
Starting commit: 4b2f764. Working tree clean. All 156 unittest tests pass.
Read AGENTS.md, all validated data/detection/lifecycle/execution/metrics sources,
test modules and methodology reports. No credentials or .env were read.

Current layout places CLI code, tests, reports and ignored data under outputs/.
Data pipeline: download_mnq -> build_5m -> detect_fvgs -> fvg_lifecycle.
Execution: cont_a_backtest.signals -> select -> levels -> execute -> metrics.
Variants reuse these functions with eligibility applied before daily selection.
The two lifecycle invalidation models are descriptive alternatives, not execution filters.

Reusable components: exact Decimal price conversion; validated bars/FVG Parquet;
calendar; tick rounding; sequential minute execution; metrics; independent integer
execution verifier. Coupling: fixed ROOT/input paths; FVG-shaped signal dictionaries;
fixed MNQ/session/daily-lock assumptions; monolithic CLI orchestration; metrics expect
legacy records. Empty results require adapter handling. None of these are casually rewritten.

## Migration boundary
Keep every outputs/*.py reference runner and prior report unchanged. Add engine/
as an adapter layer and strategies/ as editable strategy definitions. Capture golden
fingerprints before implementation. Validate exact identities, prices, stops, targets,
exit times, P&L, R and excursions against local references, not hard-coded answers.
Future extraction of the minute executor requires a separate equivalence change.

Public strategy API: declared typed inputs plus on_bar(context, parameters) returning
an entry request or None. Frozen context contains confirmed current/prior candles,
optional causally available feature objects, and no full future DataFrame. Feature
providers are separate from the execution loop. Version 1 supports MNQ/5m, full XNYS
sessions and one entry per NY date. Other instruments, management and intraday multiple
positions require explicitly versioned engine extensions, not silently relaxed defaults.

Backend: FastAPI/Pydantic, SQLAlchemy/SQLite, immutable source versions and run configs.
Each validation/backtest executes in a separate timeout-controlled process; this is
failure isolation, NOT a Python security sandbox. Only trusted local code is supported.
Local workers do not load .env. No paid-data downloader is imported by startup.
Run IDs own immutable artifact directories; mutable status and immutable configuration
are distinct. SQLite stores metadata, artifact references and metrics, not market data.

Frontend: React/TypeScript/Vite, local Monaco assets, reusable tables/charts and generated
input controls. API calls submit jobs and retrieve results; there are no per-bar HTTP calls.
Default bind is 127.0.0.1. No public deployment/authentication in v1.

## Data and assumptions
Raw: outputs/data/GLBX.MDP3_MNQ.v.0_ohlcv-1m_2024-01-01_2026-10-06.parquet.
Bars/FVGs/lifecycle: outputs/data/MNQ_{5m,FVGs,FVG_LIFECYCLE}_2024-01-01_2026-10-06.parquet.
Integers scaled by 1e9 -> Decimal; UTC bar STARTs; NY timezone preserved.
Missing bars are not synthesized. FVG observable at Candle 3 close; post-bars exact +5/+10.
Entry confirmed close; execution starts with minute beginning at entry. Stop-first if both
levels hit; adverse stop gaps use worse open; no favorable target improvement. Exit times
label minute-end confirmation. Full exit-minute extrema included in MFE/MAE. Session
close at 15:59 close after stop/target checks. Missing owned minutes fail the run.

## Tests / change gates
Existing tests: 19 bar, 23 FVG, 37 lifecycle, 36 CONT-A, 22 risk variant, 19 time variant.
Add SDK/context validation, exact full-data golden regression, persistence/versioning,
worker failure/timeout/cancellation, API, frontend workflows and browser smoke coverage.
Reference trade files stay ignored; committed golden manifests contain only counts,
aggregate metrics and canonical SHA-256 fingerprints. Local full-data regression fails
clearly when reference files/data are absent, or is explicitly skipped in portable CI.

## Planned milestones
0 audit + golden manifest; 1 adapter + generic strategy API; 2 persistence + worker API;
3 frontend/editor; 4 results/trades/comparison; 5 sweeps/research/data; 6 tests/docs.
Management callbacks will request stop updates with effective timestamps; execution must
validate activation on a future event. Management is intentionally unsupported until a
separate timing specification and regression suite exist. Candle chart overlays and
multi-parameter sweeps can follow the core stable workflow.
