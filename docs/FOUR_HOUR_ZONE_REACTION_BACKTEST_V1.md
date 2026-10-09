# Four-hour zones / five-minute reactions — frozen Development test specification

Specification version: 1. Recorded 2026-10-09 from the user's voice instructions.

**Specification status: FROZEN. Outcome execution: AUTHORIZED_DEVELOPMENT_MECHANICAL_RESEARCH.**

The user approved three separately reported setups, full-candle outside-zone confirmation, boundary stops, fixed 2R, no management, full NYSE regular sessions, no holidays or half-days, one position at a time and re-entry only after a new contact episode. This document makes those rules concrete. The user subsequently authorized removing the human-label prerequisite and proceeding with these three Development backtests. This authorization does not certify predictive performance or human-label agreement.

## Common contract

- MNQ; four-hour zones, confirmed five-minute signals and existing one-minute execution.
- Development only: New York 2020-01-01 inclusive through 2024-01-01 exclusive; dataset `research_2020_2026`.
- Zone source: `DisplacementBaseZoneProviderV2`, unchanged thresholds, on accepted/resolved `MNQ_GLOBEX_HISTORICAL_SESSION_CALENDAR_V1` / `CME_GLOBEX_4H_SESSION_ANCHORED_V2` bars. All 104 unresolved historical session dates stay excluded.
- Zone bounds are fixed: L = bottom, U = top. Base candles set bounds; departure candles do not. A zone is usable only after its recorded availability.
- “Entire candle outside” means strict separation INCLUDING WICKS: below zone requires high < L; above requires low > U. Equality is a touch, not an outside candle. No candle-direction/body-ratio filter.
- Entry at the signal candle's confirmed close. Only subsequent activity is owned; the one-minute bar starting at that confirmation is the first execution minute.
- One MNQ micro, $2/point, 0.25-point tick. Primary cost defaults retained from the preceding research discussion: one adverse tick each side, actual user-supplied Webull all-in fee $0.73/side ($1.46 round trip).
- Fixed original 2R from executed entry and initial stop, with existing tick rounding. No trailing, breakeven, partial exit or other management.
- Regular-session signals only on full XNYS dates. Exclude holidays AND half-days. Entry must precede 16:00 NY; no artificial entry-and-exit at the same closing instant. Final owned minute stop/target precedes session-close exit.
- Each setup is an independent run, with at most one open position in that run. Do not combine their trades or claim the sum is a single portfolio. No one-trade/day restriction: a later new contact episode can qualify after the prior position closes.
- Stop-first when stop and target touch within the same minute; existing adverse gap/slippage rules and strict owned-minute missing-data handling apply.
- Validation and OOS remain unqueried/sealed. No threshold optimization.

## Setup A — Enter zone, then reject fully outside

Supply SHORT:

1. Price approaches the active supply zone from below.
2. A five-minute contact episode actually penetrates the near boundary: high > L and low <= U.
3. After that episode, the first confirmed complete five-minute candle wholly below the zone (high < L) triggers SHORT at its close.
4. Stop = U + one tick.

Demand LONG mirrors this:

1. Approach from above.
2. Episode penetrates: low < U and high >= L.
3. First subsequent complete candle wholly above (low > U) triggers LONG.
4. Stop = L − one tick.

This is a separate candle after contact, not an entry using the contact candle's movement. Any intervening complete candles are processed chronologically; an incomplete/missing candle clears pending setup state. A zone that invalidates before the signal cannot produce this rejection entry.

## Setup B — Exact tap, no penetration, then reject

Supply SHORT: candle high equals L exactly, with no movement above L. A later separate complete candle with high < L triggers at its close. Stop = U + one tick.

Demand LONG: candle low equals U exactly, with no movement below U. A later separate complete candle with low > U triggers at its close. Stop = L − one tick.

An episode must remain unpenetrated to qualify for B. If a later candle enters the zone before the outside confirmation, it ceases to be a tap-only episode; it may qualify for A in that separate run. No tolerance band or near-touch approximation is introduced.

## Setup C — Full break, immediate full-outside confirmation

Supply breakout LONG:

