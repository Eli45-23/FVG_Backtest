# Frozen PDH Development fee rerun

This workflow reruns immutable Lab source version `a3dc35456fd7416abfa0df53f77fbb6e` (PDH Failed Break Short v1) through the normal worker. It changes only the actual user-supplied all-in fee to **$0.73 per side per MNQ micro**: commission $0.25, exchange $0.35, clearing $0.12, NFA $0.01. Exactly three scenarios use zero, one and two adverse ticks on both entry and exit. One tick is primary. Quantity remains one and target remains original 1R.

Status remains `DEVELOPMENT_ONLY_NOT_VALIDATED`. The allowed New York date interval is `[2020-01-01,2024-01-01)`, using `research_2020_2026`. Do not use this workflow to run Validation/OOS or optimize parameters.

## Local prerequisites

The normal Lab SQLite store, the immutable source version, the original Development audit under `work/pdh-failed-break-short-v1-development/`, candidate audit and local research Parquet files must already exist. No download occurs. The source version must match the prior saved source exactly. The original audited reconciliation script is reused with its source bound to the immutable database version and all output redirected to the new directory.

## Commands

From the repository root:

```sh
work/.venv/bin/python scripts/pdh_fee_corrected_development.py run
work/.venv/bin/python scripts/pdh_fee_corrected_development.py repeat
work/.venv/bin/python scripts/pdh_fee_corrected_development.py report
work/.venv/bin/python -m pytest tests/test_pdh_fee_diagnostics.py -q
```

`run` performs exact causal candidate preflight before enqueueing three normal Lab runs. It writes `lab_runs.json` after each enqueue and resumes those IDs on subsequent calls. It does not create another strategy version or modify older runs. If interrupted between database enqueue and journal write, inspect saved run names/configurations before restarting; do not blindly create duplicate runs.

`repeat` invokes three sequential, fresh normal worker processes without adding database runs and requires byte-identical complete result JSON. `report` refuses to interpret results unless reconciliation, repeats and same-slippage old-fill equivalence pass. It checks 67 candidates, 58 dates, 58 trades, nine later daily rejections, precise structural stops/1R brackets and fee accounting. The earlier Development artifacts are hashed and checked unchanged.

Outputs are local under `work/pdh-failed-break-short-v1-fee-corrected/`, including full trade CSVs, scenario/yearly metrics, fee economics, risk concentration, drawdown intervals, readiness and a reproducibility manifest. Normal immutable run artifacts remain under `storage/artifacts/<run_id>/`. Neither directory is committed.

## Measurement conventions

Net R divides each trade's net dollars by its own original executed risk dollars. The fee never changes eligibility. Break-even fee per side is total pre-fee P&L divided by twice the number of completed one-micro trades. Fee share of gross profit is explicitly labeled as aggregate pre-fee P&L versus the sum of positive trades. Closed-trade USD/R drawdown starts from zero; yearly drawdown restarts within each year. Top-five-risk drawdown contribution is signed P&L attribution within the actual peak-to-trough interval, not a filtered simulation.

Use only scoped synthetic checks for this task. A broad historical suite may read reserved periods even in an isolated test database. Production code is not changed by this workflow. The fixed prospective Validation ceiling remains 6.2788R; it must not be recalibrated after seeing fee-corrected results. Validation requires separate authorization.
