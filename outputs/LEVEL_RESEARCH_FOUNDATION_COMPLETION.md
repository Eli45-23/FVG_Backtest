# Level Research Foundation — completion report

Starting commit: `65af9b06c1b66600e170a7ac882f39e8058525fc`.
All work is local. No push, data download, parameter optimization or strategy recommendation.

## Architecture and preservation

A separate research subsystem now sits alongside the unchanged v1.1 trading engine:

- `engine/research/profiles.py`: additive legacy_2024_2026 and research_2020_2026 profiles,
  independent research date validation, source row counts and SHA-256 identities.
- `levels.py`, `provider.py`: sequential causal levels, strategy-compatible read-only provider,
  explicit session configuration and generic immutable Zone structure.
- `events.py`: chronological interaction detector with no forward-labeler dependency.
- `outcomes.py`: separate 1-minute forward labeling, with coverage-based censoring.
- `analysis.py`, `study.py`: matched baseline comparisons and deterministic orchestration.
- `backend/app/event_studies.py`, `event_worker.py`: isolated background studies, immutable
  configuration, reveal gates, exports, chart queries and cancellation.
- `frontend/src/EventStudies.tsx`: new workspace with settings, filters, outcome/baseline
  tables, distributions, grouped results, exports and candle inspection.

Existing engine/data.py, engine/runner.py, engine/managed.py, strategy SDK implementation,
legacy outputs runners and old reports were not changed. Existing strategy date ranges,
execution semantics, management timing, daily locks and golden fixtures remain intact.

The old strategy callback schedule omits premarket and the final RTH candle. Rather than
changing it, CausalLevelSource advances private source bars only through the requested
confirmed timestamp. It can therefore construct complete prior-session/premarket levels
for ordinary strategy code. Event Studies uses the same underlying sequential level engine.

## Datasets

| Profile | 1-minute rows | 5-minute bars | Declared date bounds |
|---|---:|---:|---|
| legacy_2024_2026 | 977,725 | 195,546 | [2024-01-01, 2026-10-06) |
| research_2020_2026 | 2,388,306 | 477,855 | [2020-01-01, 2026-10-06) |

Both profile file identities were checked again at completion and were unchanged. The
supplied new files are read-only inputs; the implementation did not rebuild them. Legacy
runs continue referring to their original data identities. Every study freezes its selected
profile, file hashes, row counts, research code version and exact exchange schedule/hash.

## Causal definitions

PDH/PDL require every complete five-minute slot in the immediately prior XNYS session.
Actual half-days are supported; holidays have no RTH observations. Missing/incomplete prior
sessions do not fall back silently to stale levels. O5H/O5L are available at 09:35, never
within their own 09:30 source candle. PMH/PML freeze after a complete explicitly configured
premarket window. **Premarket remains disabled by default; no window was guessed.**

Level metadata includes type, price, trading/source dates, availability, active state and
construction configuration. Zone supports bounds, formation/availability, timeframe and
active/invalidated state; no supply/demand detector has been invented.

TOUCH is a new contact episode; consecutive straddling candles remain one touch. SWEEP_RECLAIM,
BREAK_ACCEPTANCE, RETEST and configurable REJECTION are mechanically documented. Classes may
overlap on a single level/candle observation. Touch counts are per level/date and are not
limited to one event per day. Context includes approach side, candle properties, confirmed
time, nearest other levels, directional room, causal ATR14 and known opening/premarket ranges.

Outcome reference is confirmed event close. Labels cover 5/10/15/30/60 minutes and actual
session close using subsequent 1-minute bars. They include close change, high/low excursions,
directional MFE/MAE, ±10/25/50/75/100-point hits and first-hit minute-close timing. Missing
minutes, invalid OHLC or a horizon past session close produce censored outcomes, not fills.
Continuation and rejection views reverse directional excursion interpretation.

Baseline observations are all ordinary complete confirmed RTH candles in the selected study,
matched by year, half-hour confirmation time and causal ATR14 bucket. Fixed buckets are <10,
[10,25), [25,50), >=50 and unavailable. Results show event probability, matched baseline and
difference, plus mean directional excursion comparisons. No boundaries were optimized.

## Migration and saved state

Migration **4** adds event_studies and event_study_reveals with immutable config/reveal
triggers. No prior table is replaced or reset. Both copied-database migration tests and live
record comparisons passed. Pre-task records preserved exactly:

- 8 strategies and 17 source versions.
- 4 variants and 15 runs.
- 14 saved metric records and 81 artifact references.
- Existing sweep/experiment tables and contents.

The previous schema-version assertion was updated from 3 to 4; all old-row preservation
checks remain. The pre-migration online backup is ignored at work/levels-before.db.
New study artifacts are ignored under storage/event_studies/<id>/ and created without
replacement. A two-day Development verification study is saved locally as
`ce6e7f7400b34e8aa0c785f931088c0d`. No live OOS research study was revealed.

## OOS controls

Development: [2020-01-01, 2024-01-01).
Validation: [2024-01-01, 2025-01-01).
OOS: [2025-01-01, 2026-10-06).

