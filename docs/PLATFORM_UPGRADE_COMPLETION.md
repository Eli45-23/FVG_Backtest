# Strategy Research Lab platform upgrade — completion audit

Date: 2026-10-08 (America/New_York).
Starting commit: `653bb92f6daec812b3602daf49b7c328d26b4fd9`.
Implementation ending commit: `ddf585a5e787aeef0554ff2b94a8273fac80e238`.
This audit document is committed separately; its final delivery commit is recorded in the chat.
Nothing was pushed.

## Delivered architecture

The compatibility boundary is explicit: absent settings retain the original legacy profile,
one-trade/day policy and fill path. Opt-in extended execution adds causal feature snapshots,
sequential flat-only positions, partial legs and risk sizing. Market-data preparation,
FVG detection, lifecycle, original reference runners and historical reports were not rewritten.

Research v2 is separate from strategy execution. Confirmed level/structure events feed a
compound state machine; only after detection completes does the outcome pass inspect future
minutes. Events, ordinary observations and outcomes are immutable Parquet artifacts queried
with DuckDB. Version 1 JSON readers remain available. No historical artifact was converted.

SQLite migration **5** adds `research_split_profiles` plus immutable association triggers.
No existing table row is rewritten. Old splits resolve to legacy without adding fake history.
Migration was run twice on copies of both the starting and latest database, then applied to
the real database through normal startup. All **140 starting records** remain exactly intact;
two later-added records were also preserved: **142 records** total, excluding migration rows.
All **81 artifact references** still resolve. Existing reveal records were unchanged.
Backups: `work/upgrade-before.db` and `work/upgrade-before-release.db` (ignored, local only).

## Dataset identities

Dates are NY-calendar start-inclusive/end-exclusive. Source data remains unchanged.

| Profile | Source | Rows | SHA-256 |
|---|---|---:|---|
| legacy_2024_2026 | minutes | 977,725 | `1017843fa2937108fec7938891e46259492d2bf0a158cc35c40047691ce6d8c5` |
| legacy_2024_2026 | bars | 195,546 | `badd703b65d89953e0b209ed07218960d94b10423579e9a512b17f8eedbf592c` |
| research_2020_2026 | minutes | 2,388,306 | `6001255e1460ce6c8f45931ca252e4f0845c285de1458c7e86aa632b3ccbd700` |
| research_2020_2026 | bars | 477,855 | `002cc1dd81376a9791c63c133ab8100e1651dd85af6a7db0788dc8a33eb47582` |

New run identities include the selected profile, source hashes/row counts, strategy version,
source hash, parameters, execution settings, engine identity and management configuration.
The 2020 profile is usable by ordinary strategies, official research splits and Event Studies.
No paid download occurs at startup or during a backtest.

## Mechanical definitions

Detailed frozen defaults and assumptions are in [RESEARCH_V2.md](RESEARCH_V2.md) and
[EXECUTION_EXTENSIONS.md](EXECUTION_EXTENSIONS.md).

- Compound events: a break's adjacent complete candle confirms strict close/full hold or
  close-back failure. A later separate touch episode links retest hold/fail. Retest FULL_HOLD
  requires the immediately following candle, because a touching candle cannot simultaneously
  remain strictly outside the level. Sweep/rejection confirmation is the next adjacent close
  beyond the away-side extreme. Gaps, incomplete/invalid bars and date changes reset sequences.
- Structure: strict L/R confirmed pivots (default 2/2), formation and availability separated.
  HH+HL establishes bullish, LH+LL bearish; strict close breaks yield BOS with trend or CHOCH
  against it. Neutral breaks are labeled separately. Each swing breaks once; no backdating.
- 4h levels: latest confirmed 4h high/low remain references until replaced; broken status is
  explicit and retests remain researchable. No unconfirmed 4h bar is exposed.
- Zones: DisplacementBaseZoneDetectorV1, explicit base/body/range/ATR/departure settings,
  full-base or body-proximal/wick-distal bounds. Availability begins at departure confirmation;
  close through distal invalidates. The platform applies this detector to 4h bars.
- Indicators: close-seeded EMA9/20; simple TR14 ATR; percentile versus prior historical ATRs;
  explicit same-date typical-price volume VWAP, clipped to actual session close. Missing
  contributing bars invalidate VWAP. Regimes, efficiency, range, gaps and opening location
  are measurements only, never implicit entry filters.
- Timeframes: 1m/5m/15m/4h; extended UTC-midnight and RTH NY09:30 presets. Missing minutes are
  not synthesized. Ambiguous/nonexistent NY anchors fail instead of silently shifting.
- Outcomes: original point thresholds/horizons plus configured ATR multiples using ATR frozen
  at event confirmation. Missing minutes censor the horizon. Threshold timestamps are minute
  end bounds; no inferred intraminute ordering.

## Execution extensions

`max_trades_per_day` defaults to 1, with positive limits or unlimited (`null`). New positions
are flat-only: signals while occupied are audited POSITION_OPEN; exhausted dates receive
DAILY_TRADE_LIMIT. Rejected signals do not consume an entry. Each actual trade records its
sequence number. Primary callback timeframe and confirmed multi-timeframe context are explicit.

