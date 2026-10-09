# Opening-range breakout: reproduce and inspect

This frozen Development-only backtest is available in Lab → Research → Opening 15-minute breakout · 50 points. It uses the production minute executor directly, with sequential one-position selection; it does not add a strategy to the saved-strategy database or mutate historical runs. The standalone audit results and full trade list are immutable once verified and are exposed through a read-only, hash-checked route.

Local URL: http://127.0.0.1:5173/api/research/opening15-breakout/files/study.html

The viewer includes all primary trades, filters, CSV export and a five-minute chart for any selected trade. Opening-range lines begin at 09:45, and order lines begin at entry. The chart is retrospective: it may show later Development candles for visual auditing, never for strategy eligibility. Charts query only this backtest's verified local Development artifact, not the full market-data master.

## Reproduction

Requires the existing validated local data and eight-level study identity. Preserve protocol.json from the bundle; its specification hash must match docs/OPENING15_BREAKOUT_50PT_V1.md. Do not edit the protocol underneath a historical result identity.

```sh
work/.venv/bin/python scripts/opening15_breakout/run.py
work/.venv/bin/python scripts/opening15_breakout/report.py
work/.venv/bin/python scripts/opening15_breakout/verify.py
```

Verification repeats all fills, selection, aggregates and seeded date-cluster intervals and requires exact file hashes. It also records engine/source identities and creates a deterministic aggregate ZIP. Large raw artifacts remain local and ignored, linked in the ZIP's full evidence index without sampling. Runtime metadata is separate from deterministic results. Reproduction rewrites only this generated audit directory; archive it before intentional changes.

The stateful signal detector is independently checked with a vector crossing detector. Every opening candle reconciles to its actual source minutes. Native long/short fills are independently checked, with exact target distance, costs and nonoverlapping position timestamps. The source and production executor remain unchanged.

## Checks

```sh
work/.venv/bin/python -m pytest -q tests/test_opening15_breakout.py backend/tests/test_opening15_report.py tests/test_downward_break_full_hold.py tests/test_downward_break_feasibility.py tests/test_execution_profiles.py tests/test_extended_execution.py tests/test_management.py tests/test_eight_level_study.py
cd frontend
npm test
npm run build
npx playwright test opening15-e2e.spec.ts
```

The browser workflow mocks unrelated application endpoints so that historical reserved-period outcomes are not fetched. It verifies the Lab link, time tables, trade filters, chart and CSV/JSON/ZIP downloads. No actual Validation/OOS golden backtests are run because the production executor is unchanged and those outcomes are outside this request.

Time-window statistics describe selected historical trades. Applying a time filter later requires a new sequential backtest because different entries can occupy the position. Bootstrap intervals are exploratory, not adjusted evidence supporting the best of many windows. No time filter, stop offset or target was optimized.