Cross-segment requests are rejected. Configurations are frozen at creation. OOS initially
saves detection metadata only: outcome and baseline labels are not computed. Summary/export
requests are blocked and event charts end at confirmation. Explicit reveal appends an
immutable timestamp/config-hash record, then queues labels. Reveal cannot be undone.
Existing v1.1 experiment protections remain untouched. Reveal tests use isolated test storage;
no OOS predictive conclusion was used for implementation or hypothesis selection.

## New APIs and UI workflow

All new endpoints use `/api/level-research`:

- `/profiles`
- `/studies` (create/list) and `/studies/{id}` (status/config)
- `/studies/{id}/cancel` and `/studies/{id}/reveal`
- `/studies/{id}/events` (filtered, paginated)
- `/studies/{id}/summary` (horizon and directional interpretation)
- `/studies/{id}/export?format=json|csv`
- `/studies/{id}/events/{event_id}/chart`

Open Event Studies, select dataset/segment and exclusive date range, choose an explicit PM
window if wanted, then Create Event Study. Jobs run in a separate process with a one-hour cap
and cancellation. Select a saved study; filter level/class/direction/touch/time/year/weekday,
choose horizon and continuation/rejection view, inspect baseline comparisons and click an
event for source candles. OOS requires a separate confirmed reveal action. Restarted unfinished
jobs fail clearly rather than silently rerunning. Historical artifacts remain available.

## Verification

**341 tests passed**, compared with the v1.1 baseline of 285: 56 added.

| Suite | Passing |
|---|---:|
| Legacy unittest suite | 156 |
| Python platform/backend | 165 |
| Frontend component tests | 14 |
| Browser end-to-end workflows | 6 |
| Total | 341 |

New Python coverage includes 39 causal/profile/outcome/provider tests and 13 study/API tests.
They cover lookahead, PM confirmation, O5 availability, DST, holidays, half-days, incomplete
and missing bars, touch counts, sweeps/breaks/retests, forward labels, volatility matching,
immutable identities, OOS hiding/reveal, deterministic artifacts, migration and worker failure.
New frontend tests cover explicit PM configuration, segment boundaries and sealed OOS.
The new browser workflow creates a development study, displays results, filters events,
opens a candlestick chart and checks export availability. All five prior browser flows pass.

The first repeated browser run encountered duplicate named fixtures in reused test storage;
the final full run used fresh separate storage and all six passed. User storage was never
cleared to fix tests. Production frontend build passes. Nonblocking existing warnings remain:
large Monaco bundle and a TestClient dependency deprecation.

All three legacy golden strategies reproduce exact trade fingerprints and metrics, not only
rounded headlines:

| Reference | Trades | Net USD | PF | Average R | Max DD |
|---|---:|---:|---:|---:|---:|
| CONT-A baseline | 263 | $525.50 | 1.023713 | 0.104721 | $2,488 |
| Max risk <100 | 235 | $4,277 | 1.285466 | 0.155332 | $1,725 |
| Risk <100 + time exclusion | 170 | $4,242 | 1.416270 | 0.234810 | $1,570 |

Exact hashes:
- Baseline: a57bb17e3a401175fb7ed5b6328e4f66cec85cb5ee5a25ca806e4cf6e6992d8d
- Risk100: 3d3fc6c748e79bcab58f5913f992c42cc7edfed186829b1b3d5928ffa47daf9f
- Quality: 4719fc4e1b0ff00b63de7cf1aa4ff471eb4554b00037cf10625e5fe77420bf6d

All prior management and determinism tests pass. Source/market-data files remain ignored;
no credentials were read, modified or committed. Relevant logs are retained under ignored work/.

## Launch and limitations

```sh
./scripts/install.sh  # only if dependencies are not installed
./run_app.sh
```

Application: http://127.0.0.1:5173. API docs: http://127.0.0.1:8000/docs.
Both verified listeners bind only localhost. The app is running at completion.

This release measures RTH interactions, not all overnight interactions. The earliest source
date can lack a prior-session level. PM requires an explicit user choice. Rejection is a
mechanical proxy and event classes overlap; results are descriptive, not independent trials
or statistical significance claims. Zone detection remains pending a frozen definition.

Study JSON and aggregate queries use memory; multi-year throughput has not been benchmarked.
A columnar/query-backed artifact store is the next scaling improvement. The entire 2020–2026
file set is available, but this task did not run or interpret a full-history predictive study.
OOS protection is a local research workflow, not protection against arbitrary code or a user
reading raw files. Legacy strategy execution remains on its original data/date profile.

Unrelated untracked user scripts remain untouched. All task files are committed locally;
this does not make the overall workspace empty. Nothing was pushed.

## Local commits

1. `96f827e52ea3cfcbc7c632175bf745e598d212f8` — causal profiles, levels, events and labels.
2. `8f468fb46aa94ab1f5cc0342a76048e83e3bbdef` — persistence, workers and audited reveal.
3. `21435aab57c1fbbd2de6c3c9914cc2ce8013c940` — Event Studies interface and browser workflow.
4. Final provider/documentation commit: its hash is in the delivery message and Git log.

See docs/LEVEL_RESEARCH_FOUNDATION.md for the complete frozen measurement contract and SDK examples.
