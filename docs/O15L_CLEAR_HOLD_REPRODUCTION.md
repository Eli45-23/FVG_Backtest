# Sequential O15L clearance-and-hold Development test

## Reproduce

The frozen rules are in `O15L_CLEAR_HOLD_SEQUENTIAL_V1.md`; the exact protocol is `O15L_CLEAR_HOLD_PROTOCOL.json`. The latter hashes the former. Do not edit either after viewing results. This candidate was selected after prior Development research and has not been validated.

Prerequisites: the existing local eight-level study, completed level-combination study and validated research-profile market data. Their identities are checked before reuse. No download or normal database write is performed.

On a machine without this result directory, create `work/o15l-clear-hold-sequential-v1/` and copy the protocol JSON there as `protocol.json`. Do not replace an existing study with different rules. From the repository root:

```sh
work/.venv/bin/python scripts/o15l_clear_hold/run.py
work/.venv/bin/python scripts/o15l_clear_hold/report.py
work/.venv/bin/python scripts/o15l_clear_hold/audit.py
work/.venv/bin/python scripts/o15l_clear_hold/verify.py
```

Verification repeats the complete native execution, reports and candle audit and requires byte-identical outputs. All market-data reads are bounded to New York 2020-01-01 inclusive through 2024-01-01 exclusive. Whole-file hashing verifies preservation without decoding reserved-year outcomes.

## Inspect

Start the Lab with `./run_app.sh`. In Research, open **O15L upward clearance-and-hold · 1R**. Direct local URL:

`http://127.0.0.1:5173/api/research/o15l-clear-hold/files/study.html`

The page provides all 273 primary trades with year/time/outcome display filters, pagination, individual charts and exports. Filters only change displayed records; they do not rerun the strategy. Charts mark the opening range, frozen obstacle barrier, root break confirmation, clearance confirmation, hold/entry, original stop, fixed target and exit. Markers for root/clearance are anchored to the crossed level rather than the candle close. Candles after entry are retrospective inspection only. This result is a read-only research artifact, not a newly saved normal Lab strategy/run record.

The endpoint exposes only manifest-listed, hash-verified Development artifacts. Chart queries read only the generated Development chart file, never the full market master. Existing research endpoints remain unchanged.

## Verification completed

- 280 causal confirmations reproduced; 279 previous executable events reconciled before sequential simulation.
- 273 trades per cost scenario; six position-open skips and one at-close confirmation. Selected IDs are identical across all three cost scenarios.
- 819 native fills checked independently per full replay and matched to previous independent diagnostics: entry, original stop, target, risk, exit, net P&L, R, duration and excursions.
- 27 generated artifacts byte-identical on full repeat, including CSVs, chart Parquet, JSON, Markdown and HTML. Deterministic ZIP uses fixed member timestamps.
- Five deterministic chart samples: first trade in each Development year and maximum-risk trade. Candle completeness, root/clearance/hold timing, availability and exact brackets pass. All five rendered charts inspected in browser.
- 56 targeted Python tests passed, including causal waiting, selection timing, prior execution tests and old/new report API protections.
- Six frontend report tests passed. One isolated end-to-end workflow passed with other APIs mocked: open results, filter and clear, render all five charts, download CSV/JSON/ZIP.
- Production frontend build passed. Existing bundle-size and Starlette dependency warnings remain nonblocking.
- Market-data/reused artifact hashes verified unchanged. Saved strategy/run/study/reveal metadata remained identical to the previous snapshot (`7788ad66dc95225bc66971d478edce3a74069af91b6b705f02779ce88e553300`).

No production execution code changed. Full-history legacy golden reruns were not invoked because they access reserved-year outcomes; exact prior Development fill reconciliation and relevant synthetic tests were used instead. No Validation/OOS outcome access, reveal, new paid data or threshold optimization. Generated trades, chart bars, databases and ZIP remain ignored; only code, tests, frozen protocol, documentation and aggregate report enter Git. Pre-existing `.DS_Store` is left alone.
