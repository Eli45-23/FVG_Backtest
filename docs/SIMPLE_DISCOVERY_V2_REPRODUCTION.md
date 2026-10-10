# Reproducing the second simple-strategy batch

This additive study preserves all v1 artifacts and all production execution code.
The pre-outcome rules were committed as 6824bf6. No rule was changed after results.

Run with the existing local environment:

```
work/.venv/bin/python scripts/simple_discovery_v2/prepare.py
work/.venv/bin/python scripts/simple_discovery_v2/run.py
work/.venv/bin/python scripts/simple_discovery_v2/report.py
work/.venv/bin/python scripts/simple_discovery_v2/verify.py
```

Repeat run/report/verify for byte-identical artifact checks. Outputs are under
`work/simple-strategy-discovery-v2/`, not committed. The report and summary cover
all 45 independently funded hypothesis/cost/account combinations. Raw records are
not independent across scenarios and must never be pooled as a portfolio.

The run adapter changes only the research runner's detector, hypothesis names and
output directory in its own process. It uses the existing unchanged native 1m
execution and account selection. Source Parquet reads have explicit Development
predicates; full-file hashing verifies identity without decoding later outcomes.
Normal Lab storage is read only for preservation hashes.

Verification checks an independent vectorized detector, confirmation times,
structural risk and 2R arithmetic, all-in fees, whole-contract sizing, daily
chronological selection, every account balance, native fills against independent
minute simulation, source/storage hashes, and deterministic artifacts. Tests also
cover mirrored directions, exact thresholds, dual-boundary sweeps and missing or
incomplete candles. No frontend/API/production engine change is needed. Full
historical golden tests that would decode protected years are intentionally not
run; synthetic execution/session/management regressions are run instead.

Interpretation cautions:
- $200/$400/$4763 margin assumptions are inherited scenarios, not newly verified
  broker requirements or guarantees of account approval.
- CAPITAL_LOCKOUT counts only falling below the minimum theoretical affordable
  valid trade. An account can remain slightly above that threshold yet never see
  an affordable signal again. Inspect daily and rejection records, not just that
  flag. Neither state implies the balance is literally zero.
- The diagnostic can lose more than its nominal starting balance because it
  intentionally ignores capital feasibility; it is not an executable account.
- Adjusted inference includes all six hypotheses in these two batches, not every
  prior experiment in the repository. Development has already been inspected.
- No candidate passing this screen would be considered validated or live-ready.
