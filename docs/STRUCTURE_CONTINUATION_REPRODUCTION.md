# Reproduce standalone market structure 2R Development test

The frozen contract is `STRUCTURE_CONTINUATION_2R_V1.md`. Synthetic illustrations
motivated this test; they are not historical trade evidence. No prior key-level
result or Validation result is used to change eligibility.

Requires the existing validated research master files and the verified
`work/eight-level-reaction-entry-study-v1/source_identity.json` and manifest.
No paid download. Normal SQLite is read only to verify preserved metadata; no
strategy/run records are inserted. These results appear under Research, not Runs.

From repository root, using the installed local environment:

```
work/.venv/bin/python scripts/structure_continuation/prepare.py
work/.venv/bin/python scripts/structure_continuation/run.py
work/.venv/bin/python scripts/structure_continuation/report.py
work/.venv/bin/python scripts/structure_continuation/verify.py
```

On first creation, repeat run/report/verify: the second verify requires identical
CSV, Parquet, report, HTML and JSON artifact bytes. Prior verified artifacts are
not edited by this experiment. This reproduction command rewrites only the new
experiment's local outputs deterministically; do not change rules under its ID.

The manifest gates read-only API exports at
`/api/research/structure-continuation/files/study.html`.
Every primary trade can be opened on its five-minute chart. Swing lines start at
confirmation, not formation. Subsequent candles in charts are retrospective audit
context only. Full source files are hashed for identity, but outcome rows are
read only with Development date predicates. Validation/OOS are not decoded.

## Verification and known limitations

104 tests pass: 101 Python (detector/native-execution/research/session/API), two
frontend component tests, one Playwright workflow. Production frontend build passes.
The 1,584 signals reconcile to an independent pivot implementation; all 3,293
completed cost-scenario executions reconcile to independent minute fills. Two
runs produce byte-identical outputs. Normal storage metadata/reveal states match.
Production engine and historical results remain unchanged. Full local legacy golden
runs are not executed: they would decode 2024+ outcomes, outside this task's scope.
Synthetic execution regressions are included in the relevant checks instead.

One trade on March 18, 2020 enters short at 12:50 New York and owns the absent
12:58 minute. Its P&L cannot be reconstructed. After that failure the adapter blocks
new entries through session close, including a 15:55 long signal whose true eligibility
is unknown. Completed-trade totals therefore are not complete full-history performance.
The same issue exists in all three slippage scenarios. No synthetic replacement minute
or hypothetical P&L is assigned. The report shows an incomplete-execution banner.

2R is the sole tested exit objective. Excursions stop at exit; the native complete
exit-minute MFE can exceed 2R but does not establish attainable profit beyond target.
Milestone counts are stop-first and capped at 2R. No post-exit outcome research.
No time/structure/risk subgroup was turned into a filter; no parameter optimization.
