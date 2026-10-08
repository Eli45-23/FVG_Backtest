# Level Research Foundation — architecture and measurement contract

This is an additive research subsystem, not a trading strategy. Legacy RunConfig, input paths,
execution, management and experiment/OOS routes remain unchanged. New dataset profiles and
EventStudy records own research dates, identities and artifacts. Existing engine fingerprints
remain stored on old runs; adding engine code changes the current engine hash normally.

## Frozen measurement definitions
- Profiles: legacy_2024_2026 and research_2020_2026. End dates are exclusive NY dates.
- RTH follows installed exchange_calendars XNYS including actual early closes. Holidays have
  no RTH study observations. PDH/PDL require every complete 5m slot in the immediately previous
  exchange session; no stale fallback across missing sessions. Prior half-days are valid
  completed sessions. Research interactions occur during RTH, including half-days.
- PM window is explicit, same NY calendar date, 5-minute aligned, ending no later than 09:30.
  No default window is guessed. Disabled unless both endpoints supplied. PMH/PML freeze at
  configured end and require all expected complete bars; no evolving/future premarket extreme.
- O5H/O5L become available at 09:35. Source 09:30 candle cannot interact with its own levels.
- Detector receives only confirmed sequential candles and levels available at candle START.
  Levels are immutable daily objects. A reusable LevelEngine.update interface works without
  any forward dataframe and can be used by ordinary strategy code.
- A touch episode begins when low <= level <= high after a non-touching complete candle.
  Consecutive straddling candles are one touch; gaps reset continuity, not touch numbering.
- Approach is previous consecutive close side, otherwise opening side; exactly-on-level has
  unknown direction and is retained. Sweep: strict through + strict close back on approach side.
  Break: confirmed close strictly opposite the known approach. Gap-cross breaks are recorded
  even when no candle traded at the level; they do not increment touch count.
- Retest: later separate touch episode approaches from the confirmed break's new side.
  Rejection: configurable minimum penetration and close-back clearance (both explicit saved
  parameters, defaults 0 and .25 points). This mechanical proxy is not a trading confirmation.
  Classes are separate overlapping records linked to the same observation/level; counts must
  not be summed as independent trials. Repeated events are not statistically independent.
- Outcome reference = event confirmed close; owned forward minutes start at that close.
  5/10/15/30/60-minute and actual session-close labels are computed in a separate module.
  Full consecutive minute coverage is required. Missing/invalid minutes censor that horizon;
  fixed horizons extending beyond session close are censored, never silently shortened.
  Threshold timing is the end of the first touched minute: intraminute order is unknown.
- Up/down excursions are absolute price directions; favorable/adverse use continuation of
  approach direction. Rejection interpretation reverses the sign. Unknown approach has null
  directional values. Excursions are nonnegative, anchored at event close.
- Baseline is every ordinary complete RTH 5m confirmed-close observation (including event
  observations), matched by year and 30-minute NY confirmation-time bucket. Direction is
  matched at analysis time. Each event receives equal weight across its matched baseline;
  repeated baseline observations are disclosed, not represented as independent sample size.
  No random seed, ML, volatility optimization or strategy selection. ATR14 is causal context
  only; volatility matching is deliberately not implemented yet.

## Split policy
Development [2020-01-01,2024-01-01); validation [2024-01-01,2025-01-01);
OOS [2025-01-01,2026-10-06). Dataset bounds intersect these ranges. Crossing segment
boundaries is rejected. OOS detection may run, but labels/baseline summaries and future
chart candles are unavailable until explicit audited reveal. Reveal records are append-only;
immutable artifacts remain local/ignored. This is a trusted-local workflow, not encryption
or a security boundary against the computer owner.

## Implementation plan
1. Profiles, causal levels/zones/events, independent labeler, synthetic tests.
2. Additive study/reveal persistence, isolated worker, query/export/chart APIs and safeguards.
3. Event Studies UI and chart reuse; automated API/component/browser verification.
4. Full legacy golden reruns, development-only smoke study, documentation and local commits.

No existing data file is rewritten and no new paid data is requested. Untracked user scripts
are left alone. Generic Zone is infrastructure only; supply/demand detection awaits a frozen
mechanical specification. No research result is used to recommend a strategy in this task.
