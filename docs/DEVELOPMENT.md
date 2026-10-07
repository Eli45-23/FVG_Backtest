# Install, run, test and extend

Requirements: Python 3.13 (the validated environment), Node 22+ and npm. The current
workspace already has the ignored outputs/data/ Parquet files and local reference results.
A fresh Git clone does not contain market data: restore your authorized local data separately.
The application never downloads paid Databento data on startup and never needs .env.

```sh
./scripts/install.sh
./run_app.sh
```

Open http://127.0.0.1:5173. API/OpenAPI: http://127.0.0.1:8000/docs.
Both bind only 127.0.0.1. Ctrl+C stops both services. LAB_PYTHON overrides the Python
executable; LAB_STORAGE overrides SQLite/artifact storage for isolated testing.

Equivalent installs:
```sh
python3 -m venv work/.venv
work/.venv/bin/python -m pip install -r backend/requirements.txt
cd frontend && npm ci
```

## Tests
```sh
work/.venv/bin/python -m unittest discover -s outputs/tests -v
work/.venv/bin/python -m pytest tests backend/tests -q
cd frontend
npm run test
npm run build
npx playwright install chromium
# With the app running, preferably LAB_STORAGE="$PWD/work/browser-test-storage" ./run_app.sh:
npm run e2e
```

Full-data golden tests explicitly skip when the ignored MNQ bundle is unavailable.
Backend integration tests use temporary SQLite storage, real local data and isolated workers.
Browser tests create strategies/runs in the running instance: use a dedicated LAB_STORAGE
for a clean smoke-test workspace. They test clone, inputs, validation, run, results, trades,
history, compare, sweep, and new non-FVG Python source without backend modification.

Frontend source can be formatted with `npx prettier --write src tests`. Python is formatted
with Black. Existing outputs/ code is deliberately excluded from formatting/refactoring.

## Structure and persistence
- engine/: stable public strategy SDK, causal providers, legacy compatibility adapter.
- strategies/builtins/: one CONT-A source plus an ordinary-bar New Strategy template.
- backend/app/: FastAPI schemas/endpoints, SQLAlchemy models/migrations, worker services.
- frontend/src/: React application, local Monaco, reusable inputs/tables/charts, API types.
- storage/app.db: strategies, strategy_versions, variants, runs, run_metrics, run_artifacts,
  sweeps, sweep_runs, schema_migrations. WAL and foreign keys enabled. Ignored.
- storage/artifacts/<run_id>/: immutable source request/config snapshot, economic result,
  standardized trade records and equity JSON; bounded worker log and stage progress.
- storage/events.jsonl: structured state transitions with run_id; no source/parameters/secrets.
- outputs/: all existing validated scripts, tests, data and reports remain available.

Trade JSON is chosen because v1 permits one trade per date (hundreds of trades); decimal
prices are exact strings and timestamps ISO timezone-aware. Artifacts are referenced by
SQLite and never overwritten across run IDs. Scale to Parquet/paginated storage when
multi-entry/instrument support materially increases record counts. Back up storage/ plus
outputs/data/ and outputs/results/ together; none belongs in Git.

Migrations are additive and versioned in db.migrate(). Version 1 creates tables; version 2
adds source-version uniqueness. Do not replace/create a fresh DB to resolve migration errors.
Source saves append versions when the hash changes; renaming does not duplicate source.
Deletion archives a strategy; historical versions/runs remain accessible.

## Worker lifecycle
One server-side executor queues subprocesses sequentially to bound memory. Each process
loads read-only Parquet once, computes all events server-side, and writes result artifacts.
No per-bar HTTP. Validation timeout 10 seconds; backtest timeout 600 seconds. Stdout/stderr
are capped to 64 KiB per stream. Main service keeps running after syntax errors, crashes and
hangs; Cancel kills the process group. Restart marks unfinished persisted runs failed with a
clear reason. Current startup does not automatically rerun interrupted jobs.

This is a trusted-local-user tool, not a sandbox. No auth, public bind, deployment or remote
execution is supported. Host/origin checks reduce accidental cross-origin requests. Workers
inherit a minimal environment, not Databento credentials. They can still deliberately read
files because they execute trusted Python as your account. Never run untrusted source.

## Extend safely
Add causal data features separately from execution; supply frozen context data known at
confirmation. New strategy ideas require only source using the existing SDK. New instruments,
position management, intraday multiple trades or execution policies require new profile/schema
versions, explicit timing docs, synthetic tests and exact golden checks before release.
Do not mutate CONT-A fixtures to hide regressions. Preserve old runners for independent checks.

## Troubleshooting
- Port occupied: stop the existing local app; do not change binding to 0.0.0.0.
- Missing modules: run install.sh with the same Python used to start the app.
- Missing Parquet: restore local authorized files at the Data page's documented names.
- Syntax/input errors: Validate, read line markers, fix/save, rerun.
- Missing execution minute: inspect data; the engine intentionally fails rather than fill gaps.
- Failed/hung run: inspect local worker log, cancel, and fix the strategy. No stack trace is
  shown in normal error banners; detailed trace is available only in the explicit log viewer.
- Wrong date: dates are NY calendar dates, end exclusive; last coverage is partial.
- No signals: zero-trade runs complete normally. Check rule, date range and full sessions.
- Monaco first load: assets are local; the production bundle is large (~1 MB gzipped main
  chunk). No CDN is needed; later code splitting is a performance improvement, not a fill change.

## Remaining scope
Phase-2 financial candlestick overlays are prepared through
GET /api/backtests/{id}/candles/{trade_id} (bars, trade levels and FVG metadata).
The frontend currently provides equity/statistical charts, not candle/FVG annotations.
Management hooks are intentionally reserved/rejected. Multi-parameter sweeps, walk-forward
execution, enforced data splits, multi-instrument profiles, filesystem strategy import/export,
and shared-user authentication are not implemented. Research UI previews 100 rows; the API
supports pagination. Strategy-version history is available through the API; the editor opens
the current version and its variants. All source snapshots remain immutable and recoverable.
