# Strategy Research Lab v1.1 — completion report

Starting commit: `ca000c837dd1f56b9a38efbc7d5d71135e52168d`.
Implementation is complete locally; no push performed. The final documentation commit is
identified in the delivery message (a commit cannot contain its own hash).

## Delivered architecture and files

The React/FastAPI/SQLite platform is extended in place. Original market-data, FVG,
lifecycle and CONT-A runners under `outputs/` were not edited. The fixed-bracket executor
remains the default, with an explicitly selected managed executor alongside it.

New principal modules:
- `backend/app/charts.py`, `versions.py`, `experiments.py`.
- `engine/managed.py`; additions to SDK, loader, runner and worker configuration.
- `strategies/builtins/cont_a_rstep.py`.
- `frontend/src/TradeInspector.tsx`, `VersionBrowser.tsx`, `Experiments.tsx`.
- Chart, management, version, experiment, component and browser tests.
- `docs/V1_1_PLAN.md`, `TRADE_INSPECTOR.md`, `MANAGEMENT_API.md`, `RESEARCH_SPLITS.md`;
  updated README, architecture, SDK, assumptions and development guides.

## Candlestick Trade Inspector

Click a Trade Explorer row to open the large inspector panel. Select 30-minute,
60-minute or full New York calendar-date context; move previous/next with buttons or
arrow keys. Existing table filters survive returning to the table. Navigation uses the
whole selected run, not only filtered rows.

