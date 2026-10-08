# Causal management API v1.1

A strategy may implement `manage(ctx, params)`. Return None, `MoveStop(...)`, or a list
of requests. No callback means the original fixed-bracket executor is used unchanged.
An optional boolean input named `management_enabled=False` also uses that original path.

```python
from engine.strategy import MoveStop

def manage(self, ctx, p):
    if not ctx.stop_history and ctx.touched_profit_points(50):
        return MoveStop(ctx.entry_price + ctx.direction_sign * 5,
                        reason="+50 touch → +5", trigger_type="points_touch",
                        trigger_value=50)
    return None
```

The reference source `strategies/builtins/cont_a_rstep.py` implements the complete requested
policy. It keeps risk<100, excludes 10:00–10:29 trigger starts, and retains original 2R.
After +50 touch requests +5, a later whole candle holding beyond 1R/1.5R/1.75R requests
+1R/+1.25R/+1.5R. Strict inequalities; all thresholds at one close compete. This is a
validation example, not a claim of improvement. No thresholds were optimized.

## Event ordering
1. At minute START the previously requested stop is active.
2. Observe this owned minute's OHLC; update full-minute MFE/MAE.
3. Resolve active stop/target, conservatively stop first if both. Apply adverse stop gaps,
   unchanged slippage/commission, or 15:59 session close. Exited trades get no callback.
4. For survivors, call `minute_close`; if an eligible complete five-minute candle just
   closed, also call `bar_5m_close`. Both see the same pre-update stop/history.
5. Validate requests, round stops outward using the existing .25-tick function, reject
   loosening and stops at/beyond fixed target; choose the most protective valid request.
6. Activate at the NEXT minute start, which is the observation's close timestamp.

No request can affect price activity in the interval that produced it. Crossing the new
stop before confirmation cannot retroactively exit. If next open gaps beyond it, the usual
adverse-gap rule applies. Targets never move. Incomplete 5m candles never produce hold
callbacks; missing owned minutes fail the run. The R-Step preset additionally requires a
hold candle's START to be at/after the initial +5 activation, excluding pre-trigger activity.

## Immutable context
`timestamp` is observation close; `event` is minute_close/bar_5m_close. Context includes
entry_time/price, original_stop, current_stop, target, direction/sign, original_risk_points,
MFE/MAE, confirmed minute, optional completed_bar and frozen stop_history. `minutes_since_entry`
is elapsed owned minutes; `bars_since_entry` counts elapsed five-minute slots, not synthetic
candles. Helpers: price_at_r, reached_r, touched_profit_points, completed_bar_holds_beyond_r.
The hold helper uses long low > level / short high < level, never equality.

A fresh manager instance per trade prevents future entry precomputation state leaking into
management. Pure callbacks should derive state from context and parameters. Public context
contains no future data or mutable position. Trusted Python can still read arbitrary files:
this is not a secure sandbox. Worker timeout/cancellation applies to management too.

## Audit and reproducibility
Each applied update records event/trade IDs, observation timestamp, observed minute start,
source event, trigger type/value, prior/requested/effective stop, activation timestamp,
reason and metadata. Equal-stop requests are no-ops. Simultaneous requests produce one
applied event with the most protective result. Events use stable deterministic IDs.

Run artifacts include management_events.json and original result.json. Trade records add
final_stop_price, management_exit, management_event_count and locked_r_at_exit. The original
stop/risk/target stay unchanged. STOP remains the exit reason; management_exit disambiguates.
Run config includes source/parameter identity and management behavior version
`minute-close-next-start-v1`. Summary includes event count, management exits and average
final-stop R (including unchanged -1R stops). Counterfactual profit protected is null:
a separate paired causal comparison would be required to define it rigorously.


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
