"""Evidence-backed intervals, with unknown holiday hours excluded rather than guessed."""

from datetime import date, timedelta
from dateutil.easter import easter
import pandas as pd
from engine.canonical import digest

CALENDAR = "MNQ_GLOBEX_HISTORICAL_SESSION_CALENDAR_V1"
BARS = "CME_GLOBEX_4H_SESSION_ANCHORED_V2"
NY = "America/New_York"
ACCESS = "2026-10-08"
SOURCES = {
    "regular": dict(
        title="CME Micro E-mini launch clearing advisory 19-118",
        url="https://www.cmegroup.com/content/dam/cmegroup/notices/clearing/2019/04/Chadv19-118.pdf",
        notes="MNQ explicitly included: 17:00–16:00 CT, daily 16:00–17:00 break, 15:15–15:30 pause.",
    ),
    "pause": dict(
        title="CME SER-8788R, section 5",
        url="https://www.cmegroup.com/content/dam/cmegroup/notices/ser/2021/06/SER-8788R.pdf",
        notes="Eliminates equity pause effective June 28, 2021.",
    ),
    "juneteenth_rule": dict(
        title="CME SER-8887",
        url="https://www.cmegroup.com/content/dam/cmegroup/notices/ser/2021/12/SER-8887.pdf",
        notes="Juneteenth observed starting 2022; does not establish intraday hours.",
    ),
    "gf2023": dict(
        title="CME Good Friday Holiday Schedule, April 6–7 2023",
        url="https://www.cmegroup.com/files/good-friday.pdf",
        notes="Equities open Thursday 17:00 CT, close Friday 08:15 CT.",
    ),
    "thanks2023": dict(
        title="CME Thanksgiving Holiday Schedule 2023",
        url="https://www.cmegroup.com/trading-hours/files/thanksgiving-day-2023.pdf",
        notes="Equities Thursday halt 12:00 CT, reopen17:00; Friday close12:15. Both segments exchange trade date November24.",
    ),
    "june2023": dict(
        title="CME Juneteenth Holiday Schedule 2023",
        url="https://www.cmegroup.com/trading-hours/files/juneteenth-2023.pdf",
        notes="Equities June19 halt12:00 CT, reopen17:00. Exchange trade date June20.",
    ),
    "july2023": dict(
        title="CME July 4 Holiday Schedule 2023",
        url="https://www.cmegroup.com/trading-hours/files/4th-of-july-2023.pdf",
        notes="Equities July3 close12:15 CT; July4 halt12:00 CT, reopen17:00; July5 regular.",
    ),
    "archive2020": dict(
        title="CME 2020 holiday calendars archive",
        url="https://www.cmegroup.com/tools-information/holiday-calendar/files/2020-holiday-calendars.zip",
        notes="Official link located; contents not retrievable. NOT evidence of exact hours.",
    ),
    "archive2021": dict(
        title="CME 2021 holiday calendars archive",
        url="https://www.cmegroup.com/tools-information/holiday-calendar/files/2021-holiday-calendars.zip",
        notes="Official link located; local fetch blocked. NOT evidence of exact hours.",
    ),
    "archive2023": dict(
        title="CME 2023 holiday processing notice (not intraday hours)",
        url="https://www.cmegroup.com/notices/market-regulation/2022/12/MSN12-13-22.html",
        notes="Holiday review reference only. Exact intraday hours unresolved unless separately verified.",
    ),
    "archive2022": dict(
        title="CME 2022 holiday calendar index",
        url="https://www.cmegroup.com/content/cmegroup/cn-s/tools-information/holiday-calendar.html",
        notes="Holiday dates listed; binary spreadsheets not inspected. Exact hours unresolved.",
    ),
}
for s in SOURCES.values():
    s["access_date"] = ACCESS

# Only manually verified official tables set exception hours. No price-data input.
VERIFIED = {
    "2023-04-06": ("17:00", "gf2023", "2023-04-06"),
    "2023-04-07": ("09:15", "gf2023", "2023-04-07"),
    "2023-06-19": ("13:00", "june2023", "2023-06-20"),
    "2023-06-20": ("17:00", "june2023", "2023-06-20"),
    "2023-07-03": ("13:15", "july2023", "2023-07-03"),
    "2023-07-04": ("13:00", "july2023", "2023-07-05"),
    "2023-07-05": ("17:00", "july2023", "2023-07-05"),
    "2023-11-22": ("17:00", "thanks2023", "2023-11-22"),
    "2023-11-23": ("13:00", "thanks2023", "2023-11-24"),
    "2023-11-24": ("13:15", "thanks2023", "2023-11-24"),
}


