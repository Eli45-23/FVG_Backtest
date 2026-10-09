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


MECHANICAL_POLICY = "DEVELOPMENT_MECHANICAL_RESEARCH_V1"


def assess_mechanical(checks, configuration, implementation_hash):
    """Current opt-in research policy, authorized by the user on 2026-10-09.

    Historical assess()/require_acceptance() reports remain immutable/readable.
    Mechanical research requires engineering evidence, not human annotations.
    This is NOT a human-ground-truth or profitability acceptance declaration.
    """
    missing = [k for k in REQUIRED if checks.get(k) is not True]
    return dict(
        policy=MECHANICAL_POLICY,
        status="DEVELOPMENT_ONLY_NOT_VALIDATED",
        engineering_status="BLOCKED" if missing else "PASSED",
        human_ground_truth_required=False,
        research_allowed=not missing,
        allowed_segment="development",
        authorization="User removed human-label prerequisite on 2026-10-09",
        failed_checks=missing,
        checks=checks,
        configuration_sha256=digest(configuration),
        implementation_sha256=implementation_hash,
    )


def require_mechanical_acceptance(report, configuration, implementation_hash, segment):
    expected = assess_mechanical(
        report.get("checks", {}), configuration, implementation_hash
    )
    if (
        report != expected
        or not expected["research_allowed"]
        or segment != "development"
    ):
        raise ValueError("Matching engineering proof and Development scope required")
