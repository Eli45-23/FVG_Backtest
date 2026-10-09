# Downward-break feasibility: local reproduction and viewing

The Lab **Research** page offers **Next-candle full-hold feasibility** separately from the eight-level reaction study. Choose a level, either structural stop and 1R/2R target. Inspect primary actual-fee results, all four Development years, zero/one/two-tick sensitivity, stop-bounded paths and denominators. All 32 primary combinations are retained in fixed level order, including negative results.

Direct local view: `http://127.0.0.1:5173/api/research/full-hold-feasibility/files/study.html`.

The endpoint is read-only, Development-only and manifest-gated, with allowlisted files and SHA checks. It does not create saved strategies, write database records, reveal studies or modify execution behavior. This is an independently evaluated event audit; overlapping hypothetical trades must not be interpreted as an investable portfolio.

## Reproduction

Existing local research data and the previously verified eight-level study must be present. No download or paid-data access is performed. The frozen `protocol.json` must be retained/restored from this audit’s bundle; its specification hash must match the committed protocol document. Do not silently replace the specification under an existing identity.

```sh
work/.venv/bin/python scripts/downward_break_full_hold/run.py
work/.venv/bin/python scripts/downward_break_full_hold/report.py
work/.venv/bin/python scripts/downward_break_full_hold/verify.py
```

`verify.py` repeats every native fill and complete summary and requires byte-identical CSV/JSON/Markdown/HTML outputs. Source hashes are checked again, and a deterministic aggregate ZIP plus full evidence index is created. `verification_runtime.json` is separate from deterministic outputs. Reproduction rewrites only this audit’s generated folder; archive it before any intentional specification change.

The full native execution log and stop-bounded paths are under `work/downward-break-full-hold-feasibility-v1/`. They remain local and ignored. The ZIP contains aggregate tables, protocol and reports; its index links every unsampled raw file by path, size and hash. No raw record is discarded to shrink the ZIP.

## Test commands

```sh
work/.venv/bin/python -m pytest tests/test_downward_break_full_hold.py tests/test_eight_level_study.py tests/test_levels.py tests/test_research_extensions.py backend/tests/test_full_hold_report.py backend/tests/test_level_study_report.py backend/tests/test_event_studies.py backend/tests/test_research_upgrade.py -q
cd frontend
npm test
npm run build
npx playwright test full-hold-e2e.spec.ts eight-level-e2e.spec.ts
```

The browser tests require a running Lab and verified local artifacts. Unrelated saved-run endpoints are mocked to avoid reserved-outcome access. The existing production executor performs every fill, with an independent short-fill check on every completed/unavailable target simulation. No actual Validation/OOS golden backtests are rerun because production execution is unchanged and reserved outcomes are outside this task’s scope.

See `DOWNWARD_BREAK_FULL_HOLD_FEASIBILITY_V1.md` for the frozen entry, two stops, actual fees, session, ambiguity, missing-minute and overlap conventions.

## Controlled comparison

The original immediate-break study is a read-only dependency and every artifact in its verified manifest is hash-checked. `compare.py` links each confirmed event to its original break root, requires identical absolute stops and exactly five minutes of entry delay. All-root, matched-root and omitted-root cohorts are exported separately. Matched cohorts condition on subsequent confirmation and are not a causal treatment comparison. The entire original break population is independently reconciled to complete next-candle OHLC; missing/incomplete or non-adjacent candles cannot qualify.