def nth(year, month, weekday, n):
    ds = [
        date(year, month, d)
        for d in range(1, 32)
        if d <= pd.Period(f"{year}-{month:02}").days_in_month
        and date(year, month, d).weekday() == weekday
    ]
    return ds[n - 1] if n > 0 else ds[n]


def observed(d):
    return (
        d + timedelta(days=1)
        if d.weekday() == 6
        else d - timedelta(days=1) if d.weekday() == 5 else d
    )


def risk_dates():
    """Conservative review universe, NOT a claim that all these dates are holidays.

    Adjacent weekdays could carry preholiday hours or shifted trade dates; absent
    inspected exchange tables they remain unresolved, even if prices look regular.
    """
    result = {}
    for y in range(2020, 2025):
        days = [
            observed(date(y, 1, 1)),
            nth(y, 1, 0, 3),
            nth(y, 2, 0, 3),
            easter(y) - timedelta(days=2),
            nth(y, 5, 0, -1),
            observed(date(y, 7, 4)),
            nth(y, 9, 0, 1),
            nth(y, 11, 3, 4),
            observed(date(y, 12, 25)),
        ]
        if y >= 2022:
            days.append(observed(date(y, 6, 19)))
        for d in days:
            prev = d - timedelta(days=1)
            while prev.weekday() > 4:
                prev -= timedelta(days=1)
            nxt = d + timedelta(days=1)
            while nxt.weekday() > 4:
                nxt += timedelta(days=1)
            for x in (prev, d, nxt):
                result[str(x)] = str(d)
    return result


def profile():
    p = dict(
        calendar_version=CALENDAR,
        bar_version=BARS,
        timezone=NY,
        anchor="18:00",
        regular_close="17:00",
        historical_pause=dict(
            start="16:15", end="16:30", effective_end_exclusive="2021-06-28"
        ),
        full_starts=["18:00", "22:00", "02:00", "06:00", "10:00"],
        shortened_policy="ineligible_for_formation; preserve_ATR_when_complete",
        unknown_policy="exclude_entire_session_and_reset_ATR; nominal_buckets_diagnostic_only",
        atr="SMA14 full-bar true range, previous eligible full close; missing or unresolved resets",
        civil_session_label="NY date on which segment ends; not necessarily exchange trade date",
        start="2020-01-01",
        end_exclusive="2024-01-01",
        sources=SOURCES,
        verified_exceptions=VERIFIED,
        unresolved_review_dates={
            k: v
            for k, v in risk_dates().items()
            if "2020-01-01" <= k < "2024-01-01" and k not in VERIFIED
        },
    )
    return dict(**p, profile_sha256=digest(p))


def schedule(start="2020-01-01", end="2023-12-31"):
    if not "2020-01-01" <= start <= end < "2024-01-01":
        raise ValueError("Development only")
    risk = risk_dates()
    rows = []
    ph = profile()["profile_sha256"]
    for day in pd.date_range(start, end, freq="B"):
        label = str(day.date())
        verified = VERIFIED.get(label)
        known = bool(verified or label not in risk)
        close = verified[0] if verified else "17:00"
        source = (
            verified[1] if verified else "regular" if known else "archive" + label[:4]
        )
        op = pd.Timestamp(
            str((day - timedelta(days=1)).date()) + " 18:00", tz=NY
        ).tz_convert("UTC")
        cl = pd.Timestamp(label + " " + close, tz=NY).tz_convert("UTC")
        pause = label < "2021-06-28"
        row = dict(
            session_date=label,
            exchange_trade_date=verified[2] if verified else label if known else None,
            open=op,
            close=cl,
            official_open=op if known else None,
            official_close=cl if known else None,
            resolved=known,
            abbreviated=known and close != "17:00",
            pause_start=(
                pd.Timestamp(label + " 16:15", tz=NY).tz_convert("UTC")
                if pause
                else None
            ),
            pause_end=(
                pd.Timestamp(label + " 16:30", tz=NY).tz_convert("UTC")
                if pause
                else None
            ),
            schedule_source=source,
            calendar_version=CALENDAR,
            profile_sha256=ph,
            notes=(
                "Verified exchange table"
                if verified
                else (
                    "Standing regular rule outside holiday review envelope"
                    if known
                    else "Exact holiday/adjacent hours unresolved; nominal interval is diagnostic, not official"
                )
            ),
        )
        row["session_id"] = digest(
            [ph, label, row["official_open"], row["official_close"], known]
        )
        rows.append(row)
    return rows
