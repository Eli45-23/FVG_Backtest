# O15L 2024 Validation: reproduction and verification

The unchanged candidate failed the preregistered Validation gate. Primary result: 69 trades on 63 dates, net −$1,552.24, PF 0.677949, average net R −0.210433, closed drawdown $2,253.78 / 15.872509R. No rule or gate was adjusted after this result.

## Frozen chronology

- `6b66c12`: preregistration and protocol committed before this task decoded any 2024 bars/outcomes.
- `a1e76de`: portable detector, executor, gate and reporting code committed after exact Development reproduction, before Validation access.
- Local append-only `work/o15l-clear-hold-validation-v1/access_ledger.jsonl` records both authorized 2024 reads with protocol/code identities. It does not reveal or mutate existing sealed studies.

Prerequisites: local validated research profile, eight-level source identity and immutable prior combination/Development studies. Keep prior artifacts intact. On a fresh machine create `work/o15l-clear-hold-validation-v1/` and copy `docs/O15L_VALIDATION_PROTOCOL_V1.json` to it as `protocol.json`. Do not replace different existing results.

```sh
work/.venv/bin/python scripts/o15l_validation/detect.py
work/.venv/bin/python scripts/o15l_validation/run.py development
work/.venv/bin/python scripts/o15l_validation/run.py validation
work/.venv/bin/python scripts/o15l_validation/report.py
work/.venv/bin/python scripts/o15l_validation/verify.py
```

The first two commands use Development only and block Validation if identities or economic fields differ. The Validation commands decode December 2023 warmup plus 2024 bars, and 2024 execution minutes, with an exclusive 2025-01-01 NY boundary. Later OOS data are never decoded. Full-file hashes verify preservation, not outcomes.

## Checks completed

- Exact 280 Development confirmations and 865 obstacle opportunities reconstructed using original causal APIs, including ATR/barrier/timestamp/price agreement.
- Exact same 273 selected Development trades in each of three cost scenarios; serialized entry/stop/target/exit/P&L/R/MFE/MAE match prior artifacts. 819 native fills independently checked.
- Validation: 378 upward O15L roots; 216 frozen-obstacle opportunities; 71 hold confirmations; 69 selected trades and two session-close confirmations. No busy skips, nonpositive risk or unresolved execution minutes. Same primary trade population across cost scenarios.
- 207 Validation fills checked by an independent minute loop. All 69 primary candle sequences checked for complete root/clearance/hold bars, strict boundary conditions, availability and original 1R brackets.
- Full Validation replay/report produced 30 byte-identical artifacts. Access ledger is intentionally append-only and excluded from byte-equality comparison, then hashed into the final manifest. Economic result files, chart Parquet and HTML are deterministic. ZIP has fixed timestamps and raw-file references.
- 67 relevant Python tests passed, including gate boundaries, OOS read-bound rejection, causal waiting, position selection and old/new report API checks.
- Four frontend component tests and two browser workflows passed. New Validation and existing Development pages both tested. Trade filtering/clearing, charts and CSV/JSON/ZIP exports work. Rendered Validation report and first-trade chart inspected visually.
- Production frontend build passed. Existing chunk-size and Starlette dependency warnings remain nonblocking.

## Inspect and preserve

Run `./run_app.sh`, open Research → **O15L · 2024 Validation**. Direct URL: `http://127.0.0.1:5173/api/research/o15l-validation/files/study.html`.

The report is a separate read-only research artifact, not a normal database run or a modification to the Development strategy. Routes accept only hash-verified Validation artifacts and selected trade dates in 2024. The original Development route is unchanged. Production engine logic is unchanged; full-history legacy golden tests were not rerun because they access sealed 2025+ outcomes. Exact Development replay supplies compatible regression evidence.

Dataset/source hashes and normal user strategy, run, study, migration and reveal-state metadata remain unchanged (metadata identity `7788ad66dc95225bc66971d478edce3a74069af91b6b705f02779ce88e553300`). OOS remains sealed. No paid-data download or credential access. Generated trade records, market-data extracts, Parquet and ZIP remain local and ignored. The pre-existing `.DS_Store` remains untracked.

This is a failed test of the frozen candidate, not a reason to mine Validation for rescue filters. No OOS run or live deployment was performed. 2024 is now inspected for this candidate and cannot be reused as fresh Validation for changes motivated by these results.
