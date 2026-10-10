# Standalone market-structure continuation · frozen Development experiment v1

Status: DEVELOPMENT_ONLY_NOT_VALIDATED. Dataset research_2020_2026; New York dates
2020-01-01 inclusive through 2024-01-01 exclusive. No key-level or indicator filter.

## Signal contract

Each full XNYS RTH session starts with fresh structure. Exclude holidays/half-days.
Use complete consecutive 5-minute bars. Missing/incomplete bars reset detector state;
no bridging, synthetic candles, or overnight structure. Strict pivots use two bars
left and two right from the existing Structure provider. Equal extremes are not
pivots. A pivot becomes known at the second right-hand candle's close.

Long: latest confirmed low is HL versus the previous confirmed low, its formation
follows the latest confirmed high, both are available before the trigger candle
starts, and the first confirmed close breaks strictly above that high (previous
close at/below). Short mirrors this with LH and a break below the latest low.
No requirement that the high itself be HH or the low itself LL. No additional
BOS-state filter. The existing provider consumes the first close-break of a pivot
whether or not this entry qualifies; no deferred entry or recycled broken pivot.
Only new eligible swing breaks can create further entries.

Entry at breakout close plus one adverse tick (primary); one MNQ micro.
Stop one tick below HL for long / above LH for short. Fixed original 2R target
from executed entry, existing tick rounding. Reject nonpositive risk explicitly.
One position across both directions; busy signals logged, not queued. New entries
at session close rejected. Later distinct eligible setups allowed; no daily cap.
Stop/target/session close only. No trailing, breakeven or partial exits.

## Costs and timing

Primary one adverse tick per side. Zero/two tick sensitivity uses identical raw
signals but reselection is allowed as exit times differ. Actual user-supplied fees:
commission .25 + exchange .35 + clearing .12 + NFA .01 = $.73/side, $1.46 roundtrip.
Native unchanged 1-minute executor, stop first, adverse opening gaps, no synthetic
missing minutes. Trigger candle cannot fill its own newly created trade.

## Movement measurements

Report .5R/1R/1.5R/2R reached while a position is open, stop first in conflicting
minutes. Ambiguities listed separately. Conservative maximum R caps at the 2R
exit. Native MFE/MAE includes the full exit minute and may exceed 2R; intraminute
ordering is unknown and such excess is not evidence of attainable post-target
profits. No prices after exit are used for movement statistics.

Overall, direction, yearly, monthly, time-of-day, risk, equity and cost summaries.
Time/risk groups descriptive only; no selecting a best subgroup. Date-clustered
bootstrap intervals exploratory. No Validation/OOS outcome reads; prior records,
market data and production strategy/execution code unchanged.