PositionPlan / TargetLeg supports fixed legs and targetless runners. Stop has priority over
all same-minute target hits; otherwise target legs fill nearest first. TP1 breakeven and
MoveStop requests take effect next minute. Every partial fill records remaining quantity,
realized P&L/costs and time. Exit average is quantity weighted; charts plot actual leg fills,
not the weighted price as if it were an executed final fill. MFE/MAE preserve full exit-minute
extrema. Fixed bracket legacy behavior is unchanged.

FIXED_DOLLAR_RISK floors budget divided by stop risk including adverse stop slippage and
round-trip costs, with entry slippage already in entry-to-stop distance. Zero quantity is
rejected, maximum quantity 100. Explicit target-leg quantities must match the final quantity;
there is no silent proportional leg allocation. Fixed quantity remains the default.

## Evidence and research UI

Event Studies v2 provides level/compound/direction/approach/touch/year/month/weekday/time and
structure/EMA grouping, inclusive numeric min/max filters, custom buckets, server-side sort
and paging, point/ATR threshold selection, clustered evidence tables and optional chart
categories. Query edits explore the immutable retained dataset; create a new study to freeze
another filtering specification. Exports stream the full saved study's JSON or event CSV.

Statistics report counts, dates, complete/censored outcomes, excursion descriptions, matched
baseline probabilities, absolute/relative differences, 95% CI, p and BH q. Matching uses year,
confirmation half-hour and fixed ATR bucket. Bootstrap resamples equal-weight NY-date mean
differences with stored seed/iterations; repeated events do not create extra independent dates.
Warnings identify small date samples. No automatic best-strategy or profitability label exists.

Strategies expose profile, timeframe, daily limit, sizing/risk, quantity/cost and frame-anchor
controls. Research splits can select the research profile. The trade inspector shows partial
fill history. Existing editor, saved versions/runs, comparisons and OOS workflow remain.

New API surfaces include POST study `/query`, POST `/statistics`, GET `/fields`, streamed
exports and persisted chart context. Old study/list/summary/chart routes remain supported.
Outcome access is gated before query/export execution; sealed charts end at confirmation.

## Exact legacy regressions

All three canonical trade fingerprints reproduce exactly, covering identities, entries,
stops, targets, exits, P&L, R and MFE/MAE, not merely rounded headline statistics.

| Reference | Trades | Net USD | Max closed DD | Exact trade SHA-256 |
|---|---:|---:|---:|---|
| CONT_A_second_candle_baseline | 263 | 525.50 | 2,488.00 | `a57bb17e3a401175fb7ed5b6328e4f66cec85cb5ee5a25ca806e4cf6e6992d8d` |
| CONT_A_max_risk_100 | 235 | 4,277.00 | 1,725.00 | `3d3fc6c748e79bcab58f5913f992c42cc7edfed186829b1b3d5928ffa47daf9f` |
| CONT_A_risk100_no_1000_1029 | 170 | 4,242.00 | 1,570.00 | `4719fc4e1b0ff00b63de7cf1aa4ff471eb4554b00037cf10625e5fe77420bf6d` |

## Engineering benchmark (Development only)

Profile research_2020_2026, **2020-01-01 through 2024-01-01 exclusive**. Full Development,
not a sampled subset. No 2025–2026 outcome research was run. Research code identity:
`da7af64f932571a61945fdfb9d4b9c07fdf314c0b012627d018c277af1ecbf3a`.

| Measurement | Result |
|---|---:|
| Source 5m rows processed | 282,309 |
| Events | 171,419 |
| Ordinary observations | 78,238 |
| Outcome rows | 1,497,942 |
| Total detection + labeling runtime | 234.471 seconds |
| Peak process RSS (macOS bytes) | 1,026,310,144 |
| Parquet artifacts | 189,936,914 bytes |
| Filtered page query | 0.1585 seconds |

Local reproducibility artifacts: `work/research-v2-release-benchmark/` (ignored).
No predictive performance conclusion is drawn from these engineering counts.

## Verification

| Suite | Unique passing tests |
|---|---:|
| Legacy outputs/tests | 156 |
| Engine/SDK/research tests | 154 |
| Backend/API/migration tests | 68 |
| Frontend components | 16 |
| Browser end-to-end | 8 |
| **Total** | **402** |

The combined Python run passed 219 tests before the final three targeted test additions;
all additions passed in focused runs, totaling 222 engine/backend tests. Final partial-chart
changes passed 46 relevant tests and an explicit API fill-marker/target assertion. Existing
legacy goldens passed in the combined run. New columnar artifacts reproduced byte-for-byte.
No test was skipped to obtain the reported golden matches.

