# Four-hour supply/demand V2 — frozen engineering specification

Status: acceptance pending. Opt-in provider `DisplacementBaseZoneProviderV2`.
V1 source, default research paths and their engine identity remain unchanged.
This module is intentionally outside `engine/research`, whose source hash is
part of existing immutable studies. V2 identity includes its own code and
configuration hashes; it cannot be substituted for V1.

## Visual contract

The two user screenshots are illustrative 2026 design references, not research
evidence. Supply is the base before a drop; demand is the base before a rally.
Departures never determine rectangle bounds. Supply top is maximum base wick
high; bottom is minimum base body low. Demand bottom is minimum base wick low;
top is maximum base body high. Midpoint is display-only. Origin can be drawn
back to the base, but it must be marked unavailable until departure closes.
The screenshots use a fixed UTC−5 display during daylight saving time. Their
13:00/05:00 labels are compatible with 14:00/06:00 America/New_York, but pixels
alone cannot establish the exact vendor aggregation or back-adjustment setting.
No 2026 data is queried for this implementation audit.

## Session foundation

Preset `CME_GLOBEX_4H_SESSION_ANCHORED_V1`: America/New_York session starts
18:00 on the preceding calendar date. Full starts are 18:00, 22:00, 02:00,
06:00, 10:00; the 14:00-to-session-close bar is shortened. The regular close
is 17:00. DST follows the IANA timezone. The saved CMES calendar supplies
candidate holiday sessions and shortened closes; regular closes are capped
at 17:00. This candidate calendar must be audited against source coverage;
disagreements must not be silently relabeled as exchange closures.

Before June 28, 2021, exclude the scheduled 16:15–16:30 NY pause from expected
source minutes. The pause was eliminated effective that date; see CME
[SER-8788R](https://www.cmegroup.com/content/dam/cmegroup/notices/ser/2021/06/SER-8788R.pdf).
This is a dated schedule rule, not a gap inferred from price outcomes.
Missing expected minutes disable the bucket and reset ATR. Unexpected minutes
inside a scheduled pause also disable it. Out-of-session rows are exported
for calendar investigation. There is no forward fill, interpolation or price
repair. Empty expected intervals are audit rows, not candles.

ATR14 is the arithmetic mean of true range over 14 eligible full completed
bars. TR uses the previous eligible full close. Scheduled maintenance and
weekends preserve it. A complete shortened bar is excluded from ATR, preserves
ATR memory and clears formation adjacency. An incomplete shortened bar resets
ATR. Thus no base/departure bridges a shortened bar. Prior history is requested
before January 2020, but the available master starts January 1, 2020 at 18:00
NY: unavailable warmup is disclosed, never synthesized.

## Base and departure

Start at the last full candle before departure. Extend backward to at most
three candles, stopping at the first failure. Every body/range <=0.50; combined
wick range <=1.25 × ATR14 known at the last base close. Overlap means strictly
positive common wick-range intersection across all selected candles (edge-only
contact fails). Zero-range candles have body ratio zero but a zero-width final
zone is rejected. Prices must be valid 0.25 ticks.

Departure is the immediately following one or two full candles. At least one
has body/range >=0.60. Confirming close must be strictly beyond the base wick
extreme and at least 1.00 base-reference ATR from the proximal boundary. First
qualifying close determines availability. No third-candle rescue. The last-base
ATR is frozen, so changing departure volatility cannot move the threshold.

Incoming pattern is the sign of close minus open on the immediately preceding
confirmed candle before the selected base. Missing/neutral incoming candle is
UNKNOWN. It is metadata, never a gate. BOS/CHoCH, FVG and indicators are optional
context; unavailable context is not evidence of absence. FVG means a strict
three-candle wick gap ending at departure confirmation, with no shortened or
missing candle bridge.

## Lifecycle

All actual complete five-minute bars after availability may record contact,
including overnight. A touch episode ends on a noncontact bar; missing bars
break episode continuity and flag subsequent observations as uncertain.
Threshold events occur once per episode. Contact includes boundary equality;
entry is strictly positive penetration. Supply penetration is
(high−proximal)/width, demand is (proximal−low)/width. Values above 100% remain
visible as distal wick breaches. Full traversal requires the candle's range
cover both boundaries; this does not assert intrabar path order.

Rejection requires contact and a close strictly on the original side of
proximal. Confirmation is the adjacent complete five-minute close beyond the
rejection candle's extreme in the rejection direction. Touch/entry/mitigation
are persistent independent flags; no touch deletes a zone. Only a complete
full four-hour close strictly beyond distal invalidates it. Post-invalidation
five-minute reclaim closes back inside distal; retest requires a distinct
contact approached from a previous close strictly on the broken side.

Forward research is forbidden until source, causal, synthetic and visual
acceptance gates pass. Development only: [2020-01-01, 2024-01-01). No strategy,
Validation query, OOS reveal or threshold fitting is authorized.
