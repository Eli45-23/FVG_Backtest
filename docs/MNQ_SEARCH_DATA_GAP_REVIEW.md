# Unrestricted search: unresolved March 18, 2020 execution interval

The strict original run remains unchanged and incomplete where a selected trade
owns absent minutes. This investigation is data quality work, not a strategy
filter or a changed fill assumption.

Reading the existing local 2020 DBN archive (349,541 rows) confirms there is no
12:58 New York record on 2020-03-18. The last record before the gap starts12:57;
the next starts13:11. Thus the missing 12:58–13:10 minutes are absent in the raw
archive too; they were not merely lost during conversion to Parquet. No file was
modified and no paid data was downloaded.

There is relevant official historical evidence:

- [NYSE/SRO Market-Wide Circuit Breaker Working Group report, March31,2021](https://www.nyse.com/publicdocs/nyse/markets/nyse/Report_of_the_Market-Wide_Circuit_Breaker_Working_Group.pdf), pages5and7–8, gives the March18 cash-market halt as12:56:17–13:11:17 ET and discusses the subsequent October2020 change to futures reopening timing.
- [CME SER8567, March19,2020](https://www.cmegroup.com/notices/ser/2020/03/SER-8566/SER-8567.pdf) describes contemporaneous coordinated futures reopening and an April2020 amendment concerning Level3 halts.

Accessed2026-10-10. These sources establish a historical halt context, but this
review does NOT certify the exact MNQ instrument-status sequence. The observed
12:56/12:57 bars must be reconciled rather than silently discarded. Current CME
FAQ reopening rules must not be applied retroactively to March2020.

Consequently the production engine's missing-minute exception is preserved. No
synthetic candles, forward fill, inferred fills or exclusion of the signal are
introduced. The research screen cannot claim a complete result until a separately
versioned, authoritative instrument/session treatment is established and tested.

For CHANNEL12_BREAK, the primary unresolved short entered2020-03-18 at11:05 ET,
entry7153.00, stop7325.25, target6808.50. It was selected causally; its future gap
was not used to reject entry. Subsequent same-day eligibility remains unresolved.
Other affected policies are also retained, not selectively repaired for this lead.
