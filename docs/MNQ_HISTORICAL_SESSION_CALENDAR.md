# Historical MNQ session calendar V1

This is an additive, Development-only engineering profile, not a replacement for
legacy backtests or the previous zone candidate. Provider acceptance remains
`PROVISIONAL_PENDING_HUMAN_GROUND_TRUTH`. No forward outcomes are calculated.

## Scope and identities

`MNQ_GLOBEX_HISTORICAL_SESSION_CALENDAR_V1` covers civil segment labels from
2020-01-01 through 2023-12-31. `engine/session_calendar/mnq_v1.py` is the source;
`profile()` returns the canonical SHA-256 of its frozen conventions, exception
registry, provenance and unresolved review dates. The frozen local artifact also
records the `research_2020_2026` source identities. Price rows are read only within
Development; hashing an existing whole source file identifies it without querying
reserved outcomes.

A civil segment label is the New York date on which a session segment ends. It is
not always the CME exchange trade date. Verified holiday segments carry their
exchange trade date separately. Unknown dates have no asserted exchange trade
date or official open/close.

## Exchange evidence (accessed 2026-10-08)

- [CME launch advisory 19-118](https://www.cmegroup.com/content/dam/cmegroup/notices/clearing/2019/04/Chadv19-118.pdf)
  explicitly includes MNQ: regular Sunday–Friday 17:00–16:00 Chicago time,
  daily maintenance 16:00–17:00, and the historical 15:15–15:30 equity pause.
- [SER-8788R, section 5](https://www.cmegroup.com/content/dam/cmegroup/notices/ser/2021/06/SER-8788R.pdf)
  removes that equity pause effective June 28, 2021.
- [SER-8887](https://www.cmegroup.com/content/dam/cmegroup/notices/ser/2021/12/SER-8887.pdf)
  establishes Juneteenth observance from 2022. It does not establish intraday hours.
- [Good Friday 2023](https://www.cmegroup.com/files/good-friday.pdf): April 7
  equity close 08:15 Chicago / 09:15 New York; April 6 regular close.
- [Juneteenth 2023](https://www.cmegroup.com/trading-hours/files/juneteenth-2023.pdf):
  June 19 halt 12:00 Chicago / 13:00 New York, reopen 17:00 Chicago;
  June 20 regular close. Both segments have June 20 exchange trade date.
- [July 2023](https://www.cmegroup.com/trading-hours/files/4th-of-july-2023.pdf):
  July 3 close 12:15 Chicago / 13:15 New York; July 4 halt 12:00 Chicago,
  reopen 17:00; July 5 regular close. July 4/5 segments share July 5 trade date.
- [Thanksgiving 2023](https://www.cmegroup.com/trading-hours/files/thanksgiving-day-2023.pdf):
  November 22 regular, November 23 halt 12:00 Chicago, reopen 17:00;
  November 24 close 12:15 Chicago. November 23/24 share November 24 trade date.

Chicago and New York observe the same US DST transition dates. All calculations
use timezone-aware America/New_York, never fixed UTC offsets.

## Incomplete historical evidence — explicit exclusion

The official [2022 index](https://www.cmegroup.com/content/cmegroup/cn-s/tools-information/holiday-calendar.html)
links historical binary spreadsheets and the
[2020](https://www.cmegroup.com/tools-information/holiday-calendar/files/2020-holiday-calendars.zip)
and [2021](https://www.cmegroup.com/tools-information/holiday-calendar/files/2021-holiday-calendars.zip)
archives. Those binaries were not successfully retrieved/inspected. A local
request received a CME access-block response; it is retained as a retrieval-error
JSON, not mislabeled as an archived calendar. No access workaround was used.

For each holiday review date, the preceding and following weekdays are also
quarantined unless an inspected official table resolves them. This deliberately
conservative envelope is **not** a claim that all those days had special hours.
There are 104 unresolved civil dates. In particular Good Friday 2020, 2021 and
2022 remain unresolved. Their full date list and attempted source references are
in `official_session_exceptions.csv`. The whole-period official expected minute
count is null; only the resolved-subset count is asserted.

Outside these envelopes the standing official regular rule is used. Unscheduled
halts, no-trade minutes and vendor gaps are not inferred as new exchange hours.
Additional official notices may require a new profile version. Existing profiles
and artifacts must not be silently rewritten when more evidence becomes available.

## Official hours versus source observations

Regular New York intervals are 18:00 previous civil day to 17:00; maintenance is
17:00–18:00 and the weekend runs Friday close to Sunday 18:00. Before June 28,
2021, expected minutes exclude 16:15–16:30. Early closes come only from the
verified tables above. No schedule function receives source prices.

Unknown sessions retain nominal regular buckets **for diagnostics only**;
`official_open`, `official_close` and official expected counts are null. Such
buckets are never accepted and reset ATR continuity. Observations inside them
are classified unresolved regardless of whether they look complete.

The minute mismatch export distinguishes absent expected minutes, unexpected
observations in known pauses/maintenance, and observations in unresolved sessions.
“vendor/source missingness” is a coverage category, not a finding of vendor fault:
no-trade, halt and vendor causes remain unestablished. Known scheduled exclusions
are not absent expected minutes. Official abbreviations and the historical pause
are independently documented in the session audit; they are not inferred from gaps.

## Reproduction

From the project root:

```sh
work/.venv/bin/python -m scripts.calendar_foundation.audit
work/.venv/bin/python -m scripts.calendar_foundation.charts
```

Review every chart before issuing the readiness JSON. Provider engineering replay
requires the matching reviewed readiness/profile/bar hashes:

```sh
work/.venv/bin/python -m scripts.calendar_foundation.provider_audit
```

These runners target the dedicated engineering directory. Preserve/freeze its
completed manifest before creating any subsequent version. They do not modify
normal application storage or automatically repoint the Zone Labeler.
