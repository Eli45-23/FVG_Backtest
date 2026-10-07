# Strategy Research Lab — implementation and verification

The local v1 platform is implemented. The core acceptance workflow works through the
browser, including creating a new non-FVG Python strategy without editing backend code.
Nothing was pushed. Historical runners, reports and market-data files remain unchanged.

## Start here

Dependencies are installed in this workspace. From the repository root:

```sh
./run_app.sh
```

Open http://127.0.0.1:5173. API documentation: http://127.0.0.1:8000/docs.
Both services bind to 127.0.0.1. If already running, open the URL directly.
For a fresh installation use Python 3.13 and Node 22+:

```sh
./scripts/install.sh
```

Equivalent dependency commands:

```sh
python3 -m venv work/.venv
work/.venv/bin/python -m pip install -r backend/requirements.txt
cd frontend && npm ci
```

Fresh clones need the authorized local Parquet bundle restored separately. Startup does
not download data or read Databento credentials.

## Architecture and repository

```text
backend/app/        FastAPI, typed schemas, SQLite migrations, isolated worker services
backend/tests/      API, persistence, worker and integration coverage
engine/             causal providers, Strategy SDK, legacy execution adapter
strategies/builtins/ one editable CONT-A source and ordinary-bar template
frontend/src/       React/TypeScript, Monaco, generated inputs, charts and tables
frontend/tests/     component and browser workflow tests
tests/fixtures/     aggregate references and exact trade fingerprints
storage/            ignored SQLite, logs and immutable per-run artifacts
docs/               architecture, API, assumptions and development guides
scripts/install.sh  installation
run_app.sh          local launcher
outputs/            original validated code/data/reports preserved
```

The adapter imports the unchanged reference minute executor and metrics. Data loading,
causal event construction and user entry requests are separate from fills. CONT-A's
entry predicate, cutoff and variant inputs reside in strategy source. The generalized
runner supports ordinary confirmed-bar concepts without FVG-specific entry rules.

All prior data conversion, complete-bar handling, timezone rules, FVG/lifecycle logic,
opening exception, exact ownership timing, conservative ambiguity handling, tick
rounding, session close, MFE/MAE and existing command-line runners remain available.
No risky replacement of the validated executor was needed. The optional legacy ATR
research diagnostic is null in new platform trade records; it is not an eligibility rule.

## Regression evidence

| Configuration | Trades | Net USD | PF | Average R | Max closed-trade DD |
|---|---:|---:|---:|---:|---:|
| CONT-A baseline | 263 | $525.50 | 1.023713 | 0.104721 | $2,488.00 |
| CONT-A risk <100 | 235 | $4,277.00 | 1.285466 | 0.155332 | $1,725.00 |
| CONT-A risk <100, exclude 10:00–10:29 | 170 | $4,242.00 | 1.416270 | 0.234810 | $1,570.00 |

Golden tests compare exact canonical fingerprints of trade/setup IDs, direction, entry
and exit timestamps/prices, stops, targets, risk, exit reason, net P&L, R and MFE/MAE.
Every original overall metric also matches. These are engine-generated results, not
hard-coded output. All three configurations were additionally run through the live API:
the persisted trade fingerprints match and those runs are available in Run History.
Repeated nonempty risk-100 results have identical canonical output; source and prior
result Parquet hashes remain unchanged. Run IDs/timing metadata are intentionally unique.

## Backend and persistence

SQLite tables: schema_migrations, strategies, strategy_versions, variants, runs,
run_metrics, run_artifacts, sweeps and sweep_runs. Additive versioned migrations,
foreign keys and WAL are enabled. Each changed source save appends an immutable
version/hash; rename-only saves do not duplicate source. Delete archives strategies.

Runs preserve source/version, resolved inputs, dates, quantity, costs, execution/session
profile, engine/dependency identity, data hashes, segment label and reproduction hash.
Trade/equity JSON artifacts retain exact decimal strings and timezone-aware timestamps;
SQLite stores references and metrics. Run IDs prevent overwrite. JSON is practical for
hundreds of trades under the current one-trade/day profile.

API areas cover strategies, versions, validation, variants, queued backtests, cancellation,
metrics, equity, trades/export, candle context, comparison, sweeps, data and FVG research.
OpenAPI is generated automatically. Run states are queued/running/completed/failed/cancelled.
Restarted unfinished runs fail explicitly instead of silently resuming with changed code.

Trusted Python executes in a subprocess: 10-second validation timeout, 600-second backtest
timeout, process-group cancellation, bounded stdout/stderr, structured local state logs.
Only run strategy code you trust. This is failure isolation, not a secure Python sandbox.
Workers do not inherit Databento credentials or load .env; trusted code still has local
account file/network access. Host/origin checks and localhost defaults are enabled.

## Editor and strategy API

