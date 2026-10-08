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
- Legacy v1 segment labels remain historical labels. New v1.1 official OOS uses immutable
  frozen experiments and explicit reveal; see RESEARCH_SPLITS.md. This is a workflow
  safeguard, not protection against deliberately reading local files. No automatic winner selection.

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

## v1.1 opt-in management contract
Unmanaged sources continue to call the original executor. `manage(ctx, params)` opts
into the versioned managed executor; the standard `management_enabled=False` input
selects the original path. Entry/stop/target selection and daily locks remain unchanged.

Minute M is evaluated with its already-active stop and fixed target. Stop wins simultaneous
hits, adverse stop gaps use the worse open, full-minute extrema remain included. Exit
(including 15:59 session close) suppresses all callbacks. For a survivor, minute-close
and any complete 5m-close callbacks see the same pre-update stop. All requests at that
confirmation compete; most protective valid request wins. It activates at the next minute
START, equal to the observation's close timestamp, never earlier within minute M.
Stop updates round outward to MNQ ticks, cannot loosen, and must remain strictly inside
the original fixed target. A newly active stop beyond the next open uses adverse gap fill.
Missing owned minutes fail; incomplete 5m candles produce no 5m management event.

Callbacks get a fresh manager per trade, so precomputed future entry callbacks cannot
leak mutable strategy state into management. Context/history are frozen; public helpers
use original risk. Pure management should use that context and parameters, not external I/O.

The Quality R-Step preset first requests +5 after a surviving +50 touch. Subsequent hold
candles must START at/after that update's activation and fully close. Holds are strict:
long low > threshold / short high < threshold. Qualifying 1R/1.5R/1.75R holds request
1R/1.25R/1.5R; simultaneous thresholds use the most protective request. No sequential
waiting between R tiers is invented. The target remains original 2R.


## Additive research/execution upgrade

New ordinary backtests may explicitly select `research_2020_2026`; absent profile fields
retain legacy behavior. See [Execution extensions](EXECUTION_EXTENSIONS.md) for confirmed
multi-timeframe context, flat-only sequential trades, partial legs and risk sizing.
See [Research v2](RESEARCH_V2.md) for mechanical sequences, structure, zones, indicators,
columnar artifacts, numeric filters, date-cluster inference and limitations.

Migration 5 adds only `research_split_profiles` and immutability triggers. Existing table
rows and artifact paths are not rewritten; splits without an association imply legacy.
Back up SQLite before first upgraded launch. Normal startup retains existing data and never
redownloads paid market data. To reproduce an old sealed study's forward labels, retain its
original frozen engine checkout; this upgrade does not bypass its identity checks.