Frontend production build passed. Remaining build warning: the existing Monaco-heavy bundle
is large (about 4.2 MB uncompressed); code splitting is a future performance refinement.
A Starlette/httpx deprecation warning remains; it did not cause test failures.
Browser workflows used isolated LAB_STORAGE, never cleared normal user storage, and covered
legacy workflows plus v2 numeric/compound/ATR/chart queries and 2020 multi-trade/partial runs.
Screenshots were visually inspected; the weighted-exit chart issue found there was corrected.

## Installation and use

```sh
./scripts/install.sh
./run_app.sh
```

Open http://127.0.0.1:5173 ; API documentation http://127.0.0.1:8000/docs .
Backend and frontend bind localhost. The updated application was started and health checked.
No authentication/public hosting was added. Only run strategy code you trust; subprocess
isolation and timeouts are not a secure Python sandbox.

## Limitations

- Sequential positions only; no overlapping positions, hedging or portfolio risk allocator.
- Explicit leg quantities must match sized entry quantity; no automatic fractional allocation.
- Indicator chart lines are confirmation snapshots, not historical indicator curves.
- Source Parquet frames still occupy memory; output rows and exports are batched/columnar.
- Date bootstrap assumes approximately independent dates, treats baseline estimates as fixed,
  and does not correct every exploratory query ever made. BH applies to displayed groups.
- Old sealed studies retain strict original engine identity checks; labeling them requires
  the original frozen checkout. The upgrade does not bypass protection or relabel old data.
- Session VWAP is same-date only; a timeframe misaligned with its start yields unavailable
  VWAP. Missing input data is never silently filled.
- The chart compatibility target field remains informational for advanced plans;
  `target_legs` and partial-fill history are authoritative.
- Research advanced mechanical settings use explicit JSON plus generated numeric controls;
  specialized visual editors for every mechanical option are not yet provided.

## Local commits

```text
55815d5e3406b8161b53f7fd11622e485362834b Add opt-in research execution profiles, causal features and sequential position plans
b9849381c783fd11a7873cef946b478b280ff47f Add immutable columnar event research, compound sequences and clustered evidence
ddf585a5e787aeef0554ff2b94a8273fac80e238 Integrate research console, execution controls and partial-fill inspection
```

The audit-document commit follows these implementation commits. Its hash is given in the
final response. Starting remote-tracking HEAD remains 653bb92; no push was performed.

## Changed files

```text
M	backend/app/charts.py
M	backend/app/db.py
M	backend/app/event_studies.py
M	backend/app/experiments.py
M	backend/app/main.py
M	backend/app/services.py
M	backend/requirements.txt
M	backend/tests/test_event_studies.py
M	backend/tests/test_experiments.py
A	backend/tests/test_research_upgrade.py
M	docs/ARCHITECTURE.md
M	docs/BACKTEST_ASSUMPTIONS.md
M	docs/DEVELOPMENT.md
A	docs/EXECUTION_EXTENSIONS.md
M	docs/LEVEL_RESEARCH_FOUNDATION.md
M	docs/MANAGEMENT_API.md
A	docs/PLATFORM_UPGRADE_PLAN.md
M	docs/RESEARCH_SPLITS.md
A	docs/RESEARCH_V2.md
M	docs/STRATEGY_API.md
A	engine/execution_profiles.py
A	engine/extended_runner.py
A	engine/features.py
A	engine/partial_execution.py
A	engine/position.py
A	engine/reporting.py
A	engine/research/chart_context.py
A	engine/research/columnar.py
A	engine/research/indicators.py
A	engine/research/numeric.py
A	engine/research/queries.py
A	engine/research/sequences.py
A	engine/research/statistics.py
A	engine/research/structure.py
M	engine/research/study.py
A	engine/research/study2.py
A	engine/research/zones.py
M	engine/runner.py
M	engine/strategy/__init__.py
A	engine/timeframes.py
M	frontend/src/App.tsx
M	frontend/src/EventStudies.tsx
A	frontend/src/ExecutionSettings.tsx
M	frontend/src/Experiments.tsx
A	frontend/src/NumericResearch.tsx
M	frontend/src/TradeInspector.tsx
M	frontend/src/style.css
M	frontend/tests/levels-e2e.spec.ts
A	frontend/tests/upgrade-components.test.tsx
A	frontend/tests/upgrade-e2e.spec.ts
A	tests/test_execution_profiles.py
A	tests/test_extended_execution.py
A	tests/test_platform_extensions.py
A	tests/test_research_extensions.py
A docs/PLATFORM_UPGRADE_COMPLETION.md (this audit)
```

## Preservation and safety confirmation

Existing market files, historical outputs, source strategy versions, saved records and
artifact references were preserved. All profile hashes equal the initial audit identities.
Normal storage was backed up, migrated additively, and compared row-for-row with its latest
backup. No existing sealed study or reveal record was changed. Automated reveal tests used
isolated state and synthetic outcome placeholders or already-visible 2024 fixture dates.
No new live OOS outcome research or interpretation occurred. Credentials/.env were not read,
printed, changed or committed. No paid data was downloaded. Data and storage remain ignored.
No strategy optimization or recommendation was performed. Nothing was pushed.
