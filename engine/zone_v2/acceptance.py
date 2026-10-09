"""Fail-closed boundary between engineering diagnostics and outcome research."""

from engine.canonical import digest

REQUIRED = (
    "calendar_approved",
    "source_reconciled",
    "atr_initialized",
    "synthetic_tests_pass",
    "causal_audit_pass",
    "visual_audit_pass",
    "nonzero_both_sides",
    "deterministic",
    "legacy_preserved",
)


def assess(checks, configuration, implementation_hash):
    missing = [k for k in REQUIRED if checks.get(k) is not True]
    return dict(
        status="ACCEPTED" if not missing else "BLOCKED",
        research_allowed=not missing,
        failed_checks=missing,
        checks=checks,
        configuration_sha256=digest(configuration),
        implementation_sha256=implementation_hash,
    )


def require_acceptance(report, configuration, implementation_hash):
    """An explicit matching accepted report is required; missing checks fail."""
    expected = assess(report.get("checks", {}), configuration, implementation_hash)
    if report != expected or not expected["research_allowed"]:
        raise ValueError(
            "V2 provider acceptance incomplete or stale; forward research prohibited"
        )
