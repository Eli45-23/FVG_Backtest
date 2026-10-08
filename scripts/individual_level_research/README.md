# Individual MNQ level research — Development only

This is a research-only reproducibility kit, not a strategy or an execution-engine change. Run commands from the repository root using the existing local Python environment. Dependencies are the backend requirements plus the plotting packages listed here. The exact analysis environment is recorded in the research artifact directory.

Outputs live in `work/mnq-individual-level-master-research/` and remain outside Git. The deliverable is `MASTER_LEVEL_RESEARCH_REPORT.md` plus `MNQ_INDIVIDUAL_LEVEL_RESEARCH.zip`. Full unsampled Parquet exports are linked by SHA-256 in `EVIDENCE_INDEX.json`; they are intentionally not committed or bundled as market-data samples.

The saved primary family is 12 level families × 14 interaction classes × two stored directions × two measured directions, at 30 minutes and 1 ATR. BH spans all 672 hypotheses. Other horizons, thresholds, years and contexts are exploratory. Existing studies and source files are never overwritten. Supply/demand are explicitly blocked under the frozen 4h provider, not reported as zero-probability results.

## Reproduce aggregate reports against the existing local artifacts

```sh
work/.venv/bin/python scripts/individual_level_research/consolidate.py
work/.venv/bin/python scripts/individual_level_research/report.py
work/.venv/bin/python scripts/individual_level_research/determinism_check.py
work/.venv/bin/python -m pytest -q scripts/individual_level_research/verify_analysis.py
work/.venv/bin/python scripts/individual_level_research/finalize.py
```

The deterministic check reruns the aggregation and Markdown report generation. The independent checks recompute causal prices/pivots and selected one-minute outcomes, and compare vectorized date-bootstrap results with the validated engine implementation. No Validation/OOS outcome access is needed. Do not run the historical 2024–2026 golden simulations as part of this Development-only research.

## Full source-artifact analysis pipeline

1. `preregister.py` writes a protocol only if it does not already exist. The completed project's saved protocol must remain unchanged. Do not overwrite it to represent a different experiment.
2. `run_premarket.py` creates the midnight PMH/PML immutable study only if its saved study ID does not exist. It uses the normal Lab worker and waits for completion; it does not reset or seed SQLite. Do not rerun it to duplicate a completed study.
3. `audit_foundation.py` verifies source identities, records PM coverage and independently replays causal feature construction. No market data is mutated.
4. `analyze.py` reads full Development-only columnar outcomes one level/horizon at a time. Verified per-level completion markers prevent accidental recomputation; remove only this analysis's marker files when intentionally rebuilding derived outputs. It does not recreate source studies.
5. `audit_events.py` verifies all selected point-event records and draws chronological examples. `refresh_charts.py` draws availability-aware charts clipped to the actual session close.
6. `augment.py` adds excursion/control comparisons, revisits, independent swing checks and same-date sensitivity. `distributions.py` adds full distributions and episode accounting.
7. Run the aggregate/report/check/package commands above. Work scripts included in the local bundle are the same reproducibility sources as this directory.

`determinism_check.py` invokes the copies under the work output directory so a delivered bundle remains locally reproducible; keep those copies synchronized when changing the kit. The source studies are fixed by IDs in the kit. To create a different study, make a new version/directory and preregister it before inspecting outcomes.

Only the two authorized Development study directories are used for outcomes. Dataset hashing may read whole-file bytes to verify identity, but decoded historical rows are bounded before 2024-01-01. Calendar metadata is not predictive outcome data. No API credentials are loaded.

## Method limits

See the delivered `ADDITIONAL_METHOD_NOTES.md`. In particular, primary confidence intervals are conditional on the empirical matched pool, labels overlap, and same-date controls are an exploratory sensitivity that may overcondition on the intraday path. A positive threshold effect is not trade profitability. The broad primary and exploratory families must not be replaced by isolated favorable tests.
