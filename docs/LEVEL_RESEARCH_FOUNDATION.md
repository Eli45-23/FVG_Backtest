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
  observations), matched by year, 30-minute NY confirmation-time bucket and causal ATR14 bucket.
  Fixed point buckets are <10, [10,25), [25,50), >=50, and unavailable. Direction is
  matched at analysis time. Each event receives equal weight across its matched baseline;
  repeated baseline observations are disclosed, not represented as independent sample size.
  No random seed, ML, volatility optimization or strategy selection. Bucket boundaries are
  documented fixed measurement choices, not optimized values.

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

## Public level/zone API

Ordinary strategies can import `LevelEngine`, `SessionConfig` and `Zone` from
`engine.research.levels`. For a complete confirmed ordinary SDK bar:

```python
# In Strategy.__init__:
self.levels = LevelEngine(SessionConfig())  # PM deliberately disabled

# In Strategy.on_bar(ctx, params):
known_levels = self.levels.on_bar(ctx.bar)
```

The adapter returns levels known at that bar's close. EventDetector instead checks levels
available at bar START so source-candle price activity cannot create a retroactive event.
The regular SDK still supplies legacy data and dates; selecting a research profile does not
extend trading-strategy availability. To use early-history data in strategy backtests would
be a separate future engine-profile change. Zone has no automated detector or implicit
supply/demand interpretation.

Calendar sessions and exchange_calendars version are frozen into each study configuration,
including a schedule hash. Repeated study outputs use that schedule rather than silently
adopting a later library calendar update. ATR is the 14-bar mean true range after 14
consecutive complete 5m bars, reset at gaps; it is descriptive and not an eligibility filter.

### Provider for the existing strategy callback schedule

The legacy executor intentionally calls strategies only within its established session
window; it omits premarket and the candle closing at 16:00. That behavior is preserved.
Use the provider below rather than feeding only `ctx.bar` if PDH/PDL or PM levels are needed:

```python
from engine.research.provider import CausalLevelSource
from engine.research.levels import SessionConfig

# Strategy.__init__ (legacy input profile is the default):
self.level_source = CausalLevelSource.from_profile(config=SessionConfig())

# Strategy.on_bar:
levels = self.level_source.at(ctx.timestamp)
```

The provider advances its private source iterator only through candles whose close is at or
before the requested timestamp. It includes bars omitted by strategy callbacks. Its public
API exposes immutable currently available levels, not future source bars. Calls must use
nondecreasing aware timestamps. `identity` exposes the selected profile hashes for audit.
As everywhere else, arbitrary trusted Python can inspect private objects or read files;
this protects the intended API against accidental lookahead, not malicious source code.

## Persistence, API and operation

Migration **4** adds only `event_studies` and `event_study_reveals`, plus triggers protecting
study config/hash and immutable reveal records. Existing tables and artifacts are retained.
The online pre-migration backup is local `work/levels-before.db`. The prior migration test
now expects schema 4; its exact old-row preservation assertions remain intact.

Immutable config includes profile/file hashes, source row counts, study code fingerprint,
explicit session/rejection settings, segment/date range, outcome resolution, baseline
matching method and frozen exchange calendar. Artifacts live under ignored
`storage/event_studies/<id>/`: config, detections, ordinary observations, outcomes and
baseline outcomes. Files are created exclusively, never overwritten through the app.
CSV is a deterministic export with per-event outcomes JSON; full JSON includes config,
all events/labels and matched-baseline source observations/labels.

Study jobs run sequentially in a separate subprocess queue, with cancellation and a one-hour
limit. Errors do not crash FastAPI. Restart marks interrupted jobs failed; create a new study
to retry. An audited reveal cannot be undone; a failed reveal remains recorded. No pending
OOS labels are computed before reveal. Raw files remain accessible to the trusted local user.

Endpoints under `/api/level-research`:
- `GET /profiles`: profile range, row counts and SHA-256 identities.
- `GET/POST /studies`: list/create immutable studies.
- `GET /studies/{id}`: status, config, reveal timestamp and outcome availability.
- `POST /studies/{id}/cancel`: cancel queued/running work.
- `POST /studies/{id}/reveal`: explicit irreversible OOS reveal and label computation.
- `GET /studies/{id}/events`: paginated detection metadata with seven UI filters.
- `GET /studies/{id}/summary`: horizon/directional view, probabilities, matched baseline,
  excursion distributions and grouped results. Sealed OOS returns 409.
- `GET /studies/{id}/export?format=json|csv`: immutable result export; sealed OOS returns 409.
- `GET /studies/{id}/events/{event_id}/chart`: source candles/level/event annotations.
  Sealed charts end at confirmation. Lines begin no earlier than level availability.
  Changed source hashes prevent reconstruction from mismatched data.

Dates are NY calendar dates, with exclusive ends. The UI names segments explicitly, allows
level/class/approach direction/touch count (including 3+)/time/year/weekday filtering, and
provides continuation vs rejection MFE/MAE. Probabilities use fractions from 0 to 1. Baseline
comparisons use only the selected study's observations; event filters select events, while
baseline matching retains ordinary observations from the same frozen study range.

## Limits, not hidden assumptions

This foundation measures RTH interactions (including actual XNYS half-days), not overnight
interactions. PM extremes may derive from the explicitly configured premarket window, but
interaction detection begins at RTH. Sessions with incomplete source coverage do not acquire
complete-session levels. The dataset's earliest day may lack a prior-session level because
no pre-2020 source is present. Touch/reclaim/rejection classes intentionally overlap.

No inference of intraminute ordering, transaction-cost simulation, trade sizing, strategy
optimization, significance testing or machine learning occurs. A rejection is the documented
mechanical proxy, not a claim of profitable confirmation. Supply/demand detection is pending.

Events are paginated in the UI, but stored JSON and aggregate queries are loaded in memory.
Long multi-year studies may use substantial memory and artifacts; all-years throughput has
not been benchmarked. The one-hour worker cap fails explicitly, without silently sampling.
Use date-bounded studies for review. A future columnar/query store can improve scale without
changing the frozen event definitions. No change is required to the existing execution engine.

## Verification commands

```sh
work/.venv/bin/python -m unittest discover -s outputs/tests
work/.venv/bin/python -m pytest tests backend/tests -q
npm --prefix frontend test
npm --prefix frontend run build
# Browser tests should use fresh, separate LAB_STORAGE; never reset user storage.
LAB_STORAGE="$PWD/work/browser-storage" ./run_app.sh
npm --prefix frontend run e2e -- --workers=1
```

Alternate test ports are supported by `LAB_TEST_API_PORT` in Vite and `LAB_TEST_URL` in
Playwright. Defaults remain localhost 8000/5173. A reused browser-test workspace can contain
duplicate named fixtures; use a new test directory instead of deleting user research.


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
