# MNQ four-hour bar contract V2

Profile: `CME_GLOBEX_4H_SESSION_ANCHORED_V2`, backed by
`MNQ_GLOBEX_HISTORICAL_SESSION_CALENDAR_V1`. This opt-in module leaves
`engine/zone_v2/frames.py`, provider thresholds, old artifacts, strategy fills and
normal application defaults unchanged. See [calendar provenance](MNQ_HISTORICAL_SESSION_CALENDAR.md).

## Exact construction

Raw Databento `ts_event` is a minute start. OHLC fixed-point integers are reduced
before division by 1e9. Open is first, high maximum, low minimum, close last,
volume integer sum. Buckets are left-inclusive/right-exclusive and become known
only at their scheduled end. No missing candles are synthesized.

Known sessions start at 18:00 New York. Full buckets start 18:00, 22:00, 02:00,
06:00, 10:00; the remaining segment starts 14:00 and ends at the documented
close. An earlier official close may truncate an earlier bucket instead. The
historical pause is subtracted from expected minutes, not filled. DST is handled
by timezone-aware session opens (the transition itself occurs on the closed
weekend). A full bucket means four elapsed hours, not merely 240 observations.

Each inventory row carries session label/ID, bucket start (`timestamp`), scheduled
end (`availability_timestamp`), last observed minute, OHLCV, full/shortened flag,
expected/observed/missing/unexpected counts, completeness, official schedule and
bar-profile versions, coverage status, exclusion reason, stable bar ID, ATR count
and eligibility. `official_expected_minutes` is null for unknown sessions;
`expected_minutes` there is only the nominal diagnostic count.

Completeness requires a resolved schedule, exactly the expected minute set and
valid tick-aligned OHLC. Duplicate or off-grid source timestamps fail construction.
A minute in a documented pause makes that bucket incomplete even when no expected
minute is absent. Such a minute is never used to assert different official hours.
Empty buckets have absent OHLC and are audit records, not synthetic price bars.
Shortened buckets can be coverage-complete but cannot form zones.

## ATR and formation timing

The unchanged V2 rule is SMA14 of true range over eligible complete full bars.
True range references the previous eligible full close. Scheduled maintenance,
weekends and complete abbreviated segments preserve the rolling state; shortened
segments do not contribute TR and clear pending formation sequences. An unexpected
incomplete bucket or unresolved session resets ATR and clears formation. Recovery
requires fourteen subsequent eligible full bars. A gap does not get an invented TR.

No December 2019 data exists locally. Warmup remains unavailable until sufficient
2020 observations exist. In this audit:

- first accepted full bar closes January 2, 2020 at 22:00 New York;
- first ATR14 is known January 7 at 10:00 New York;
- earliest theoretical one-base/one-departure confirmation following that ATR is
  January 7 at 14:00 New York, conditional on frozen formation criteria;
- first actual new-profile zone confirms January 8 at 10:00 New York.

The initial unavailable sessions are recorded separately from later continuity
resets in the foundation summary. Missing warmup is an explicit limitation, not
a provider defect.

## Lifecycle and causality

Formation uses only complete full 4h bars and their then-known ATR. The unchanged
provider consumes closed buckets sequentially. Lifecycle uses complete 5m bars
inside resolved official intervals, including valid 5m observations within an
otherwise incomplete 4h bucket. Unknown official hours are masked and treated as
coverage uncertainty. They are not misrepresented as a scheduled market closure.
Four-hour invalidation still requires complete full bars. No future outcomes,
returns, excursions or threshold-hit labels are calculated by this engineering run.

## Identity and acceptance

Session and bar IDs include the calendar profile hash. Zone IDs include the new
frame identity, so even economically unchanged zones receive new IDs. The mapping
export links old/new IDs by zone type, formation time and base candle timestamps.
Source file hashes are recorded separately. Legacy artifacts retain their identities.

Independent raw-integer reductions check every inventory row; accepted bars must
agree exactly on OHLCV, interval, count and completeness. Full-pipeline canonical
hashes must match on rerun. Human readiness applies only to the resolved,
complete-full-bar subset, with excluded sessions visibly identified. It does not
certify discretionary zone semantics. The provider remains
`PROVISIONAL_PENDING_HUMAN_GROUND_TRUTH`; predictive research stays prohibited.
