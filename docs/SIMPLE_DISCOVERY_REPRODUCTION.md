# Reproduce the simple-strategy discovery study

Protocol: `SIMPLE_STRATEGY_DISCOVERY_V1.md`; preregistration commit e675402.
Only three fixed rule families were tested. No subsequent threshold/stop/target
changes, no selected time filters, no account deposits. Primary fees remain the
user's actual $.73/side. Current official margin snapshot and historical uncertainty
are documented in the frozen protocol, not substituted for historical broker data.

## Local reproduction

Requires the existing validated research Parquets and the prior verified source
identity at `work/eight-level-reaction-entry-study-v1/source_identity.json`.
No download required or performed. Existing normal storage is read-only for
metadata/reveal preservation checks; this is a research study, not new normal
Lab strategy-version/run records.

```
work/.venv/bin/python scripts/simple_discovery/prepare.py
work/.venv/bin/python scripts/simple_discovery/run.py
work/.venv/bin/python scripts/simple_discovery/report.py
work/.venv/bin/python scripts/simple_discovery/verify.py
```

Repeat run/report/verify for byte-level equivalence. Source reads have explicit
2020–2023 predicates. Full-file hashes confirm source identity without decoding
later outcomes. No legacy golden runner is executed because that would decode
2024–2026 outcomes; production execution is unchanged and covered by synthetic
regressions and independent per-trade fill checks instead.

The read-only report is at `/api/research/simple-discovery/files/study.html`.
The Research page links it. Select hypothesis, account scenario and slippage to
see all four years, account path and every trade. Charts show retrospective
Development candles; they do not affect causal entry selection. CSV/JSON exports
are hash-guarded. No generated source samples, trades or Parquets are committed.

## Verification

77 relevant tests: 74 Python, 2 frontend, 1 browser. Production build passes.
18,931 signals reconcile against an independent vector implementation. Every
scenario's first daily eligible signal and integer quantity are independently
reconciled. 7,778 distinct selected native fill configurations match independent
fills. Repeated outputs are byte-identical, source hashes and normal DB metadata
including reveal states unchanged. No selected execution gap or margin breach
was found in this experiment. Complete daily denominators are 1,000 full sessions.

One bookkeeping correction was made before finalization: terminal capital lockout
must include the minimum tick-aligned risk that ALSO satisfies net reward > all-in
loss. This is $4.46/$5.96/$7.46 per micro at 0/1/2 ticks, plus margin. The initial
$1.96 label threshold undercounted terminal lockout days. Entry eligibility was
already correct; no signals, quantities or economic fills changed. Final outputs
were rerun twice with the corrected status accounting. Frozen formation rules and
sizing rules were not changed.

## Interpretation limit

All three fail the preregistered primary gate. This does not prove that no simple
MNQ strategy exists. It shows these three fixed rules do not support the specified
$100/day objective on a $500 account. Increased size magnifies losses too. The
one-micro two-push result is positive but weak, inconsistent across years and
insignificant under the registered uncertainty assessment. There is no automatic
Validation advance. Remaining Validation/OOS restrictions stay in force.
