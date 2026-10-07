# Backtest/data contract

The reference outputs/ files remain authoritative and unmodified. The adapter reuses
cont_a_backtest.execute, tick rounding, calendar and metrics. See existing BAR_LAYER,
FVG_LAYER, LIFECYCLE_LAYER and CONT-A reports for the full historical record.

- MNQ.v.0 continuous futures, GLBX.MDP3; no split/back adjustment or roll repair.
- Raw OHLC are int64 scaled 1e9. Convert exactly to Decimal. Executable MNQ tick is .25;
  point value is $2 per micro. Quantity scales dollars/commissions, not per-contract points/R.
- UTC timestamps represent bar START. Five-minute buckets are clock-aligned, not rolling.
- No synthetic missing candles. Incomplete bars cannot create confirmed strategy events;
  missing owned execution minutes fail the run, not silently skip a trade.
- NY dates are calendar dates, not CME custom session dates. UI start is inclusive, end
  exclusive by entry's NY date. Warmup/context can precede start; no entry can precede it.
- Available request coverage is 2024-01-01 UTC inclusive to 2026-10-06 UTC exclusive.
  The last NY date is partial; the data page shows actual first/last source observations.
- Version 1 is MNQ/5m, full XNYS sessions only, one actual entry per NY date. The calendar
  is the pinned exchange_calendars 4.13.2 schedule; no web query occurs during runs.
- Entry fills at confirmed 5m close. The 1m bar starting at entry is owned; the preceding
  signal minute cannot hit stops or targets before entry.
- Original fixed stop and target only. Long low<=stop / high>=target; mirrored short.
- Both levels in one minute: STOP first. Adverse gaps fill at worse of stop/open; targets
  fill at the target without favorable improvement. Slippage is adverse on entry and exit.
- Commission input is USD per side per contract. Quantity multiplies dollar amounts;
  the baseline defaults remain quantity=1, commission=0, slippage=0.
- Stops/targets stay active through 15:59–16:00. If neither hits, session-close exit uses
  15:59 close. Exit labels are minute-end confirmation, not exact intraminute execution time.
- MFE/MAE include full owned-minute extrema including exit minute. Order of extrema in
  that minute is unknown; these are OHLC bounds, not guaranteed realizable pre-fill paths.
- Closed-trade equity starts at zero, not an invented account balance. Drawdown/run-up are
  dollar measures, not percentage account returns. No Sharpe/annualized return is invented.
- Null PF means undefined/no losses; inspect profit_factor_status to distinguish cases.
  Empty runs are valid and report zero trades with null averages/rates, not fabricated trades.
- R normalizes net outcome by each original risk. Positive mean R and negative dollars can
  coexist when larger-risk losses dominate. Different date/data/engine configs are flagged.
- Segment labels (development/validation/out-of-sample) are saved labels. They do not
  enforce untouched test sets or prevent repeated inspection. No automatic winner selection.

## Compatibility detail
Golden tests compare exact trade identities, entry/exit timestamps and prices, stops,
targets, risk, P&L, R and MFE/MAE plus all original overall metrics. The adapter uses the
reference decimal128(24,9) serialization. It adds metadata and generic metrics. Legacy
optional descriptive ATR is not recomputed by SDK v1 (nullable, never an entry condition).
The old runner/logs containing that research field are retained. Standard run artifacts add
run/source/version IDs without changing economic trade identity or historical files.

## Determinism boundary
Pure source + validated parameters + settings + source data hashes + engine/dependency
identity reproduce the same economic result. Run IDs/timestamps are intentionally different
for each saved execution. Core result JSON is stable; identity-enriched artifacts necessarily
contain their own run_id. Arbitrary trusted Python can use randomness/network/clock; the
platform cannot guarantee determinism for intentionally nondeterministic source.
