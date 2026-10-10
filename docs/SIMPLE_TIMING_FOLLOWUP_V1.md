# Separately registered timing follow-up

DEVELOPMENT_ONLY_NOT_VALIDATED. This is a later exploratory family, not part of
or an amendment to the frozen twelve-policy study. Rationale is external to its
results: Gao, Han, Li and Zhou, Market Intraday Momentum,
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866 (accessed2026-10-10),
studied S&P500ETF morning-to-final-half-hour predictability. Their overnight-
inclusive return definition differs from simply measuring from today's open.
This is an MNQ adaptation with a structuralstop, not an exact paper replication.
No evidence of ETF results is assumed to transfer to MNQ.

Two definitions only:
1. LAST30_RTH: direction is sign of today's09:55bar close minus09:30bar open.
2. LAST30_OVERNIGHT: direction is sign of today's09:55bar close minus the immediately
   prior XNYSsession's final5m close. Missing previoussession close => no signal.

Require all6opening5mbars complete and contiguous. Enter at15:30 on the confirmed
15:25candle close, long forpositive signal, short fornegative, no trade forzero.
The6complete15:00–15:30bars set stop: their lowestlow−.25 long, highesthigh+.25 short.
No profit target. Exit at stop or16:00, via existing no-target PositionPlan.
No management. No timeframe, entrytime, stopwidth or target optimization.
Full XNYSsessions only; one micro; actual.73fees/side;1adversetick/side primary,
0/2coststress. No account or dollar-risk cap. Development2020–2023 only.
All1000fullsessions count in averages. No future missingness entry filter.

Same evidence gates as the unrestricted search, adjusted over ALL20policies:
6previouscapped+12unrestricted+2timing. Calendar-monthbootstrap5000draws seed1729.
No later period accessed. Everyfailedhypothesis retained. No automatic additional
family after this follow-up. A pass remains only PROMISING_DEVELOPMENT_ONLY.
