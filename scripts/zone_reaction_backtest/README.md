# Four-hour zone reaction experiment

Run from the repository root with its existing local research environment:

```sh
work/.venv/bin/python scripts/zone_reaction_backtest/verify.py
```

This executes all three frozen setups twice, with the unchanged native one-minute executor, and requires byte-identical result/configuration files. It writes only to `work/four-hour-zone-reaction-backtest-v1/results/`. The earlier frozen specification snapshot and accepted provider artifacts are read-only. The work directory and all market-data files stay ignored by Git.

`signals.py` accepts only confirmed bars and currently known zone/invalidation state. `run.py` verifies accepted source hashes, replays the original provider and invalidations exactly, checks engineering evidence, runs synthetic tests, applies sequential position ownership, and checks each native fill against an independent reference. `report.py` computes descriptive summaries without searching parameters. `verify.py` repeats the complete process and records fingerprints.

Required local inputs are the accepted calendar-foundation artifacts, existing immutable Development study configuration `78c96aa0e91147ba9913e365f33ed2f9`, and the existing research one-/five-minute Parquet data. No downloader is invoked. Data scans are predicate-bounded to New York 2020-01-01 through 2024-01-01 exclusive. Whole-file hashes verify identity without querying reserved outcomes.

These are independent Development research runs, not a combined portfolio and not saved-run database entries. All three retain one micro, fixed 2R, one adverse tick per side and $0.73/side fees. No human-label prerequisite remains for this explicitly authorized experiment. Engineering requirements, unresolved-session exclusions and Validation/OOS protection remain in force.

The old acceptance functions preserve historical report semantics. New code opts in explicitly through `assess_mechanical` / `require_mechanical_acceptance`; it does not relabel the provider as human-ground-truth accepted.

See `docs/FOUR_HOUR_ZONE_REACTION_BACKTEST_V1.md` for the exact signal and same-timestamp ordering contract.
