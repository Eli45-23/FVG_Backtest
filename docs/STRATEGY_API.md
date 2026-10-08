# Strategy SDK v1

Only run strategy code you trust. Python workers are **not securely sandboxed**.
They can access files and the network with your local account's permissions.
Validation executes top-level source in a separate process (10-second timeout).
Backtests use a separate process (600-second timeout). Cancel terminates its process group.

## Smallest strategy

```python
from decimal import Decimal as D
from engine.strategy import Float, Entry

class Strategy:
    name = "Morning candle experiment"
    feature = "bars"
    inputs = [Float("target_r", "Target R", 2, min=.25, step=.25)]

    def on_bar(self, ctx, p):
        if ctx.bar.time == "09:45" and ctx.bar.close > ctx.bar.open:
            return Entry("LONG", ctx.bar.low - ctx.tick_size,
                         D(str(p["target_r"])))
        return None
```

Paste this into **New Strategy**, save, validate, choose dates, and run. No backend
source changes are needed. This example illustrates the API, not an investment recommendation.

## Inputs

Constructors: `Float`, `Int`, `Bool`, `String`, `Choice`, `Time`, `Session`.
All accept `id`, `label`, `default`; numeric constructors accept `min`, `max`, `step`;
all accept `description`; Choice requires `choices`. IDs must be unique.

```python
from engine.strategy import Float, Int, Bool, String, Choice, Time, Session
inputs = [
    Float("max_risk", "Maximum risk", 100, min=0, step=.25),
    Int("length", "Lookback", 14, min=1, max=256),
    Bool("longs", "Allow longs", True),
    String("memo", "Label", "Experiment"),
    Choice("side", "Side", "both", ["both", "long", "short"]),
    Time("cutoff", "Trigger before", "11:00"),
    Session("window", "Research window", "09:30-11:00"),
]
```

Numeric overrides are validated for finiteness, bounds, integer type and step.
Time is HH:MM; session is HH:MM-HH:MM. Time/session inputs are values for your hook,
not implicit execution rules. Overrides live in immutable run configs, not source.
Unknown input IDs fail validation. Source version and parameters are recorded separately.

## Context and confirmed timing

`Context` and its `Bar`/`FVG` objects are frozen dataclasses. Decimal OHLC prices
are already normal point prices; never divide them by 1e9 again.

- `timestamp`: current candle's CLOSE instant, timezone-aware UTC.
- `bar.timestamp`: current candle START, timezone-aware UTC.
- `bar.time`: current candle START HH:MM in America/New_York.
- `bar`: open/high/low/close/volume, known only after confirmation.
- `previous_bar`: previous adjacent complete candle, or None.
- `history`: tuple ending with the current confirmed bar, maximum 256 bars; resets on gaps/incomplete bars.
- `instrument`: MNQ; `tick_size`: Decimal("0.25").
- `position`: None in v1. Hooks request flat entries; no live-position callbacks.

The public context contains no future DataFrame, lifecycle outcomes or unconfirmed
candles. This prevents accidental context-based look-ahead, not malicious trusted code
reading raw files itself. Strategies should be pure functions of context and parameters;
randomness, wall-clock reads and external I/O break reproducibility and are unsupported.

### Feature provider: fvg_second

`feature = "fvg_second"` calls the hook once per validated FVG when its exact second
post-formation candle closes. All five formation/post candles must be adjacent, complete
and on the same NY date. `fvg` exposes id, direction, top, bottom, formation START and
opening_exception. `bar1`/`bar2` are the first/second post candles. History contains those
five confirmed candles. The provider does **not** prefilter for CONT-A entry predicates.
Your source defines the entry predicate. Lifecycle hindsight fields are never exposed.

Default `feature = "bars"` works without an FVG setup and supports completely new concepts.
Additional causal feature providers belong in engine/data.py with dedicated tests.

## Entries, structural stops and targets

Return `Entry("LONG" | "SHORT", stop, target_r=Decimal("2"), max_risk=None,
metadata={})`, or None. Entry happens at the confirmed bar close with configured adverse
slippage. The engine rounds the stop outward, calculates original risk, rejects nonpositive
risk, then applies an optional **exclusive** max-risk bound before the daily lock. Target
is calculated from executed entry plus/minus original risk times target R, rounded to ticks.
Metadata must be JSON-serializable and is preserved with the trade. Prices should use Decimal.

One eligible trade per full XNYS calendar date. Stable event order uses confirmation time,
oldest FVG formation and stable feature ID. Rejections do not consume the lock. A source
can use any eligible intraday trigger before the 16:00 close; CONT-A's 11:00 cutoff is in
its source, not hard-coded into the generic engine. No overnight positions are supported.

## Position management (v1.1)

Implement `manage(ctx, params)` and return `MoveStop(price, reason, trigger_type,
trigger_value, metadata)` or a list, or None. The engine alone controls activation;
requests observed from a minute activate at the next minute start. Frozen context
provides original risk, current stop, confirmed OHLC, excursions and applied history.
See [MANAGEMENT_API.md](MANAGEMENT_API.md) for complete event ordering and examples.
The old reserved StopUpdate type is not an executable request; use MoveStop.
No callback (or management_enabled=False) preserves the exact fixed-bracket path.

## Immutable source history (v1.1)

Strategies → Versions lists hashes, creation dates and associated run/variant counts.
Select either side of Monaco Diff for read-only comparison. Clone this version creates a
new strategy. Restore as NEW version always appends, even when restoring current source.
Runs/Variants tabs display relationships for the selected source version; each run links
back to the exact source it used. No endpoint edits old source.

## Built-in presets

One CONT-A source has three saved input variants: baseline (max_risk=0 means disabled),
risk <100, and risk <100 with exclude_middle=True. Source returns the same mirrored
second-candle predicate and one-tick first-post-bar stop as the legacy runners. Their
full-data fingerprints are checked against preserved local reference files.


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
