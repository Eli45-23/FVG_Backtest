# Simple MNQ search without the prior account restrictions

Frozen before outcomes. DEVELOPMENT_ONLY_NOT_VALIDATED. Scope: 2020–2023 only.
The user's latest instruction removes $500 capital, $75 risk, $100/day and
one-trade/day constraints. One micro throughout isolates price-rule expectancy.
No affordability claim. No Validation/OOS outcome access. No paid download.

Exactly twelve hypotheses, fixed 2R target, no parameter grid:
- TWO_PUSH, OUTSIDE_REVERSAL, INSIDE_BREAK: exact detector definitions from v1.
- PULLBACK_RESUME, RANGE_FAILURE, THREE_BAR_BREAK: exact definitions from v2.
  These are new execution policies on previously tested signals, not new independent
  hypotheses. No dollar risk/reward filter, no daily lock.
- OPEN_MOMENTUM_15: at09:45, buy if complete09:30–09:45 close>open, sell if<open.
  Stop beyond opposite opening-range wick byone tick. Doji has no entry.
- OPEN_FADE_15: same opening observation, opposite direction. Same structural stop.
- EMA20_CROSS: RTH EMA20 of complete5m closes, seeded with first close; require21
  contiguous bars. Long when previous close<=previous EMA and current close>current
  EMA. Short mirrors. Stop beyond current candle opposite wick byone tick.
- EMA20_PULLBACK: previous close>previous EMA; current low<=previous EMA, current
  close>current EMA and current open, and EMA rising. Long; short mirrors all.
  Stop beyond current candle opposite wick byone tick. Uses just one indicator.
- CHANNEL12_BREAK: close strictly outside previous12 complete5m candle high/low
  range, trade that direction. Stop beyond opposite12-bar range edge byone tick.
- CHANNEL12_RECLAIM: current candle sweeps one previous12-bar range boundary and
  closes strictly inside, without sweeping other boundary. Fade the sweep.
  Stop beyond current candle opposite wick byone tick.

Missing/incomplete bars reset detection continuity and EMA warmup. Opening setup
requires all three opening candles, no fallback. Everything is RTH/full XNYS
sessions, no holidays/half-days; exit at actual close. Both directions. No time,
year, month, weekday or regime filters. No management. Entry at confirmed close,
then use only subsequent1m bars. Stops one tick outward, targets original2R.
Entry/exit1adverse tick primary,0/2 sensitivities. Actual userfees .73/side.
Stop-first ambiguity and native adverse gap behavior unchanged. Reject only
nonpositive risk. All other raw signals kept in audit; skip while position active.
Reenter only from a NEW confirmed signal, including a signal confirmed exactly at
recorded previous exit time. No queuing skipped signals. No overlapping positions.
Missing owned minute leaves that trade unknown and suppresses later same-day
selection because flatness is unknown; next session starts flat under no-overnight
contract. Aggregate returns remain incomplete, not zero-filled, if any such case.

Evidence standard frozen before inspection:
- Positive total net dollars AND average net R afterprimarycosts; PF>1.
- At least200 completed trades and200 distinct dates.
- Positive net in >=3/4 Developmentyears; no year>50%sumpositiveyearprofits.
- Positive net afterremoving top5 profitable dates (robustness, NOT an eligibility
  or production filter); positive totalnet at2tickcoststress.
- Calendar-monthblock bootstrap of alldailyreturns:5000draws,seed1729; lower95%CI>0.
  One-sided centeredbootstrap p, Holm over12new policies PLUS6previous capped
  policies=18tests. This is not correction for all historic repository research.
- Complete known execution, exact independent fills and deterministic rerun.
A pass is PROMISING_DEVELOPMENT_ONLY, never 'proven consistent/live-ready'. No
positiveclaimwithunknownexecution. Reporteveryyear, losingdays, worstday, drawdown,
long/short, fees, risk, tradecounts and same-minuteambiguity.

Stop after this complete registered family; do not repeatedly alter definitions
until one passes. Later research requires a separately documented rationale and
all failedtrials remainvisible. AllDevelopmentdataalreadyinspected; honest later
validation cannot be replaced by a search result. No automaticdeployment.
