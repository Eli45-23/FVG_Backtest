# Explicit session policy for extended execution

`RunConfig.session_policy` and API `RunSettings.session_policy` default to `XNYS_FULL`, preserving existing strategy behavior. `XNYS_ALL` is an explicit opt-in and requires `extended_v1`; it admits scheduled XNYS half-days and uses the existing executor's actual calendar close. Neither policy permits overnight ownership. Existing run artifacts/configurations are not rewritten.

Extended execution also passes `feature_config.session` to the existing `SessionConfig`/`FeatureHub` interface. Omission retains defaults. To reconcile a saved event study exactly, pass its original session configuration including its numeric representation. Level IDs include serialized configuration; `0` and `0.0` historically have different hashes. This change does not normalize or rewrite old IDs.

The PDH Development strategy uses `XNYS_ALL` and the immutable study's explicit session settings. Its late same-day signal report translates either `POSITION_OPEN` or `DAILY_TRADE_LIMIT` into the strategy's `DAILY_LIMIT_REACHED` policy only after proving a prior signal was selected that date; native engine reasons remain in the audit.

Synthetic tests cover unchanged defaults, explicit early-close exits, configuration validation, and session metadata propagation. Real 2024–2026 golden reruns require separate authorization when a task forbids Validation/OOS data access; golden fixtures and legacy execution implementations remain unchanged.
