# v1.1 audit and implementation plan

Starting HEAD ca000c837dd1f56b9a38efbc7d5d71135e52168d; clean working tree.
Origin/main matches HEAD. No later user work was present. Read AGENTS.md, backend
models/migrations/API/workers, SDK/providers/runner, frontend editor/trades/charts,
versioning, sweeps and assumptions. Existing storage contains three completed runs.
A SQLite online backup is preserved locally at work/v11-before.db; browser testing
uses separate work/v11-browser-storage. No database reset or market-data changes.

Baseline: 156 legacy + 44 Python platform + 5 component + 2 E2E = 207 passing.
Logs: work/v11-baseline-*.log. The upstream TestClient deprecation is non-failing.

1. Refine the existing candles API into windowed chart data with generic annotations.
   Add a large Trade Inspector with Lightweight Charts, exact UTC data / NY labels,
   actual-time overlays, details and previous/next navigation.
2. Keep the unmanaged ref.execute path untouched. Add opt-in manage(ctx, params)
   execution with immutable contexts and MoveStop requests. Test synthetic causal
   scenarios first. At each minute: active-stop/target/session exits FIRST; only
   survivors get minute-close and completed-5m callbacks. Requests activate at the
   next minute start (the confirmation instant), never within the observed interval.
   Coalesce simultaneous requests to most protective; reject loosening. R-Step holds
   require a full bar starting at/after the +5 request activation, so no pre-touch
   candle activity qualifies as a later whole-bar hold. All qualifying R thresholds
   at one close compete, with the most protective winning; no artificial serial delay.
3. Persist events as versioned run artifacts, chart stop activation segments, and
   run the exact requested Quality R-Step twice without optimization.
4. Add immutable version detail/diff/clone/restore actions and Monaco Diff UI.
5. Add additive research_splits, experiment_snapshots and experiment_runs tables.
   Freeze exact source/config/data/engine, require explicit OOS run/reveal, preserve
   audited timestamps. Use NY end-exclusive dates consistently (UI labels explicit).
   Reject overlap/reversal/out-of-coverage, warn gaps. Guard sweeps server-side;
   official OOS cannot be swept. Freeze identity is checked again at execution.
6. Add segmented UI, comparison warnings, documentation, migration/protection and
   browser tests. Re-run exact fixed-bracket goldens and verify old storage records.

No push. Logical local commits only. Management is opt-in; old sources/results remain
recoverable. Sealed OOS is a workflow safeguard, not a file-security boundary.
