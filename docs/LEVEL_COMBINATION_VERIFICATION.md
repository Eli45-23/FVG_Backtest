# Level-combination study v1: verification

The completed study is available under Research → **Do nearby levels improve entries?**. Its frozen protocol and reproduction instructions are adjacent documentation files.

## Calculation checks

- 32,979 raw causal break/rejection events across 1,005 Development dates; 36,400 entry records including waiting confirmations.
- 10,011 waiting opportunities independently reconciled with a vectorized sequence audit; 3,421 confirmations and 3,376 completed primary waiting diagnostics.
- 216,282 completed native fills independently checked in each full historical run. Six combinations are diagnostics: two fixed targets × three slippage assumptions.
- 68,184 matching prior Development downside diagnostic rows reconcile exactly. Completed rows match entry, risk, stop, target, exit, P&L, R, duration and excursions. Non-executable rows match eligibility and initial risk.
- Full repeated calculation produced 23 byte-identical result files. The subsequent presentation-only change replaced internal table headings and formatted numbers; all economic outputs remained identical, and HTML/report generation was repeated twice with identical results.
- One independent audit implementation initially included a spurious timestamp for an empty session-close window. That audit-only boundary bug was corrected; the causal detector and economic results did not change. A synthetic session-close test covers the intended empty-window behavior.
- 32 predeclared primary comparisons share one BH family. Inference clusters by NY date; all primary inference groups have at least 70 supported dates. Unmatched rejections and non-executable pairs are separately reported.

## Tests and presentation

- 102 relevant backend, research, and execution tests passed.
- 37 frontend unit/component tests passed.
- 5 browser smoke workflows passed: combinations and the four existing research report pages. The new page was tested again after its display-only change.
- Production frontend build passed. Existing chunk-size and dependency deprecation warnings remain nonblocking.
- Rendered report visually checked; level/direction filters, clear action, full table navigation, CSV/JSON/ZIP downloads verified.

Legacy full-history golden replays were deliberately not run because this task forbids reserved-year outcome reads. Production fill logic did not change; the exact prior Development economic comparison above provides task-compatible regression evidence.

## Preservation

Market-data and reused study source hashes match. The normal database was never reset or written by these scripts. Saved run, strategy/version, study, migration, split, experiment and reveal-state metadata match the pre-run snapshot. Research queries are bounded to New York 2020-01-01 inclusive through 2024-01-01 exclusive. No Validation/OOS outcomes were queried by the research; no reveal was performed. No paid data download or credential access occurred.

Generated event/trade exports, market files, databases and the ZIP remain local and ignored by Git. Only code, tests, documentation and aggregate findings are committed. A pre-existing untracked `.DS_Store` is preserved.
