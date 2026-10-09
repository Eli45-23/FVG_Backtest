"""The predeclared decision rule; sensitivities cannot override the primary."""


def classify(metrics, interval, unresolved, protocol, integrity=True):
    checks = {
        "integrity": bool(integrity and unresolved == 0),
        "sample": metrics["trades"] >= protocol["min_trades"]
        and metrics["unique_dates"] >= protocol["min_dates"],
        "net_usd_positive": metrics["net_usd"] > 0,
        "mean_net_r_positive": metrics["avg_net_r"] is not None
        and metrics["avg_net_r"] > 0,
        "net_pf_above_one": metrics["profit_factor"] is not None
        and metrics["profit_factor"] > 1
        or metrics["losses"] == 0
        and metrics["wins"] > 0,
        "r_drawdown": metrics["max_dd_r"] <= protocol["max_drawdown_r"],
        "mean_r_lower_ci_positive": interval["mean_r_ci_low"] is not None
        and interval["mean_r_ci_low"] > 0,
    }
    if not checks["integrity"]:
        status = "INCONCLUSIVE_INTEGRITY"
    elif not checks["sample"]:
        status = "INCONCLUSIVE_SAMPLE"
    elif not all(
        checks[k]
        for k in [
            "net_usd_positive",
            "mean_net_r_positive",
            "net_pf_above_one",
            "r_drawdown",
        ]
    ):
        status = "VALIDATION_GATE_FAILED"
    elif not checks["mean_r_lower_ci_positive"]:
        status = "CONDITIONAL_VALIDATION_EVIDENCE"
    else:
        status = "VALIDATION_SUPPORTS_FROZEN_HYPOTHESIS"
    return {"classification": status, "checks": checks}
