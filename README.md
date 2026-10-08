# Strategy Research Lab v1.1

Local Python strategy editor and research platform over the validated MNQ execution engine.

```sh
./scripts/install.sh
./run_app.sh
```

Open **http://127.0.0.1:5173**. No cloud deployment or paid data download occurs.
Only run strategy code you trust. Python is isolated in workers, **not securely sandboxed**.

## Workflow
1. Strategies → CONT-A Second Candle. Choose Baseline, Risk <100, or Risk <100 + time exclusion.
2. Clone, rename, edit Python in Monaco, Save and Validate. Source edits create immutable versions.
3. Change generated inputs without editing source. Choose NY start/end dates (end exclusive),
   quantity, per-side/per-contract commission and slippage ticks. Add a hypothesis in run notes.
4. Save/Clone Variant to preserve inputs/settings against a source version.
5. Run Backtest. See worker stage/status, cancel if needed, then inspect results and trades.
6. Runs retains every execution/config. Select completed runs in Compare for side-by-side
   metrics, equity/drawdown overlays, grouped results and exact configurations.
7. Sweeps uses the currently opened strategy/settings: choose one numeric/choice input and
   explicit values. Each child is a saved run. No automatic best-strategy selection.
8. New Strategy provides a short ordinary-bar template. Replace the rule; validate/run without
   changing backend code. The SDK supports non-FVG strategies.
9. Data shows local sources; Research explores qualified FVG lifecycle observations without
   exposing future outcomes to strategy contexts.

## Documentation
- [Architecture and migration audit](docs/ARCHITECTURE.md)
- [Strategy API, inputs, context, entries, stops, targets and reserved management](docs/STRATEGY_API.md)
- [Execution and data assumptions](docs/BACKTEST_ASSUMPTIONS.md)
- [Installation, tests, storage, extension and troubleshooting](docs/DEVELOPMENT.md)
- Existing methodology and reports remain under [outputs](outputs/README.md).

Market data, .env, SQLite, logs and generated run artifacts stay ignored. Version 1 supports
MNQ/5m, full XNYS sessions, fixed bracket/session-close execution and one trade per NY date.
See DEVELOPMENT.md for documented limits and the next extension phase.


## v1.1
- Click any trade for the candlestick Inspector, levels, FVG and managed-stop history.
- Strategies → Versions offers read-only Monaco Diff, historical clone and append-only restore.
- CONT-A Quality R-Step demonstrates opt-in causal management without changing fixed references.
- Experiments provides saved research splits, Development/Validation, freeze and explicit OOS reveal.
- Sweeps default to Development; Validation requires an advanced override; official OOS is blocked.

Read docs/TRADE_INSPECTOR.md, docs/MANAGEMENT_API.md and docs/RESEARCH_SPLITS.md before
interpreting managed or segmented results. No claim of R-Step outperformance is made.
