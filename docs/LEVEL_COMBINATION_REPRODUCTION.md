# Reproduce the level-combination study

The frozen definitions are in `docs/LEVEL_COMBINATION_STUDY_V1.md`. This is Development-only, uses existing local data and verified immutable eight-level study inputs, and never accesses Validation/OOS outcome rows. Full-file hashing verifies preservation but does not decode reserved outcome data.

From the repository root, with the existing virtual environment and completed eight-level study available:

```
work/.venv/bin/python scripts/level_combination/run.py
work/.venv/bin/python scripts/level_combination/report.py
work/.venv/bin/python scripts/level_combination/audit.py
work/.venv/bin/python scripts/level_combination/verify.py
```

`work/level-combination-study-v1/protocol.json` must already contain the frozen specification SHA-256 and parameters (nearby_atr=1, primary_slots=32, seed=1729, bootstrap=2000). Do not replace an existing protocol or a historical result to try other parameters; use a separately versioned study instead.

The independent audit checks every waiting opportunity with a separate vectorized implementation, including empty session-close windows. The verifier also reconciles all 68,184 matching prior Development downside diagnostic rows (full economics for completed trades, eligibility and initial risk for non-executable signals). No reserved-year golden replay is needed for that comparison.

The verifier repeats both full calculations and requires byte-identical CSV, JSON, Markdown and HTML artifacts. It records the code hashes and native independent fill-check count, builds a complete ZIP, and only then writes the PASS manifest used by the read-only API. Runtime is separate from deterministic economic artifacts. The archive's manifest excludes its own ZIP hash to avoid a self-reference; the external manifest includes that ZIP hash.

Start the existing Lab with `./run_app.sh`, open `http://127.0.0.1:5173`, go to Research, and choose **Open level-combination evidence**. Direct URL: `http://127.0.0.1:5173/api/research/level-combinations/files/study.html`.

The page offers full-family corrected statistical evidence, waiting-policy coverage, trade-conditional diagnostics, year tables, cluster comparisons, costs, source preview and full exports. Tables can be filtered by level and direction, then cleared. This is a read-only diagnostic study, not a saved executable portfolio strategy. No database migration or mutation is performed. The API rejects non-Development manifests, unknown file paths and changed artifact hashes.

Every execution row retains original opportunity ID, entry ID, timestamps, fixed original-candle stop, costs and native fill result. The signal export freezes known levels, availability times, obstacles and cluster membership. Waiting opportunities include failures and no-entry reasons. Statistical rows expose all matched/paired observations; unsupported clusters are reported in the evidence table. Repeated levels on the same candle are documented in the overlap audit and uncertainty clusters by date.

Re-running the scripts intentionally regenerates ONLY this new study's output directory, as verified byte-identical. Existing source studies, market files, strategies, saved runs and gates are never overwritten.

Tests:

```
work/.venv/bin/python -m pytest tests/test_level_combination.py backend/tests/test_combination_report.py
cd frontend
npm test
npm run build
npx playwright test combination-e2e.spec.ts
```

Production fill logic is unchanged. Legacy full-history golden executions are not run in this Development-only research task because they would decode reserved years; relevant synthetic execution regression tests are run instead.