Monaco supplies Python highlighting, line numbers, folding, search and keyboard editing.
The UI provides search/library, New, Clone, rename, archive confirmation, Save, Validate,
source-change indicator, Ctrl/Cmd+S and syntax markers. Generated controls support float,
integer, boolean, string, choice, time and session inputs. Overrides create run configs,
not source edits. Validation checks hooks, features, syntax and parameter constraints.

```python
from decimal import Decimal as D
from engine.strategy import Float, Entry

class Strategy:
    name = "Morning candle experiment"
    inputs = [Float("target_r", "Target R", 2, min=.25, step=.25)]

    def on_bar(self, ctx, p):
        if ctx.bar.time == "09:45" and ctx.bar.close > ctx.bar.open:
            return Entry("LONG", ctx.bar.low - ctx.tick_size,
                         D(str(p["target_r"])))
        return None
```

The immutable context contains confirmed candles and a bounded causal history, not future
bars/lifecycle outcomes. Entry requests specify direction, stop, target R, optional exclusive
max-risk bound and metadata. The engine owns fills, daily locks, costs and statistics.
The FVG-second provider adds the confirmed setup and two post-FVG candles. A reserved
StopUpdate contract documents future activation requests; management callbacks are currently
rejected explicitly until event timing is separately validated.

## Research workflow and interface

1. Open CONT-A in Strategies and select one of its three presets.
2. Clone/rename, edit code or generated input controls; save and validate.
3. Select NY calendar dates (end exclusive), quantity, costs, notes and research segment.
4. Save/Clone Variant to retain parameters/settings against a source version.
5. Run Backtest; observe stage/status, cancel if needed, inspect the results.
6. Runs automatically retains every config/version and result; clone a run configuration.
7. Compare completed runs: side-by-side metrics, absolute equity/drawdown overlays,
   yearly/monthly/direction/time/weekday/risk/excursion groups and exact config differences.
   Different settings, data, engine or research segments produce visible warnings.
8. Sweeps: choose a numeric/choice input and up to 20 explicit values. Each child is saved;
   the definition retains child IDs. Results are sortable; no automatic best selection.

Results include KPI cards, all standard metrics, equity/drawdown, monthly/yearly,
direction, trigger time, weekday, risk buckets, R distribution, MFE/MAE and duration.
Undefined metrics are null. Trade Explorer includes entry/stop/target/exit, risk, P&L/R,
excursions and duration, with date/time/direction/outcome/year/month/weekday/risk/exit filters
and CSV export for the selected run.

Research provides qualified lifecycle summaries and filters for direction, formation date/time,
size, touch/fill/invalidation and opening exception. The Data page lists the four local sources,
coverage, counts and status. Neither route downloads data or exposes credentials.

## Tests and checks

| Suite | Result |
|---|---:|
| Original unittest suite | 156 passed |
| SDK/context tests | 23 passed |
| Full-data golden/determinism/protection tests | 4 passed |
| Backend/API/worker integration tests | 17 passed |
| Frontend component tests | 5 passed |
| Browser end-to-end workflows | 2 passed |
| Total | 207 passed |

Production frontend build passes. Browser tests cover clone/input/run/results/trades/history/
compare/sweep and a newly written non-FVG strategy producing two trades without backend edits.
Screenshots were inspected. Git diff checks pass; original outputs sources/reports have no diff.
Data/results/SQLite/.env remain ignored. Tracked-file checks found no market-data or credential
files and no matching credential patterns. Live ports bind only 127.0.0.1.

Non-failing warnings: the frontend's Monaco bundle is large; TestClient reports an upstream
httpx deprecation. Both are documented, neither changes execution semantics.

## Limits and next phase

V1 deliberately supports MNQ/5m, full XNYS sessions, one daily entry and fixed bracket/session
close execution. No trailing/partial management or additional instrument profiles yet.
Candle-context API is implemented; candlestick/FVG overlays remain a UI follow-up. Research
UI previews 100 rows; API pagination is available. Version history is accessible through API;
the editor opens current source. Segment labels persist but do not enforce out-of-sample
separation or run walk-forward tests. Multi-parameter grids and filesystem import/export are
future work. Pure source must avoid external I/O, randomness or wall-clock dependencies for
reproducibility; arbitrary trusted Python cannot be guaranteed deterministic by isolation alone.

Recommended next phase: candle-level trade inspection and source-version browsing, followed
by separately specified/tested execution management. Add new instruments only through a
versioned profile and fresh equivalence tests. Existing CLI references should remain intact.

## Documentation and commits

See ../docs/ARCHITECTURE.md, ../docs/STRATEGY_API.md,
../docs/BACKTEST_ASSUMPTIONS.md and ../docs/DEVELOPMENT.md.

Milestone commits before this completion/documentation commit:
- c505dc2 — architecture audit and reference fingerprints
- 73433ce — causal SDK and exact execution adapter
- 56b369f — persistence, workers and backend API
- c7ec98c — editor, results, comparisons and sweeps frontend

The final documentation/polish commit hash is included in the task's completion response.
No commits were pushed.
