# Supply and demand zones — research and Lab contract

Research date: 2026-10-09. Scope: external conceptual research and inspection of existing code. No historical predictive studies, Validation queries, OOS reveals, provider tuning or strategy changes were performed.

## What a zone is and where it starts

For this Lab, a zone is the **base immediately preceding a qualifying directional departure**, represented as a price interval. The base is the origin; the departure is the evidence that makes the candidate knowable. Supply is a base followed by a sharp decline; demand is a base followed by a sharp advance. Broker educational material describes tracing an impulsive move back to its preceding consolidation, while cautioning that zones can fail. This is an analysis convention, not direct observation of unfilled institutional orders. [CMC Markets](https://www.cmcmarkets.com/en-gb/technical-analysis/what-is-supply-and-demand-in-trading)

Sam Seiden describes four pattern families and explicitly emphasizes quantifying what counts as supply/demand rather than relying on the picture alone. This is useful primary practitioner material, not an independently validated MNQ detector or performance guarantee. [Seiden, “Is This In Your Trading Plan?”](https://www.fxstreet.com/amp/education/lessons-from-the-pros-201406030000)

| Incoming move | Base | Departure | Label |
| --- | --- | --- | --- |
| Rally | Pause/base | Drop | Supply, reversal pattern |
| Drop | Pause/base | Drop | Supply, continuation pattern |
| Drop | Pause/base | Rally | Demand, reversal pattern |
| Rally | Pause/base | Rally | Demand, continuation pattern |

A single large reversal candle, an arbitrary swing extreme, an FVG and an order-block convention are not automatically the same thing as this base/departure definition. Do not silently interchange their detector outputs. The original user screenshots specify a base-only rectangle, body-based proximal edge, wick-based distal edge and forward extension; those are the Lab's explicit visual semantics, not numerical ground truth extracted from image pixels.

## Exact rectangle convention for our software

These formulas preserve the user's previously chosen convention and the current V2 implementation. They are not presented as the sole industry-standard way to draw zones.

For each selected base candle, body low = min(open, close), body high = max(open, close).

| Boundary | Supply | Demand |
| --- | --- | --- |
| Distal: far edge | Maximum base wick high (top) | Minimum base wick low (bottom) |
| Proximal: near edge on a normal return | Minimum base body low (bottom) | Maximum base body high (top) |
| Width | Distal minus proximal | Proximal minus distal |
| Normal approach | From below | From above |

**Departure candles never contribute to these bounds.** Freeze the selected base, bounds and source identities when the departure confirms. A later successful bounce must not move the rectangle to a better-looking origin.

Synthetic example, not market data: two base candles have bodies 100–101 and 100.5–101.5, with combined wick range 99–102. A qualifying bullish departure gives demand **99–101.5**; a qualifying bearish departure gives supply **100–102**. It is the departure direction, not candle color alone, that distinguishes the candidate.

There are two different timestamps:

- **Origin:** start of the first selected base candle, where the rectangle can be drawn historically.
- **Availability:** close of the first departure candle that satisfies all frozen confirmation rules. The detector, strategy and interaction recorder cannot use the zone before this time.

The chart may shade the base retrospectively but must distinguish it from the actionable extension that starts at availability. It must not make the zone appear available during its own departure.

## Why price might react, and what the evidence actually says

CME describes support/resistance as areas where trends may pause or reverse, notes that levels can fail, and discusses former support becoming resistance and vice versa. That supports measuring multiple possible reactions instead of assuming every return bounces. It does not supply this Lab's base-detection thresholds. [CME Group](https://www.cmegroup.com/education/courses/technical-analysis/support-and-resistance)

Carol Osler's research studies currency support/resistance and dealer orders. It offers empirical evidence and a microstructure explanation for both reversals at levels and acceleration after breaks, including clustering of stop-loss and take-profit orders. Its market, period and level definitions differ from four-hour MNQ base zones. We cannot transfer those results into a claimed MNQ zone edge. [Federal Reserve Bank of New York, Staff Report 125](https://www.newyorkfed.org/research/staff_reports/sr125.html), [Osler, 2000 study](https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf)

Our inference: chart geometry is a testable proxy for a past directional price move. OHLC alone cannot establish which participants traded, whether institutional orders remain, or whether repeated touches consumed those orders. “Fresh zones are stronger” and “each retest weakens a zone” remain hypotheses to measure, not automatic eligibility filters.

## Reactions to record, without building a strategy

Let B = zone bottom, T = top, W = T−B > 0. The following describes an explicit measurement vocabulary; existing versioned lifecycle rules remain unchanged.

| Reaction | Objective observation |
| --- | --- |
| Contact | A post-availability candle overlaps [B,T], including boundary equality |
| Entry/penetration | Price moves strictly beyond the proximal edge into the zone |
| Partial penetration | Supply: (high−B)/W; demand: (T−low)/W; between 0 and 1 |
| Full depth / distal touch | Penetration reaches 1; report as geometry, not proof orders were “mitigated” |
| Distal wick breach | Penetration exceeds 1; retain actual depth rather than clipping away the breach |
| Rejection | Contact then close outside proximal on the approach side: supply close < B; demand close > T |
| Close through | Supply close > T; demand close < B; record timeframe explicitly |
| Failed break/reclaim | A break followed by a subsequent confirmed close back across the distal boundary; store both event times |
| Retest | A later distinct contact approached from the broken side after a break |
| Repeated contact | Separate episodes split by a noncontact bar; do not count each overlapping candle as a new first touch |

A full-range candle does not reveal intrabar order. A candle spanning both zone boundaries can traverse either way. Do not infer first passage from OHLC without finer data; even one-minute OHLC retains ambiguity.

V2 already distinguishes five-minute interaction observations from its **full four-hour close beyond distal** invalidation rule. A five-minute close through is not automatically a four-hour invalidation. Wick breach, rejection, reclaim and invalidation can occur on different timestamps; maintain separate flags/history instead of one overloaded “broken” field. Gaps that jump past a zone must not be mislabeled as a traded-through contact.

## Current provider compared with this research

`engine/zone_v2/provider.py` already implements the user's main geometry correctly: base-only bounds, separate departure, frozen ATR reference, first qualifying confirmation, deterministic identity and no future reaction requirement.

Its numerical definition is **a frozen engineering proposal**, not a conclusion of the sources:

- 1–3 base candles, each body/range <= 0.50;
- combined base wick range <= 1.25 ATR14;
- strictly positive common wick-range overlap;
- immediately following 1–2 departure candles;
- at least one departure body/range >= 0.60;
- confirming close beyond base wick extreme and >= 1.00 base-reference ATR from proximal;
- no third-candle rescue; no departure candle in boundaries.

These rules may omit visually plausible formations or include weak ones. The greedy backward base selection and the single incoming candle used to name a reversal/continuation are operational conventions, not proofs of market structure. The research reviewed here does not justify changing 0.50, 1.25, 0.60, 1.00 or choosing a more profitable threshold.

Use the accepted, versioned historical foundation `MNQ_GLOBEX_HISTORICAL_SESSION_CALENDAR_V1` with `CME_GLOBEX_4H_SESSION_ANCHORED_V2` when a future approved task resumes zone work. Its New York session anchor, official exceptions, excluded unresolved sessions, shortened bars and exact source coverage must remain part of the identity. Do not replace it with midnight UTC or vendor chart boundaries. See [calendar contract](MNQ_HISTORICAL_SESSION_CALENDAR.md) and [bar contract](MNQ_FOUR_HOUR_BAR_CONTRACT.md).

## Software decision and next usable workflow

The Zone Labeler workspace is removed from navigation and rendering. Manual annotation is no longer the application's user-facing zone workflow. Existing annotation files, immutable snapshots, comparison artifacts and compatibility endpoints are retained so this change does not destroy prior research. Old React components remain unmounted historical compatibility code, not a screen users need to operate.

The useful future interface is **automatic, explainable zone inspection** in the existing chart: draw the base rectangle, mark departure bars and availability, show source timestamps/boundary arithmetic, and distinguish contact/rejection/break states. It should explain why a zone exists without requiring the user to label dozens of windows. This is a documented direction, not a claim that a replacement screen has been implemented in this change.

Retiring the labeler does **not** silently accept V2 or bypass its research gate. Its stored status remains `PROVISIONAL_PENDING_HUMAN_GROUND_TRUTH`, preserving the existing contract even though the UI workflow is retired. A separate explicit versioned acceptance decision must replace that gate before zone outcome studies can run. A legitimate alternative is a mechanically specified hypothesis evaluated on Development with causal construction/coverage tests and matched baselines; call that mechanical research validity, not agreement with discretionary human ground truth. Do not relabel old studies or invent precision/recall without actual labels.

For a future authorized measurement task: freeze definition and calendar identities first; include every eligible zone regardless of later reaction; compare rejection and continuation after confirmed interactions against matched ordinary observations; preserve censoring, within-date clustering and multiple-testing correction; keep Validation/OOS sealed. No entry, stop, target, indicator filter or automatic “best zone” score is selected by this document.

## Sources and limits

All sources above were accessed 2026-10-09. CME provides exchange education; CMC and Seiden provide their own practitioner explanations; Osler provides primary empirical FX research. None establishes a universally correct candle-count/ATR detector or demonstrates profitability for this project's MNQ four-hour zones. The sources support understanding and explicit measurement, not an assertion that chart-defined zones contain resting orders or must cause reversal.
