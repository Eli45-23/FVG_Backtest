"""All registered hypotheses; daily denominators, month-block inference, no tuning."""

import sys, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.simple_discovery.run import P, write, save
from scripts.simple_discovery.core import HYPOTHESES, MODES
from scripts.zone_reaction_backtest.report import table


def block_evidence(g):
    if g.net_pnl_usd.isna().any():
        return dict(
            ci_low=None, ci_high=None, p_value=1.0, evidence_status="INCOMPLETE"
        )
    v = (
        g.groupby("month")
        .agg(total=("net_pnl_usd", "sum"), n=("net_pnl_usd", "size"))
        .to_numpy(float)
    )
    mean = float(g.net_pnl_usd.mean())
    rng = np.random.default_rng(1729)
    ix = rng.integers(0, len(v), size=(5000, len(v)))
    sums = v[ix].sum(axis=1)
    samples = sums[:, 0] / sums[:, 1]
    null = samples - mean
    return dict(
        ci_low=float(np.quantile(samples, 0.025)),
        ci_high=float(np.quantile(samples, 0.975)),
        p_value=float((1 + (null >= mean).sum()) / 5001),
        evidence_status="COMPLETE",
    )


def summary(d, t):
    d = d.sort_values("date")
    t = t.sort_values("entry_time_utc")
    n = len(t)
    net = t.net_pnl_usd
    loss = -net[net < 0].sum()
    complete = d.net_pnl_usd.notna().all()
    known = d.net_pnl_usd.dropna()
    eq = np.r_[0, known.cumsum()]
    dd = float((np.maximum.accumulate(eq) - eq).max())
    consecutive = mx = 0
    for x in net:
        consecutive = consecutive + 1 if x < 0 else 0
        mx = max(mx, consecutive)
    # Portfolio adverse mark is a known pre-exit observation, not the full exit-minute wick.
    peak = 500.0
    worst = 0.0
    for r in t.itertuples():
        peak = max(peak, float(r.balance_before))
        mark = (
            float(r.balance_before)
            - 0.73 * r.quantity
            - float(r.adverse_active_points) * 2 * r.quantity
        )
        worst = max(worst, peak - mark, peak - float(r.balance_after))
        peak = max(peak, float(r.balance_after))
    return dict(
        days=len(d),
        known_days=int(d.net_pnl_usd.notna().sum()),
        unknown_days=int(d.net_pnl_usd.isna().sum()),
        trades=n,
        unique_dates=t.date.nunique(),
        wins=int((net > 0).sum()),
        losses=int((net < 0).sum()),
        win_pct=float((net > 0).mean() * 100) if n else None,
        known_net_usd=float(known.sum()),
        avg_daily_net=float(known.mean()) if complete else None,
        avg_active_day_net=float(net.mean()) if n else None,
        net_pf=float(net[net > 0].sum() / loss) if loss else None,
        avg_net_r=float(t.result_r.mean()) if n else None,
        total_fees=float(t.commission_usd.sum()),
        ending_balance=(
            float(d.balance_after.iloc[-1])
            if complete and pd.notna(d.balance_after.iloc[-1])
            else None
        ),
        max_closed_dd=dd if complete else None,
        known_prefix_dd=dd,
        max_observed_intratrade_dd=worst if complete else None,
        winning_days=int((d.net_pnl_usd > 0).sum()),
        losing_days=int((d.net_pnl_usd < 0).sum()),
        zero_days=int((d.net_pnl_usd == 0).sum()),
        days_at_least_100=int((d.net_pnl_usd >= 100).sum()),
        max_losing_streak=mx,
        mean_quantity=float(t.quantity.mean()) if n else None,
        max_quantity=int(t.quantity.max()) if n else None,
        mean_planned_risk=float(t.planned_loss.mean()) if n else None,
        max_planned_risk=float(t.planned_loss.max()) if n else None,
        losses_over_75=int(t.loss_exceeds_75.sum()),
        margin_breaches=int(t.margin_breach.sum()),
        lockout_days=int(d.status.eq("CAPITAL_LOCKOUT").sum()),
        target_exits=int(t.exit_reason.eq("TARGET").sum()),
        stop_exits=int(t.exit_reason.eq("STOP").sum()),
        session_exits=int(t.exit_reason.eq("SESSION_CLOSE").sum()),
        complete=bool(complete),
    )


