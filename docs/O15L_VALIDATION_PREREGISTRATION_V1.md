# O15L clearance-and-hold: 2024 Validation preregistration

Frozen before reading 2024 bars or outcomes for this task. User authorized the unchanged setup's Validation test with “Let’s do it”. Criteria below are an explicit research decision rule chosen before outcome access, not a claim of statistical power or a live-trading risk budget.

## Identity and unchanged execution

Use the exact O15L / UP / WAIT_CLEAR_HOLD definition in O15L_CLEAR_HOLD_SEQUENTIAL_V1.md and the committed detector, context, waiting and native fill functions. No time restriction, stop management, changed target, or optimization. Long at confirmed full-hold close. Root break low minus 0.25 stop, fixed original 1R target, quantity one MNQ micro, $2 per point. One position at a time, chronological signal-ID ties, discard busy confirmations without queuing. Native session-close and missing-owned-minute rules unchanged. Actual XNYS RTH including early closes.

Validation scoring range: New York 2024-01-01 inclusive to 2025-01-01 exclusive. Only causal state warmup may use prior Development bars. No 2025+ bars/outcomes may be decoded. PM is midnight–09:30, complete coverage only. Levels become available causally. ATR is the existing 5m simple mean of 14 true ranges with existing gap resets, as used by the original v2 study.

Primary: one adverse tick each side, actual fee $0.73 per side. Zero/two tick scenarios are predeclared sensitivity reports only and cannot rescue a failing primary result. Preserve prior Development files and saved study/reveal states. This is a separate read-only research artifact, not a reveal of any existing sealed study.

## Gate, frozen before inspection

1. Integrity must pass: exact Development signal/economic reproduction of the portable detector/executor; deterministic Validation rerun; no unresolved owned execution data; no rule changes.
2. At least 30 completed trades on 30 distinct NY dates. Below either is INCONCLUSIVE_SAMPLE. This is a minimum coverage rule, not a claim that 30 observations ensure adequate power.
3. Primary net USD > 0, mean net R > 0, and net PF > 1 (positive gross net-winning sum with zero net losses is treated as infinite PF).
4. Maximum closed-trade cumulative-net-R drawdown <= 7.031524868463503R, the existing Development maximum. This deliberately asks whether the single Validation year stays within the previously observed full-Development R drawdown, not an inferred future bound.
5. Date-cluster bootstrap mean-net-R 95% percentile interval: 5,000 resamples, seed 1729, same method as Development. A lower bound > 0 is required for VALIDATION_SUPPORTS_FROZEN_HYPOTHESIS. If conditions 1–4 pass but the interval includes zero, classify CONDITIONAL_VALIDATION_EVIDENCE. If any economic condition or drawdown condition fails, classify VALIDATION_GATE_FAILED. Integrity failure overrides all results as INCONCLUSIVE_INTEGRITY.

No threshold will be changed after seeing Validation. Quarterly/monthly/yearly, concentration, costs and chart diagnostics are descriptive and cannot become new eligibility rules in this test. No automatic advance to OOS and no live-trading recommendation. Historical 2024 data have been inspected by unrelated earlier project research; describe this as held-out for this frozen candidate, not universally untouched market history.

## Reproduction and reporting

Before accessing Validation, run the portable signal construction on Development and require the exact 280 causal entries, original timestamps, levels, barriers, close/stop identity, and causal ATR agreement against the frozen prior study. Preserve the 279 executable reference and sequential 273 primary trades. Block Validation if this differs. Snapshot code/data hashes and record the preregistration commit and first access in an append-only local access ledger.

Report raw roots, obstacle opportunities, confirmations, selected/busy/at-close/nonpositive/missing-data counts; primary and sensitivity metrics; monthly and quarterly results; mean-R interval; every gate separately; max drawdown; risk concentration; complete trade CSV/JSON and chart access. Preserve source identities and user storage. No retraining or alternative parameter tests after results.
