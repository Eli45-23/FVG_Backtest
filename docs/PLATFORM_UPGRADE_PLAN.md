# Platform upgrade: compatibility boundary and phased implementation

Start: 653bb92. Existing metadata backed up online to work/upgrade-before.db; input identities
captured in work/upgrade-data-identities.json. No secrets read and no market files modified.
The 341-test baseline and exact golden fingerprints are the regression authority.

Legacy defaults must dispatch to the existing execution implementation. New execution settings
are explicit immutable fields; absent fields resolve to legacy. Research v2 artifacts are
additive, with old JSON readers retained. No existing study or reveal is rewritten.

Phases: execution profiles; causal compound/numeric research; clustered statistics; sequential
execution; structure; explicit multi-timeframe aggregation; indicators/context; zones;
ATR labels; opt-in legs/sizing; columnar storage; integrated UI and engineering benchmark.

Ambiguities are configuration, not inferred trading filters. In particular a strict full-hold
candle cannot literally touch the level. Retest full-hold therefore requires a later adjacent
complete candle; the retest candle itself can only close-hold/fail. Both timestamps are retained.
4h requires an explicit UTC-clock or NY-session anchor; no assumed CME session. All mechanical
rules and warmups must be in snapshots. No OOS benchmark labels or strategy optimization.

Execution remains flat-only. Multiple entries may follow an exit confirmed at/before the next
signal time. Stop-first intraminute ambiguity remains. Partial fills are opt-in and isolated
from Entry's old behavior. Dataset selection never rewrites previous run identities.
