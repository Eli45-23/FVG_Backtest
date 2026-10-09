# Eight-level Development study: use and reproduction

This study answers the fixed-level reaction and entry-timing request using the existing Development artifacts. It is separate from the executable strategy backtests. No execution, position management, saved strategies, database migrations or reveal rules are changed.

## Open the completed results

Start the existing Lab with `./run_app.sh`, open `http://127.0.0.1:5173`, select **Research**, and choose **Open results, entry comparisons and chart audits**. The viewer has eight levels, ten entry definitions, both directions and six forward horizons. The registered evidence table always refers to 30 minutes / 50 points, regardless of the exploratory horizon selector.

The report is also directly available at:

`http://127.0.0.1:5173/api/research/eight-level-study/files/study.html`

The read-only API exposes files only after the study has passed verification, only from its manifest allowlist, and only if their hashes still match. It does not query the run/study database or reveal outcomes. A missing local study displays an unavailable message; nothing runs or downloads on startup.

## Files

All full observations and generated measurements are ignored by Git under `work/eight-level-reaction-entry-study-v1/`:

- `protocol.json`: frozen pre-analysis rules and specification hash.
- `source_identity.json`: exact original Development study/data hashes.
- `source_events.parquet`: all reused/new causal events with source IDs.
- `entry_events.parquet`: all candidate entry observations, including late/censored cases.
- `baseline_observations.parquet`, `baseline_outcomes.parquet`: all ordinary observations and subsequent one-minute measurements, shared by timestamp without sampling.
- `primary_evidence.csv`: entire globally corrected 160-comparison family.
- `fixed_point_outcomes.csv`, `atr_outcomes.csv`: all predefined horizons/distances.
- `context_comparisons.csv`: yearly, time, touch number and volatility descriptions.
- `entry_frequency.csv`, `paired_entry_comparisons.csv`, `overlap_audit.csv`: opportunities, timing, overlap.
- `data_quality.csv`, `chart_audit.csv`, `quality_verification.json`: complete/censored denominators and source/chart checks.
- `EIGHT_LEVEL_RESEARCH_REPORT.md`, `study.html`, `study_summary.json`: readable results.
- `evidence_index.json`: links and hashes for every unsampled source/result artifact.
- `study_bundle.zip`: report, viewer, all aggregate tables, charts and evidence index. Full Parquet files remain external with exact hashes rather than being silently sampled.
- `reproducibility_manifest.json`: byte-identity check and served-artifact hashes.
- `verification_runtime.json`: measured rerun duration, excluded from deterministic economic/research artifacts.

The original six level studies and their configurations remain immutable. O15 is constructed additively; this work does not create or change a database EventStudy record.

## Reproduce locally

Use the existing installed environment (`work/.venv/bin/python`) and existing local files; do not download market data. The frozen `protocol.json` must already be present, or restored from the verified bundle. Never silently recreate a different protocol under the same study identity.

```sh
work/.venv/bin/python scripts/eight_level_study/detect.py
work/.venv/bin/python scripts/eight_level_study/label.py
work/.venv/bin/python scripts/eight_level_study/analyze.py
work/.venv/bin/python scripts/eight_level_study/qa.py
work/.venv/bin/python scripts/eight_level_study/report.py
work/.venv/bin/python scripts/eight_level_study/verify.py
```

`verify.py` repeats all five stages and requires byte-identical CSV/JSON/Parquet/HTML/Markdown/SVG outputs before publishing the manifest and deterministic ZIP. Only this new study's generated directory is rewritten during reproduction. Archive it before intentionally changing any definitions; do not overwrite prior immutable studies. Artifact-serving hash checks refuse changed outputs until verification passes again.

## Checks

```sh
work/.venv/bin/python -m pytest tests/test_eight_level_study.py tests/test_levels.py tests/test_research_extensions.py backend/tests/test_level_study_report.py backend/tests/test_event_studies.py backend/tests/test_research_upgrade.py -q
cd frontend
npm test
npm run build
npx playwright test eight-level-e2e.spec.ts
```

The browser smoke test requires the completed local study and running Lab. It mocks unrelated app-list endpoints so no saved Validation/OOS results are loaded; the new read-only Development report and downloads are exercised against the actual API. Synthetic sealed-gate tests operate in isolated storage. Real legacy golden reruns are unnecessary because production strategy/execution code is unchanged; do not run reserved-history backtests as part of this study.

See `EIGHT_LEVEL_REACTION_ENTRY_STUDY_V1.md` for the frozen methodological definitions. Favorable excursion probabilities are not strategy win rates or guaranteed fills, and paired timing subsets do not prove that waiting causes better performance.
