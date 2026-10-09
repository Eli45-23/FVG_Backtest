# V2 zone engineering audit (not an accepted research provider)

Run from the repository root using the project environment:

```sh
work/.venv/bin/python -m scripts.zone_v2.audit_foundation
work/.venv/bin/python -m scripts.zone_v2.audit_lifecycle
work/.venv/bin/python -m scripts.zone_v2.chart_audit
work/.venv/bin/python -m pytest tests/test_zone_v2.py -q
```

These commands write engineering diagnostics under `work/supply-demand-provider-v2/`.
They do not create an immutable Lab study or calculate forward outcomes. Re-running
chart generation resets the manual review fields; preserve a reviewed export first.
The frozen configuration must match before the foundation runner proceeds.

The candidate CMES schedule disagrees with local historical MNQ coverage on
specific holidays. The provider is deliberately not registered in the production
Event Studies selector. Resolve and version the calendar, rerun reconciliation,
and complete five-minute lifecycle visual audits before enabling research.
`engine.zone_v2.acceptance.require_acceptance` rejects incomplete/stale acceptance.

See `docs/FOUR_HOUR_SUPPLY_DEMAND_VISUAL_SPEC_V2.md` for frozen semantics. No existing
V1 implementation or research source identity is changed by this additive module.
