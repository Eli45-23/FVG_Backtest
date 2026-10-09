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
        status="PROVISIONAL_PENDING_HUMAN_GROUND_TRUTH",
        engineering_status="PASSED" if not missing else "BLOCKED",
        human_ground_truth_required=True,
        research_allowed=False,
        failed_checks=missing,
        checks=checks,
        configuration_sha256=digest(configuration),
        implementation_sha256=implementation_hash,
    )


def require_acceptance(report, configuration, implementation_hash):
    """V2 cannot authorize outcome research before a separate human-label review.

    Even every engineering check passing is insufficient. This task provides
    no boolean override for human acceptance; that protocol is a separate task.
    """
    expected = assess(report.get("checks", {}), configuration, implementation_hash)
    if report != expected or not expected["research_allowed"]:
        raise ValueError(
            "V2 remains provisional pending human ground truth; forward research prohibited"
        )