[Lightweight Charts 5.2](https://tradingview.github.io/lightweight-charts/docs/5.0)
provides interactive candles. UTC remains the data clock; labels use America/New_York.
Generic overlays support boxes, horizontal lines, vertical/point markers and labels.
Built-ins show FVG where applicable, entry, original stop, target, exit and managed stop
segments beginning at activation. Non-FVG strategies can provide annotations through
entry metadata. Prices and timestamps are checked against source Parquet in tests.

API: `GET /api/backtests/{run_id}/trades/{trade_id}/chart?window=30|60|session`.
The old candles endpoint remains compatible. Windowed reads avoid sending entire datasets.
Annotation coordinates interpolate between integer chart indices to align one-minute events
with five-minute candles. Full session means NY calendar date, not a newly invented CME day.

## Management API and exact causality

Strategies optionally implement `manage(ctx, params)` and return `MoveStop`, a list of
requests, or None. Frozen context contains owned confirmed minute, optional complete
five-minute candle, original risk, fixed target, active stop, MFE/MAE and immutable stop
history. It exposes no future bars. A fresh manager per trade prevents future signal-scan
state from leaking into management. Trusted Python is not securely sandboxed.

For each owned minute, resolve the active stop/target first, conservatively stop-first on
conflict, then session close. Exited trades receive no callback. Survivors receive the
minute-close event and, when available, complete-five-minute-close event. Both see the same
pre-update state. Select the most protective valid request. Round outward to MNQ ticks;
reject nonfinite, loosening or at/beyond-target requests. Equal-stop requests are no-ops.

A requested stop activates at the NEXT minute start: the same instant as the prior minute's
close, never within the interval that produced the request. Adverse opening gaps use the
existing execution convention. Targets never move. Full exit-minute MFE/MAE remains unchanged.
Missing owned execution minutes fail the run; incomplete 5m candles cannot create hold events.

Events record observed minute start, confirmation, activation, previous/requested/effective
stop, trigger, reason and metadata. Management version is `minute-close-next-start-v1`.
Events are saved per run and available through the management-events API and inspector.

## Exact reference R-Step experiment

CONT-A Quality entry eligibility is unchanged: risk <100, exclude 10:00–10:29 trigger starts,
fixed original 2R, one MNQ, zero costs. After a surviving +50-point touch, request +5 points.
A later whole candle must start at/after that activation. Strict whole-candle holds beyond
1R, 1.5R and 1.75R request stops at +1R, +1.25R and +1.5R. Simultaneous qualifications
compete for the most protective stop. No threshold optimization was performed.

Full local historical results, 2024-01-01 through exclusive 2026-10-06:

| Metric | Fixed 2R Quality | R-Step |
|---|---:|---:|
| Trades | 170 | 170 |
| Winners / losers | 73 / 97 | 96 / 74 |
| Win rate | 42.94% | 56.47% |
| Net USD | $4,242 | $1,261 |
| Profit factor | 1.416270 | 1.166623 |
| Average trade | $24.95 | $7.42 |
| Average R | 0.234810 | 0.127229 |
| Total R | 39.9177 | 21.6289 |
| Gross profit / loss | $14,432.50 / $10,190.50 | $8,829 / $7,568 |
| Max closed-trade drawdown | $1,570 | $1,665 |
| Longest losing streak | 10 | 5 |
| Average duration (minutes) | 79.83 | 45.42 |
| Long / short P&L | $2,890 / $1,352 | $1,304.50 / -$43.50 |

R-Step generated 122 stop-update events and 60 managed-stop exits. Its higher win rate
came with $2,981 less net profit and $95 greater maximum drawdown. It did not improve this
historical comparison. Counterfactual profit-protected is null rather than fabricated.

Saved live runs, visible in Runs and Compare:
- Fixed 2R: `71d54a8cfec54ab191e7035d0ba64e57`.
- R-Step: `8825486834df4c1ab5ae7792e77b57bd`.

The saved fixed-run trade fingerprint exactly matches the original Quality golden fixture.
The final managed economic-result digest is
`1f6f0c22a53d6bddec7cc1fd401cdedb13cca646068ebaa74e813cdfb88300a6`.
Repeated managed runs are also checked in the automated suite.

## Immutable source versions

The Strategies page offers Code, Versions, Runs and Variants. The version browser displays
exact source, identity, related runs/variants and read-only Monaco side-by-side diffs.
Clone creates a separate strategy from the selected historical source. Restore appends a
new current version; it never overwrites history, including when restoring current source.
Saved runs link to their exact source version. Database triggers protect source immutability.

## Research splits, freeze and OOS

Research splits store development, validation and OOS ranges plus description and warnings.
All dates are start-inclusive/end-exclusive. Overlap and invalid ranges are rejected; gaps
are disclosed. One-day ranges require the following date as end. Defaults partition the
available period at 2026-01-01 and 2026-07-01.

Experiment creation captures immutable source/version/hash, resolved parameters, settings,
ranges, data/engine identity and management version. Development precedes validation.
Freeze requires successful development and validation plus unchanged identities. Explicit
Run/Reveal OOS requires freeze and records audit timestamps. No OOS run is created before
that action, so the UI cannot accidentally display precomputed OOS performance.

Each segment is a separate labeled run. Combined reporting includes only revealed completed
segments. Draft configurations are also immutable: create a new experiment to change them.
Frozen OOS is a research workflow guard, not an access-control boundary for the machine owner.

Sweeps default to development. Validation requires explicit advanced intent; official OOS
sweeps are rejected. Unscoped legacy sweeps cannot overlap frozen OOS; intentional future
research requires a new profile. Comparisons warn about different source, management,
segments, date ranges, data and engine identities. Cloned experiment runs become AD_HOC.

## Database migration and preservation

Migration 3 adds `research_splits`, `experiment_snapshots`, `experiment_runs` and immutable
record triggers. It is additive and idempotent; no reset is required. The original database
was backed up online to ignored `work/v11-before.db`. Migration tests operate on a copy.

At final inspection the live database had already migrated and contained additional user
research. It was not replaced or restarted. Every original row in strategies (1), versions
(1), variants (3), runs (3), metrics (3), and artifact references (15) compared equal with
the pre-task backup. Newer user strategies/runs were retained. Two verification runs were
then appended. Existing data/result files remain unchanged and ignored.

## Verification

Before implementation: 207 passing tests. After implementation: **285 passing**, 78 added.

| Suite | Passing |
|---|---:|
| Original legacy tests | 156 |
| Python platform/backend | 113 |
| Frontend components | 11 |
| Browser end-to-end | 5 |
| Total | 285 |

The 113 Python tests include 37 management, 6 chart, 8 version and 18 experiment tests,
plus existing SDK/backend and four full-data golden/determinism checks. All three original
reference configurations reproduce exact trade fingerprints and metrics: baseline 263/$525.50,
risk100 235/$4,277, Quality 170/$4,242. Disabled management reproduces fixed execution.

Browser tests cover existing platform workflows plus managed candles/activation overlays,
version diff/clone/restore, and development/validation/freeze/OOS. Screenshots were inspected
locally; generated market-data images are not committed. Production build passes. Production
npm dependency audit reports zero vulnerabilities. Nonblocking warnings: large Monaco bundle
and a TestClient dependency deprecation. Relevant logs are retained in ignored work/.

Both live listeners are 127.0.0.1. Ignore checks cover .env, local Parquet and SQLite. No
credentials or downloaded market data are included in these commits. Unrelated untracked
user scripts appeared during development and are deliberately left untouched; the tracked
task changes are committed rather than deleting user work to make status appear empty.

## Install and launch

```sh
./scripts/install.sh
./run_app.sh
```

Open http://127.0.0.1:5173; API documentation: http://127.0.0.1:8000/docs.
The existing local service is running. Do not launch a second instance on occupied ports.
Python 3.13 and Node 22+ are documented; verification used Node 24.3. Existing authorized
local market data is required. No Databento download or API key is needed by the app.

## Limits and recommended v1.2

Inspector is a large panel rather than a deep-link route. Execution profile remains MNQ,
5-minute signals/1-minute fills, one daily entry. Partial exits, alternative management timing,
additional instruments, multi-parameter sweeps and automatic engine-environment restoration
are not implemented. Historical source is retained, but reconstructing an old engine runtime
still requires its Git/dependency environment. Python remains trusted-user execution only.

Recommended next: portable research-workspace archive/restore with pinned engine environment,
inspector deep links, and more compact management-event audit tables. Preserve the existing
regression fixtures before expanding execution profiles; no automatic optimization is proposed.

## Local commits

1. `0a0f8103f2b79cd6e8ce0855cc3a46c260003b82` — candlestick inspector and annotations.
2. `467b1aa323c936b597b6fa8d6efb455017a16cac` — causal management and synthetic tests.
3. `a300cf36ef0b79fddd7260d7025dcf18666bae3f` — persistence, versions and frozen experiments.
4. `80835537c735a2094ce9d8cba1fe5712669b0222` — integrated version and OOS UI.
5. Final documentation/verification commit: see delivery message and local Git log.

No commits pushed for this task.