1. Price approaches from below and crosses the supply zone.
2. First complete five-minute break candle wholly above the zone (low > U).
3. Immediately adjacent next complete five-minute candle must also have low > U.
4. Enter LONG at that confirmation close. Stop = L − one tick, beyond the opposite zone edge.

Demand breakout SHORT mirrors this: first full candle has high < L, adjacent next candle also high < L; enter at its confirmed close; stop = U + one tick.

The second candle need not close beyond the first candle's extreme: the user confirmed full-outside acceptance, not an additional momentum test. Missing/incomplete adjacency cancels the attempt. A failed attempt requires a new contact episode before another attempt; two arbitrary outside candles later in a trend are not a new breakout signal.

## Explicit implementation conventions for the first run

These details make the narrative deterministic without adding optimized filters:

- Approach side is the prior adjacent complete candle close; at RTH open use that candle's open. Only a normal-side approach arms a setup.
- A contact episode is a contiguous sequence of complete five-minute candles whose ranges overlap [L,U]. Boundary equality counts as contact. At least one contact is required before a break attempt; a gap jumping entirely over the zone without observed contact is not silently counted as traded-through.
- Record episode IDs independently of position ownership. A signal while occupied is skipped, never queued for delayed entry. The next entry needs a newly begun episode after the prior exit; no reuse of the episode that generated or overlapped the held position.
- Pending entry patterns reset at the end of RTH and on unexpected gaps/incomplete bars. Higher-timeframe zones can persist across dates while valid; no intraday pending signal carries overnight.
- Multiple eligible zones at the same timestamp: oldest zone availability, then stable zone ID. Audit the skipped competitors.
- Zone validity uses the unchanged V2 lifecycle, including full four-hour-close invalidation. Do not resurrect invalidated zones or infer validity from later reaction. Any same-timestamp invalidation/confirmation ordering must be covered by explicit causal tests before execution; it must not be chosen by P&L.
- Rejection setups require a still-active zone at confirmation. Breakout candidates must originate while active; their immediately adjacent confirmation may follow invalidation caused by that same breakout, but no unrelated later breakout can reuse the invalidated zone. Store this strategy-specific pending-confirmation allowance separately; never alter the historical lifecycle record.
- Reset pending patterns across excluded/unresolved sessions. Preserve excluded-date and incomplete-bar counts in the report rather than silently substituting data.
- Reject nonpositive executed risk explicitly. No maximum-risk or ATR eligibility filter.

## Three outputs, one common comparison

Run A, B and C separately with identical data/provider/cost identities and fixed 2R. Save raw signals, skipped reasons, trades, exact configurations and economic fingerprints. Compare trade counts, long/short results, yearly 2020–2023 performance, net/gross P&L, PF, average/median R, drawdown, stop size, MFE/MAE, contact number, same-minute ambiguity and source exclusions. These are Development hypotheses, not validated strategies. Do not pick a winner from aggregate net P&L alone.

Required checks: causal zone availability; no departure in base bounds; strict whole-candle separation and equality edge cases; tap-versus-penetration distinction; adjacent breakout confirmation; no signal-candle fills; one open position; fresh episode after exit; holiday/half-day exclusion; fixed stop/2R; native one-minute fills; deterministic repeats; unchanged source identities and old engine behavior.

## Current authorization and historical preservation

On 2026-10-09 the user explicitly instructed: “remove that restriction … then move on with the back testing.” The human-ground-truth prerequisite is removed for this mechanical Development experiment. The new `DEVELOPMENT_MECHANICAL_RESEARCH_V1` policy still requires engineering evidence and rejects Validation/OOS scope. It does not claim human-ground-truth acceptance.

The original readiness artifacts and old acceptance API remain unchanged for historical reproducibility. Their saved `forward_outcome_research_allowed: false` describes the earlier policy, not a veto on this later explicit authorization. The experiment records its own authorization and exact source hashes. Formation thresholds, calendar exclusions, fills and lifecycle behavior are unchanged.

Results retain `DEVELOPMENT_ONLY_NOT_VALIDATED`. Human labels are optional future diagnostic evidence, not a prerequisite for these runs.
