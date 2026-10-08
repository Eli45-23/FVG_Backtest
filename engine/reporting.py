"""Additional generic display metrics for the opt-in executor."""

import statistics


def extend(summary, trades, signals, events, metrics):
    for minute in range(660, 960, 30):
        label = (
            f"{minute//60:02}:{minute%60:02}-{(minute+29)//60:02}:{(minute+29)%60:02}"
        )
        clock = (
            lambda t: t["second_bar_time_ny"].hour * 60 + t["second_bar_time_ny"].minute
        )
        summary["trigger_time_bins"][label] = {
            **metrics.performance(
                [t for t in trades if minute <= clock(t) < minute + 30]
            ),
            "signals": sum(minute <= clock(s) < minute + 30 for s in signals),
        }
    pnl = [float(t["net_pnl_usd"]) for t in trades]
    equity = trough = runup = 0
    for value in pnl:
        equity += value
        trough = min(trough, equity)
        runup = max(runup, equity - trough)
    summary["overall"].update(
        median_trade_usd=statistics.median(pnl) if pnl else None,
        max_runup_usd=runup if pnl else None,
    )
    for f in ("mfe_r", "mae_r"):
        summary["excursions"]["average_" + f] = (
            statistics.mean(t[f] for t in trades) if trades else None
        )
    summary["management"] = {
        "events": len(events),
        "management_exit_count": sum(t["management_exit"] for t in trades),
        "average_locked_r_at_exit": (
            statistics.mean(t["locked_r_at_exit"] for t in trades) if trades else None
        ),
        "profit_protected_usd": None,
        "version": "extended-v1-next-minute",
    }
