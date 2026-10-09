# Development swing-low execution feasibility

This audit implements only the user-prespecified entries (raw TOUCH close, existing REJECTION overlap, existing SWEEP_RECLAIM overlap), structural stops (swing/event low minus one tick), targets (0.5/1/1.5R), and 0/1/2-tick slippage with actual $0.73/side fees. It does not create a saved strategy or change the production engine.

The executable source population is **5,319 causal 5m_SWING_LOW / TOUCH / DOWN events over 1,006 Development dates**. The historical **4,816/1,004** measurement reference is not an eligibility gate. All immutable sources refer to Development study `5cb7fab0d4e7414792a3fbe59ded4999` and the master research directory. Required market reads use Development date predicates only.

Run from the repository root:

```sh
work/.venv/bin/python scripts/swing_low_feasibility/run.py
work/.venv/bin/python scripts/swing_low_feasibility/report.py
work/.venv/bin/python scripts/swing_low_feasibility/finish.py
work/.venv/bin/python -m pytest tests/test_swing_low_feasibility.py -q
```

Local outputs are under `work/5m-swing-low-execution-feasibility-v1/`, ignored by Git. The first population-gate audit is preserved under `preflight_before_population_amendment/`. Do not run the original `swing_low_feasibility_preflight.py` over the completed folder: it represents the earlier, superseded 4,816-raw-event gate.

`run.py` checks immutable sources and candidate identity, reconstructs exact causal swing context, then invokes the normal `engine.partial_execution.execute` for every positive-risk target diagnostic. A separate numerical reducer checks fills, timestamps, P&L, extrema and conflicts. B/C reuse the same event executions and never receive later-candle membership decisions. Actual missing owned minutes would remain execution-unavailable; later gaps after an exit are not owned.

`core.py` measures stop-bounded paths, fixed-horizon censoring, threshold races and intraminute uncertainty. Full exit-minute extrema are upper bounds, with pre-exit lower bounds exported. Never present those upper bounds as necessarily attainable profit. R metrics retain ATR-unavailable events. Calendar-close confirmations are retained in the population but cannot own a new minute after the close.

`report.py` partitions raw eligibility, risk rejection, no-owned-session interval, completed execution and measurement completeness explicitly. Descriptive horizon completeness is independently reconciled with the immutable horizon artifacts. Annual/touch/structure slices do not change eligibility.

`finish.py` assembles the reviewed findings and refuses to silently reuse the negative-result conclusion if its supporting conditions no longer hold. It does not rank targets or optimize a strategy. Recommendation status is `DEVELOPMENT_EXECUTION_FEASIBILITY_ONLY`; the result applies only to the frozen protocol. Summed independent overlapping event P&L is not a portfolio return.

Only the scoped synthetic tests should run for this task. Broad historical test suites may query reserved periods. No Validation/OOS outcome access or push is authorized.
