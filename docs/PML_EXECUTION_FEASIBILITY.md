# PML failed-break execution-feasibility audit

This independent Development-only audit reuses immutable study
`78c96aa0e91147ba9913e365f33ed2f9`. It does not register a strategy or change production fills.

Run from the repository root with the existing research environment:

```sh
work/.venv/bin/python scripts/pml_feasibility/run.py
work/.venv/bin/python scripts/pml_feasibility/report.py
work/.venv/bin/python scripts/pml_feasibility/finish.py
work/.venv/bin/python -m pytest -q tests/test_pml_feasibility.py tests/test_swing_low_feasibility.py
```

Output: `work/pml-failed-break-execution-feasibility-v1/` (ignored market-data derivatives).
The report, frozen execution protocol, source manifest, exact events, full executions and metric-specific denominators are retained locally. Reruns deterministically regenerate this audit's files only; they never modify the source study or earlier audits.

The raw population is 407 PML `BREAK_FAILED_NEXT_CANDLE_HOLD` / DOWN events on 286 dates. The historical 30m/1ATR reference is 387 events on 274 dates; 20 session-boundary events remain execution candidates. PML uses the complete same-date 00:00–09:30 New York window. Short entry follows the confirmed reclaim above PML; this measures renewed downside, not the upward reclaim response.

Exactly three stops (sequence high, failure high, root high, each plus one tick), three diagnostic targets (.5/1/1.5R), and three slippage scenarios (0/1/2 ticks each side) use the existing executor with actual user-supplied $0.73/side fees. Nonpositive risk and no post-entry session minutes are explicit statuses. No daily lock, filtering, optimizer, managed stop or portfolio performance claim is added. All historical source reads are predicate-bounded to Development, and no database/reveal APIs are used.

The short-side independent fill check mirrors the previously tested long-side research checker. The 15/30/60-minute races have separate complete/censored denominators; session-wide races cannot silently substitute for them. Inclusive exit-minute MFE/MAE are upper bounds on intraminute ordering. Native fills are checked against independent prices, time, net P&L, conflicts and excursions. A complete causal replay verifies source event IDs and episode inheritance. Context never becomes eligibility.

Only scoped synthetic tests should be run for this task. Broad historical regression suites may read reserved 2024+ data; they are not necessary because production code is unchanged. No push is authorized.

For the complete verification sequence (scoped tests and two full byte-comparison reruns):

```sh
work/.venv/bin/python scripts/pml_feasibility/verify.py
```
