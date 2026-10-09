# Opening fifteen-minute low: upward clearance-and-hold v1

Status: DEVELOPMENT_ONLY_NOT_VALIDATED. This candidate was selected after inspecting Development diagnostics; this sequential replay is not independent validation. Frozen before the sequential result.

## Signal and the one controlled change

Reuse the immutable level-combination study's O15L / UP / WAIT_CLEAR_HOLD signals, rederive their causal waiting sequence against original five-minute bars, and reconcile all 280 confirmation signals, including the one at session close. The previous 279 executable independent diagnostics remain the reference, never a future-outcome eligibility filter.

O15L is the wick low of the complete 09:30–09:45 New York opening candle, available at 09:45. A confirmed upward root break is the existing BREAK_CLOSE signal. At its close, identify OTHER already-known daily levels strictly above that raw close and within one causal ATR14; freeze them and their farthest price. Require a later complete five-minute close strictly above that farthest price, followed immediately by a complete candle whose LOW is strictly above it. Enter at the second candle's confirmed close. Root-level reclaim/equality, incomplete/missing adjacency or session end cancels pending confirmation. Failed full holds may start another clearance attempt exactly as the existing frozen detector permits. No hindsight level selection or later level additions.

The ONLY change versus independent diagnostics is chronological selection with one open position total. Signals continue to be detected while occupied. A confirmation while occupied is logged POSITION_OPEN and discarded, not queued. A confirmation at or after the prior exit timestamp may enter; a root may have formed while occupied if its new confirmation arrives after the position closes. Ties resolve by stable signal ID. No daily trade limit. No pyramiding or concurrent trades.

## Unchanged economics and calendar

LONG only; one MNQ micro, $2 per point, 0.25 tick. Entry is confirmation close plus adverse entry slippage. Stop remains the ORIGINAL root break candle LOW minus exactly one tick, NOT the clearance or hold candle low. Target is fixed original 1R above executed entry with validated tick rounding. No management, trailing stop, partial exit, stop-size filter or time filter.

Primary: 1 adverse tick entry and exit; actual all-in fee $0.73 per side ($0.25 commission, $0.35 exchange, $0.12 clearing, $0.01 NFA). Sensitivity: 0 and 2 adverse ticks, same fees and same raw signals; position selection is replayed separately. No other targets tested.

Research profile research_2020_2026; Development 2020-01-01 inclusive through 2024-01-01 exclusive. Preserve the source study's actual XNYS RTH calendar INCLUDING early closes; no holiday session or overnight holding. Do not add the half-day exclusion used by a different earlier opening-range strategy. Close remaining positions at actual session close. At-close confirmations are audited as AT_SESSION_CLOSE. Nonpositive risk is rejected explicitly.

Native 1-minute engine handles fills starting at confirmation (the completed signal candle cannot fill its own new bracket), conservative stop-first ambiguity, adverse gaps and strict missing owned minutes. An unresolved owned minute is EXECUTION_DATA_UNAVAILABLE; no synthetic fill. Any such unresolved position blocks the rest of its session and prevents an unqualified performance conclusion.

## Verification and reporting

Require exact 280 raw / 279 executable source reconciliation BEFORE sequential P&L interpretation, exact initial brackets/fills versus the previous independent diagnostics for every selected event, no overlapping positions, no change to raw signals between cost scenarios, and byte-identical economic outputs on full rerun. Inspect the first selected entry of each Development year plus the maximum-risk selected entry on charts, using the frozen known-level identities and confirmation sequence (outcome selection of the largest risk is diagnostic only and changes no rule).

Report primary and 0/2-tick results, skipped signals, yearly/monthly performance, equity and drawdown, risk distribution/concentration, fee sensitivity and comparison to the old independent diagnostic subset. Confidence intervals for mean net R cluster by NY date, 5,000 bootstrap resamples, seed 1729; descriptive post-selection intervals, not an independent confirmation or a new optimization family. Time-of-day tables, if shown, are descriptive only.

No Validation/OOS outcome queries, source mutations, database resets, new paid data, production execution changes or threshold optimization. Persist separate local artifacts and expose every selected primary trade in a read-only Lab report/chart view. Existing studies and saved runs stay unchanged. Repository standing commit/push workflow applies.