def main():
    d = pd.read_csv(P / "daily.csv")
    t = pd.read_csv(P / "trades.csv")
    a = pd.read_csv(P / "signal_audit.csv")
    raw = pd.read_csv(P / "raw_signals.csv")
    rows = []
    yearly = []
    directions = []
    for key, g in d.groupby(["hypothesis", "ticks", "mode"], sort=True):
        h, k, m = key
        tr = t[(t.hypothesis == h) & (t.ticks == k) & (t["mode"] == m)]
        rows.append(dict(hypothesis=h, ticks=int(k), mode=m, **summary(g, tr)))
        for year, y in g.groupby("year"):
            yearly.append(
                dict(
                    hypothesis=h,
                    ticks=int(k),
                    mode=m,
                    year=int(year),
                    **summary(y, tr[tr.year == year])
                )
            )
        if k == 1:
            for side, sg in tr.groupby("direction"):
                directions.append(
                    dict(
                        hypothesis=h,
                        mode=m,
                        direction=side,
                        trades=len(sg),
                        net_usd=float(sg.net_pnl_usd.sum()),
                        avg_r=float(sg.result_r.mean()),
                    )
                )
    write("scenario_summary.csv", rows)
    write("yearly.csv", yearly)
    write("direction.csv", directions)
    evidence = []
    for h in HYPOTHESES:
        dg = d[
            (d.hypothesis == h) & (d.ticks == 1) & (d["mode"] == "ONE_MICRO_DIAGNOSTIC")
        ]
        evidence.append(dict(hypothesis=h, **block_evidence(dg)))
    order = sorted(range(3), key=lambda i: evidence[i]["p_value"])
    prev = 0
    for rank, i in enumerate(order):
        prev = max(prev, min(1, (3 - rank) * evidence[i]["p_value"]))
        evidence[i]["holm_p"] = prev
    write("registered_evidence.csv", evidence)
    gates = []
    for h in HYPOTHESES:
        r = next(
            x
            for x in rows
            if x["hypothesis"] == h
            and x["ticks"] == 1
            and x["mode"] == "RISK_SIZED_200"
        )
        ev = next(e for e in evidence if e["hypothesis"] == h)
        yr = [
            y
            for y in yearly
            if y["hypothesis"] == h
            and y["ticks"] == 1
            and y["mode"] == "RISK_SIZED_200"
        ]
        positive = [max(0, y["known_net_usd"]) for y in yr]
        concentration = max(positive) / sum(positive) if sum(positive) > 0 else None
        checks = dict(
            complete=r["complete"],
            positive_net=r["known_net_usd"] > 0,
            positive_r=r["avg_net_r"] is not None and r["avg_net_r"] > 0,
            pf_above_one=r["net_pf"] is not None and r["net_pf"] > 1,
            positive_three_years=sum(
                y["complete"] and y["known_net_usd"] > 0 for y in yr
            )
            >= 3,
            no_single_year_dominance=concentration is not None and concentration <= 0.5,
            positive_ci=ev["ci_low"] is not None and ev["ci_low"] > 0,
            holm_significant=ev["holm_p"] < 0.05,
            no_margin_breach=r["margin_breaches"] == 0,
            no_terminal_lockout=r["lockout_days"] == 0,
        )
        qualifies = all(checks.values())
        objective = (
            qualifies and r["avg_daily_net"] is not None and r["avg_daily_net"] >= 100
        )
        gates.append(
            dict(
                hypothesis=h,
                status=(
                    "OBJECTIVE_SUPPORTED_IN_DEVELOPMENT"
                    if objective
                    else (
                        "PROMISING_BELOW_OBJECTIVE" if qualifies else "DOES_NOT_QUALIFY"
                    )
                ),
                positive_years=sum(
                    y["complete"] and y["known_net_usd"] > 0 for y in yr
                ),
                largest_positive_year_share=concentration,
                checks=checks,
                average_daily_objective_met=objective,
            )
        )
    save("qualification.json", gates)
    accounting = (
        a.groupby(["hypothesis", "ticks", "mode", "selection_status"])
        .size()
        .reset_index(name="signals")
    )
    write("signal_accounting.csv", accounting)
    counts = (
        raw.groupby("hypothesis")
        .agg(raw_signals=("signal_id", "size"), dates=("date", "nunique"))
        .reset_index()
    )
    write("signal_counts.csv", counts)
    primary = [r for r in rows if r["ticks"] == 1 and r["mode"] == "RISK_SIZED_200"]
    ones = [r for r in rows if r["ticks"] == 1 and r["mode"] == "ONE_MICRO_200"]
    diag = [r for r in rows if r["ticks"] == 1 and r["mode"] == "ONE_MICRO_DIAGNOSTIC"]
    cols = [
        "hypothesis",
        "days",
        "trades",
        "avg_daily_net",
        "known_net_usd",
        "ending_balance",
        "net_pf",
        "max_closed_dd",
        "lockout_days",
        "unknown_days",
    ]
    text = [
        "# Simple MNQ strategy search · $500 account / $75 risk",
        "",
        "**DEVELOPMENT_ONLY_NOT_VALIDATED**. Three preregistered candle patterns, four Development years. No strategy tuning after inspection. No claim of an exhaustive search.",
        "\n## Objective\n",
        "Average at least $100 net per full trading session, including losing/no-trade/lockout days, at most one entry daily. No deposits. $75 planned all-in risk, whole-contract sizing, structural stop, fixed 2R.",
        "\n## Primary risk-sized accounts ($200 assumed margin)\n",
        table(primary, cols),
        "\n## One-micro accounts ($200 assumed margin)\n",
        table(ones, cols),
        "\n## One-micro diagnostic without capital constraints\n",
        table(diag, cols),
        "\nThe diagnostic is not a feasible $500 account result. Zero days stay in every complete average. Unknown paths are NULL rather than silently removed. Closed drawdown does not represent worst intratrade account stress; see complete CSV.\n",
        "\n## Every registered hypothesis\n",
        table(counts.to_dict("records"), ["hypothesis", "raw_signals", "dates"]),
        "\n" + (ROOT / "docs/SIMPLE_STRATEGY_DISCOVERY_V1.md").read_text(),
        "\n## Every primary year\n",
        table(
            [y for y in yearly if y["ticks"] == 1 and y["mode"] == "RISK_SIZED_200"],
            [
                "hypothesis",
                "year",
                "days",
                "trades",
                "avg_daily_net",
                "known_net_usd",
                "net_pf",
                "lockout_days",
                "unknown_days",
            ],
        ),
        "\n## Diagnostic yearly results\n",
        table(
            [
                y
                for y in yearly
                if y["ticks"] == 1 and y["mode"] == "ONE_MICRO_DIAGNOSTIC"
            ],
            [
                "hypothesis",
                "year",
                "days",
                "trades",
                "avg_daily_net",
                "known_net_usd",
                "net_pf",
                "avg_net_r",
            ],
        ),
        "\n## Registered evidence family\n",
        table(
            evidence,
            ["hypothesis", "ci_low", "ci_high", "p_value", "holm_p", "evidence_status"],
        ),
        "\nCalendar-month block bootstrap (5,000 draws, seed 1729), ONE_MICRO_DIAGNOSTIC mean net/day. One-sided centered bootstrap p and Holm adjustment across exactly three hypotheses. Previously inspected Development is not independent new evidence.\n",
        "\n## Frozen qualification gates\n",
        "```json\n" + json.dumps(gates, indent=2) + "\n```",
        "\n## All costs and margin scenarios — not an optimization grid\n",
        table(
            rows,
            [
                "hypothesis",
                "mode",
                "ticks",
                "trades",
                "avg_daily_net",
                "ending_balance",
                "net_pf",
                "lockout_days",
                "unknown_days",
            ],
        ),
        "\n## Operational caveats\n",
        "Current Webull quote snapshot is not historical margin or account approval. The $200 primary margin is a scenario assumption; larger-margin cases are stress tests. Broker discretionary liquidation cannot be reproduced from OHLC. Stops can gap beyond $75. Missing owned minutes terminate known account paths; no made-up P&L or replenishment. No post-target or future-label information decides entries. At most one daily trade is enforced separately for each independently funded scenario. These scenarios must not be added together as a portfolio. Futures metadata, normal database and previous studies remain unchanged. No Validation or OOS outcomes accessed.",
        "\n## Reproduce\n",
        "Run `scripts/simple_discovery/run.py`, `report.py`, and `verify.py` with work/.venv/bin/python. Local protocol and source identities are required. Run/report/verify twice for byte equivalence. Raw local artifacts remain ignored by Git.",
    ]
    (P / "REPORT.md").write_text("\n".join(text) + "\n")
    data = dict(
        primary=primary,
        ones=ones,
        diagnostic=diag,
        scenarios=rows,
        yearly=yearly,
        evidence=evidence,
        gates=gates,
        counts=counts.to_dict("records"),
        daily=json.loads(d.to_json(orient="records")),
        trades=json.loads(t.to_json(orient="records")),
    )
    save(
        "summary.json", {k: v for k, v in data.items() if k not in ["daily", "trades"]}
    )
    (P / "study.html").write_text(
        (ROOT / "scripts/simple_discovery/viewer.html")
        .read_text()
        .replace(
            "/*DATA*/",
            json.dumps(data, separators=(",", ":"), allow_nan=False).replace(
                "</", "<\\/"
            ),
        )
    )
    print(json.dumps(dict(primary=primary, gates=gates), sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
