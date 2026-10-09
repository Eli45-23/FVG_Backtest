"""Audited fee diagnostics; reads only the explicitly named Development run artifacts."""

import json
from decimal import Decimal as D
import numpy as np
import pandas as pd
from pdh_fee_corrected_development import (
    ROOT,
    P,
    OLD,
    VERSION,
    FEE,
    read,
    save,
    sha,
    identity,
)


def csv(name, rows):
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    frame.to_csv(P / name, index=False, float_format="%.12g", lineterminator="\n")


def drawdown(values):
    curve = np.r_[0.0, np.cumsum(np.asarray(values, dtype=float))]
    drops = np.maximum.accumulate(curve) - curve
    bottom = int(np.argmax(drops))
    peak = int(np.argmax(curve[: bottom + 1]))
    return float(drops[bottom]), peak, bottom


def pf(values):
    a = np.asarray(values, dtype=float)
    loss = -a[a < 0].sum()
    return float(a[a > 0].sum() / loss) if loss else None


def stats(g):
    g = g.sort_values(["exit_time_utc", "trade_id"])
    n = len(g)
    out = dict(
        trades=n,
        wins=int((g.net_pnl_usd > 0).sum()),
        losses=int((g.net_pnl_usd < 0).sum()),
        breakeven=int((g.net_pnl_usd == 0).sum()),
        session_close_exits=int(g.exit_reason.eq("SESSION_CLOSE").sum()),
        win_rate=100 * float((g.net_pnl_usd > 0).mean()),
        gross_pnl_usd=float(g.gross_pnl_usd.sum()),
        total_fees_usd=float(g.commission_usd.sum()),
        net_pnl_usd=float(g.net_pnl_usd.sum()),
        gross_pf=pf(g.gross_pnl_usd),
        net_pf=pf(g.net_pnl_usd),
        gross_average_r=float(g.gross_result_r.mean()),
        net_average_r=float(g.result_r.mean()),
        median_net_r=float(g.result_r.median()),
        total_net_r=float(g.result_r.sum()),
        max_drawdown_usd=drawdown(g.net_pnl_usd)[0],
        max_drawdown_r=drawdown(g.result_r)[0],
        same_minute_conflicts=int(g.same_minute_stop_target_conflict.sum()),
        adverse_stop_gaps=int(g.adverse_stop_gap.sum()),
    )
    for name, col in [
        ("risk_points", "risk_points"),
        ("risk_usd", "risk_usd"),
        ("duration_minutes", "duration_minutes"),
        ("mfe_points", "mfe_points"),
        ("mae_points", "mae_points"),
        ("mfe_r", "mfe_r"),
        ("mae_r", "mae_r"),
    ]:
        out["average_" + name] = float(g[col].mean())
        out["median_" + name] = float(g[col].median())
    out.update(
        min_risk_points=float(g.risk_points.min()),
        max_risk_points=float(g.risk_points.max()),
    )
    return out


def table(frame, columns=None):
    if columns:
        frame = frame[columns]

    def fmt(x):
        if isinstance(x, (float, np.floating)):
            return f"{x:,.6f}".rstrip("0").rstrip(".")
        return str(x)

    return (
        "| "
        + " | ".join(frame.columns)
        + " |\n| "
        + " | ".join(["---"] * len(frame.columns))
        + " |\n"
        + "\n".join(
            "| " + " | ".join(fmt(x) for x in row) + " |"
            for row in frame.itertuples(index=False, name=None)
        )
    )


def report():
    source, spec = identity()
    gate = read(P / "reconciliation_gate.json")
    assert gate == read(OLD / "reconciliation_gate.json") and gate["passed"]
    rec = pd.read_csv(P / "signal_reconciliation.csv")
    assert len(rec) == 67 and rec.event_id.is_unique and rec.date.nunique() == 58
    assert rec.selection_reason.value_counts().to_dict() == {
        "SELECTED": 58,
        "DAILY_LIMIT_REACHED": 9,
    }
    bytime = {
        pd.Timestamp(x["timestamp_utc"]): x for x in read(P / "causal_candidates.json")
    }
    byid = {x["event_id"]: x for x in bytime.values()}
    oldruns = {
        x["slippage_ticks"]: x["run_id"] for x in read(OLD / "lab_runs.json")["runs"]
    }
    checks = []

    def check(name, passed):
        checks.append({"check": name, "passed": bool(passed)})
        assert passed, name

    frames = []
    fingerprints = {}
    artifact_hashes = {}
    audit = []
    info = read(P / "lab_runs.json")
    for item in info["runs"]:
        ticks = item["slippage_ticks"]
        folder = ROOT / "storage/artifacts" / item["run_id"]
        config = read(folder / "config.json")
        result = read(folder / "result.json")
        check(
            f"{ticks}: source identity",
            config["source_hash"] == spec["source_hash"]
            and config["frozen_strategy_version_id"] == VERSION,
        )
        check(
            f"{ticks}: frozen settings",
            all(
                config["settings"][k] == v
                for k, v in {
                    **spec["settings"],
                    "commission": "0.73",
                    "slippage": ticks,
                }.items()
            ),
        )
        check(f"{ticks}: fee provenance", config["actual_observed_fee_schedule"] == FEE)
        check(
            f"{ticks}: data hashes",
            config["dataset_identity"]["files"] == spec["dataset_identity"]["files"],
        )
        check(
            f"{ticks}: Development",
            config["segment"] == "development" and config["run_type"] == "DEVELOPMENT",
        )
        check(
            f"{ticks}: byte-identical independent repeat",
            (folder / "result.json").read_bytes()
            == (P / f"repeat_{ticks}/result.json").read_bytes(),
        )
        old = read(ROOT / "storage/artifacts" / oldruns[ticks] / "result.json")
        check(
            f"{ticks}: unchanged candidate engine audit",
            result["audit"] == old["audit"] and len(result["audit"]) == 67,
        )
        mapped = []
        for a in result["audit"]:
            c = bytime[pd.Timestamp(a["timestamp"])]
            mapped.append(c["event_id"])
            selected = c["event_id"] in gate["selected_event_ids"]
            check(
                f'{ticks}: candidate {c["event_id"]}',
                (
                    a["reason"] == "SELECTED"
                    if selected
                    else a["reason"] in ["DAILY_TRADE_LIMIT", "POSITION_OPEN"]
                ),
            )
            audit.append(
                dict(
                    slippage_ticks=ticks,
                    event_id=c["event_id"],
                    date=c["date"],
                    native_reason=a["reason"],
                    reason="SELECTED" if selected else "DAILY_LIMIT_REACHED",
                )
            )
        check(
            f"{ticks}: exact candidate set",
            len(set(mapped)) == 67 and set(mapped) == set(byid),
        )
        trades = result["trades"]
        check(
            f"{ticks}: exact selected identities",
            [t["metadata"]["candidate_event_id"] for t in trades]
            == gate["selected_event_ids"],
        )
        oldbyid = {t["metadata"]["candidate_event_id"]: t for t in old["trades"]}
        output = []
        for t in trades:
            md = t["metadata"]
            eid = md["candidate_event_id"]
            c = byid[eid]
            oldt = oldbyid[eid]
            entry, stop, target, risk = (
                D(t[k])
                for k in ["entry_price", "stop_price", "target_price", "risk_points"]
            )
            gross, net, fees = (
                D(t[k]) for k in ["gross_pnl_usd", "net_pnl_usd", "commission_usd"]
            )
            at = pd.Timestamp(t["entry_time_utc"])
            date = str(at.tz_convert("America/New_York").date())
            check(
                f"{ticks}/{eid}: Development date", "2020-01-01" <= date < "2024-01-01"
            )
            check(
                f"{ticks}/{eid}: confirmed entry",
                at
                == pd.Timestamp(md["confirmation_timestamp"])
                == pd.Timestamp(md["failure_bar_start"]) + pd.Timedelta(minutes=5),
            )
            check(
                f"{ticks}/{eid}: frozen bracket",
                stop == max(D(md["break_high"]), D(md["failure_high"])) + D(".25")
                and risk == stop - entry
                and risk > 0
                and target == entry - risk,
            )
            check(
                f"{ticks}/{eid}: frozen entry",
                entry == D(c["entry"]) - D(".25") * ticks,
            )
            check(
                f"{ticks}/{eid}: fee math",
                fees == D("1.46")
                and gross == (entry - D(t["exit_price"])) * 2
                and net == gross - fees,
            )
            check(
                f"{ticks}/{eid}: net R",
                abs(t["result_r"] - float(net / (risk * 2))) < 1e-12
                and abs(t["gross_result_r"] - float(gross / (risk * 2))) < 1e-12,
            )
            check(
                f"{ticks}/{eid}: unchanged fills and context",
                all(
                    t[k] == oldt[k]
                    for k in [
                        "entry_time_utc",
                        "entry_price",
                        "stop_price",
                        "target_price",
                        "exit_time_utc",
                        "exit_price",
                        "exit_reason",
                        "risk_points",
                        "risk_usd",
                        "gross_pnl_usd",
                        "mfe_points",
                        "mae_points",
                        "mfe_r",
                        "mae_r",
                        "duration_minutes",
                        "metadata",
                        "same_minute_stop_target_conflict",
                    ]
                ),
            )
            check(
                f"{ticks}/{eid}: no management",
                md["touch_number"] == 1
                and t["quantity"] == 1
                and t["management_event_count"] == 0
                and D(t["final_stop_price"]) == stop,
            )
            row = {k: v for k, v in t.items() if not isinstance(v, (dict, list))}
            row.update(
                run_id=item["run_id"],
                candidate_event_id=eid,
                root_event_id=md["root_event_id"],
                touch_number=1,
                entry_date=date,
                slippage_ticks=ticks,
                risk_atr=float(risk) / md["atr14"],
                atr14=md["atr14"],
                stop_distance_points=float(risk),
                adverse_stop_gap=t["exit_reason"] == "STOP"
                and D(t["exit_price"]) > stop + D(".25") * ticks,
                net_result_r=t["result_r"],
                fee_drag_r=float(fees / (risk * 2)),
            )
            for k in [
                "entry_price",
                "stop_price",
                "target_price",
                "exit_price",
                "risk_points",
                "risk_usd",
                "gross_pnl_usd",
                "net_pnl_usd",
                "commission_usd",
                "mfe_points",
                "mae_points",
            ]:
                row[k] = float(row[k])
            output.append(row)
        g = (
            pd.DataFrame(output)
            .sort_values(["exit_time_utc", "trade_id"])
            .reset_index(drop=True)
        )
        check(
            f"{ticks}: 58 unique selected dates",
            len(g) == 58 and g.entry_date.is_unique,
        )
        check(f"{ticks}: total fee", round(g.commission_usd.sum(), 2) == 84.68)
        csv(f"trades_{ticks}tick_actual_fee.csv", g)
        frames.append(g)
        fingerprints[str(ticks)] = {
            "result_sha256": sha(folder / "result.json"),
            "trade_csv_sha256": sha(P / f"trades_{ticks}tick_actual_fee.csv"),
            "request_sha256": sha(folder / "request.json"),
            "config_sha256": sha(folder / "config.json"),
        }
        artifact_hashes[str(folder.relative_to(ROOT))] = fingerprints[str(ticks)]
    # Same selected economic identities across all three scenarios; bracket risk/target
    # properly change with executed entry, never with fee deductions.
    for g in frames[1:]:
        check(
            "Cross-scenario signal identities",
            list(g.candidate_event_id) == list(frames[0].candidate_event_id),
        )
        check(
            "Cross-scenario entry timing/structural stops",
            g[["entry_time_utc", "stop_price"]].equals(
                frames[0][["entry_time_utc", "stop_price"]]
            ),
        )
    overall = []
    yearly = []
    economics = []
    riskrows = []
    largest = []
    ddrows = []
    for ticks, g in enumerate(frames):
        st = stats(g)
        overall.append(
            dict(
                slippage_ticks=ticks,
                candidate_events=67,
                unique_dates=58,
                selected_trades=58,
                same_day_rejected_signals=9,
                **st,
            )
        )
        for year in range(2020, 2024):
            yearly.append(
                dict(slippage_ticks=ticks, year=year, **stats(g[g.year == year]))
            )
        gross = st["gross_pnl_usd"]
        fee = st["total_fees_usd"]
        be = gross / (2 * len(g))
        economics.append(
            dict(
                slippage_ticks=ticks,
                fee_per_side=0.73,
                round_trip_fee=1.46,
                total_development_fees=fee,
                fees_pct_gross_net_before_fees=100 * fee / gross if gross else None,
                fees_pct_sum_positive_gross_trades=100
                * fee
                / g.loc[g.gross_pnl_usd > 0, "gross_pnl_usd"].sum(),
                average_fee_drag_r=float(g.fee_drag_r.mean()),
                break_even_all_in_fee_per_side=be,
                actual_fee_margin=be - 0.73,
                net_profit_per_trade=st["net_pnl_usd"] / len(g),
            )
        )
        top = g.sort_values(
            ["risk_points", "entry_time_utc"], ascending=[False, True]
        ).head(5)
        ddu, peak, bottom = drawdown(g.net_pnl_usd)
        ddr, rpeak, rbottom = drawdown(g.result_r)
        topids = set(top.candidate_event_id)
        intrough = g.iloc[peak:bottom]
        signed_contribution = -intrough.loc[
            intrough.candidate_event_id.isin(topids), "net_pnl_usd"
        ].sum()
        riskrows.append(
            dict(
                slippage_ticks=ticks,
                min=g.risk_points.min(),
                q25=g.risk_points.quantile(0.25),
                median=g.risk_points.median(),
                q75=g.risk_points.quantile(0.75),
                max=g.risk_points.max(),
                mean=g.risk_points.mean(),
                top5_net_pnl=top.net_pnl_usd.sum(),
                top5_pct_net_pnl=100 * top.net_pnl_usd.sum() / g.net_pnl_usd.sum(),
                top5_gross_risk_share_pct=100
                * top.risk_points.sum()
                / g.risk_points.sum(),
                top5_abs_pnl_share_pct=100
                * top.net_pnl_usd.abs().sum()
                / g.net_pnl_usd.abs().sum(),
                top5_signed_usd_drawdown_contribution=signed_contribution,
                top5_pct_usd_drawdown=100 * signed_contribution / ddu,
            )
        )
        for rank, (_, t) in enumerate(top.iterrows(), 1):
            largest.append(
                dict(
                    slippage_ticks=ticks,
                    rank=rank,
                    candidate_event_id=t.candidate_event_id,
                    entry_time_ny=t.entry_time_ny,
                    risk_points=t.risk_points,
                    risk_usd=t.risk_usd,
                    net_pnl_usd=t.net_pnl_usd,
                    result_r=t.result_r,
                    in_max_usd_drawdown=t.candidate_event_id
                    in set(intrough.candidate_event_id),
                    signed_dd_contribution=(
                        -t.net_pnl_usd
                        if t.candidate_event_id in set(intrough.candidate_event_id)
                        else 0
                    ),
                )
            )
        for unit, col, pk, bt, depth in [
            ("USD", "net_pnl_usd", peak, bottom, ddu),
            ("R", "result_r", rpeak, rbottom, ddr),
        ]:
            eq = np.r_[0, g[col].cumsum().to_numpy()]
            recover = next((i for i in range(bt + 1, len(eq)) if eq[i] >= eq[pk]), None)
            ddrows.append(
                dict(
                    slippage_ticks=ticks,
                    unit=unit,
                    max_drawdown=depth,
                    peak_time=(
                        "INITIAL_ZERO" if pk == 0 else g.iloc[pk - 1].exit_time_ny
                    ),
                    bottom_time=(
                        "INITIAL_ZERO" if bt == 0 else g.iloc[bt - 1].exit_time_ny
                    ),
                    recovery_time=g.iloc[recover - 1].exit_time_ny if recover else None,
                    peak_trade_count=pk,
                    bottom_trade_count=bt,
                )
            )
    for name, rows in [
        ("overall_results.csv", overall),
        ("yearly_fee_corrected_results.csv", yearly),
        ("fee_economics.csv", economics),
        ("risk_distribution.csv", riskrows),
        ("largest_risk_trades.csv", largest),
        ("drawdown_analysis.csv", ddrows),
        ("signal_selection_audit.csv", audit),
    ]:
        csv(name, rows)
    for path, expected in read(P / "preserved_prior_artifacts.json").items():
        check("Preserved " + path, sha(ROOT / path) == expected)
    # Rehash the shared raw files without decoding any reserved rows.
    for infofile in spec["dataset_identity"]["files"].values():
        path = ROOT / "outputs/data" / infofile["name"]
        if not path.is_absolute():
            path = ROOT / path
        check(
            "Unchanged market-data hash " + str(path), sha(path) == infofile["sha256"]
        )
    save(
        P / "verification.json", {"passed": len(checks), "failed": 0, "checks": checks}
    )
    primary = overall[1]
    econ = economics[1]
    development_checks = {
        "positive_average_net_r": primary["net_average_r"] > 0,
        "net_pf_above_one": primary["net_pf"] > 1,
        "positive_net_usd": primary["net_pnl_usd"] > 0,
        "drawdown_at_most_frozen_6_2788R": primary["max_drawdown_r"] <= 6.2788,
    }
    # No new thresholds: fail any requested broad Development screen -> do not advance.
    classification = (
        "CONDITIONAL_ADVANCE" if all(development_checks.values()) else "DO_NOT_ADVANCE"
    )
    save(
        P / "validation_readiness.json",
        {
            "classification": classification,
            "development_screen": development_checks,
            "validation_executed": False,
            "minimum_future_validation_trades": 10,
            "frozen_max_drawdown_r": 6.2788,
        },
    )
    caveats = """# Methodology and caveats

This is a rerun of the exact saved immutable Development strategy, not a new signal or historical trade subset. All three runs use the normal Lab worker and the user-supplied Webull all-in fee, represented by the engine commission field. Fee components are stored separately in each immutable run configuration. No website estimate was used.

Development uses New York dates [2020-01-01,2024-01-01). The existing loader predicate reads only this date range and up to 30 prior calendar days for causal warmup; local data begins in 2020. Whole-file identity hashing is byte inspection, not querying reserved rows. Session calendar metadata is not an outcome query. Prior work has inspected some later data; this task makes no claim of universal historical independence.

An adverse entry tick lowers short entry; structural stop stays fixed. Original risk therefore increases, and the fixed 1R target moves with executed entry. The adverse exit tick increases the short exit price. Fees never change signal eligibility, structural stop or target. Wins, losses and win rate use after-fee net dollars. Net R equals net dollars divided by original executed risk dollars; gross R uses pre-fee dollars. USD and R drawdowns include initial zero equity and are measured on chronologically closed trades; yearly drawdowns restart at zero for each year.

Same-minute stop/target conflicts remain conservative stop-first. Adverse stop gaps are stop exits worse than stop plus configured exit slippage. Stop/target activity starts with the minute beginning at confirmed entry. MFE/MAE include the full exit minute, whose intraminute ordering is unknown; they are gross market excursions, not fee-adjusted. All first-touch metadata and unchanged old zero-fee fills are checked trade-by-trade. Native POSITION_OPEN/DAILY_TRADE_LIMIT skips are exported as the frozen policy DAILY_LIMIT_REACHED with the native reason retained.

Fee as a percentage of gross Development profit uses aggregate pre-fee P&L (wins less losses). A separate percentage uses the sum of positive gross trades to remove ambiguity. Break-even fee is aggregate pre-fee P&L / (2 × completed trades). It is a dollar break-even point, not an R-expectancy threshold.

Risk-tail contribution to maximum drawdown is the signed loss of top-five-risk trades inside the actual peak-to-trough interval. Winning tail trades may reduce drawdown, giving negative contribution. This is attribution within the observed drawdown, not a counterfactual risk filter or another backtest. Fractions of tiny net P&L can exceed 100% and are not probabilities.

Fees are the supplied observed schedule, held fixed across the Development history; no claim is made that Webull charged this same schedule in every historical year. No historical bid/ask, latency or intraminute trade-order model is available. Fifty-eight trades provide limited evidence. No signal, stop, target, sizing, management or filter was modified, and no reserved-segment outcomes were requested. No production engine code changed, so no broad or legacy historical test suite was run that could query reserved periods.
"""
    (P / "methodology_and_caveats.md").write_text(caveats)
    readiness = f"""# Validation readiness: {classification}

Status remains DEVELOPMENT_ONLY_NOT_VALIDATED. Validation was not run.

Primary Development checks against the user-specified broad gate:

{table(pd.DataFrame([{'condition':k,'passed':v} for k,v in development_checks.items()]))}

Actual net expectancy is {primary['net_average_r']:.6f}R; net PF {primary['net_pf']:.6f}; net dollars ${primary['net_pnl_usd']:.2f}; R drawdown {primary['max_drawdown_r']:.6f} versus the frozen 6.2788R ceiling. Dollar break-even fee per side is ${econ['break_even_all_in_fee_per_side']:.6f}, leaving ${econ['actual_fee_margin']:.6f} above the actual $0.73. This is fee-sensitive Development evidence, not validation.

The classification is conditional when all listed screens pass because the remaining dollar fee margin is thin, not because of a new numerical gate. A failing screen would mean DO_NOT_ADVANCE. Conditional advancement permits only a separately authorized test of the unchanged specification; it does not permit rule repair on Validation. No new threshold or filter is proposed here. The prior preregistration additionally discussed three positive Development years and year-concentration; all four after-fee years are disclosed in the report. The latest user-specified fixed 6.2788R ceiling is preserved; it is not recomputed from fee-corrected drawdown.

If a future Validation run is separately authorized, preserve all rules and actual costs, require at least 10 trades (otherwise inconclusive), positive average net R, net PF >1, positive net dollar P&L and drawdown <=6.2788R. No changes after seeing Validation. The saved source currently guards Development dates: a separately approved, immutable date-guard-only source version would be needed. No OOS authorization follows automatically.
"""
    (P / "validation_readiness.md").write_text(readiness)
    of = pd.DataFrame(overall)
    yf = pd.DataFrame(yearly)
    report_text = f"""# PDH Failed Break Short v1 — fee-corrected Development

Status: **DEVELOPMENT_ONLY_NOT_VALIDATED**. Readiness: **{classification}**.

Primary one-tick result: **${primary['net_pnl_usd']:.2f} net**, **{primary['net_pf']:.6f} net PF**, **{primary['net_average_r']:.6f} average net R**. This thin dollar result must be assessed alongside risk-weighted expectancy, drawdown and all four years.

## Frozen identity and reconciliation

Immutable source version: `{VERSION}`; source SHA256 `{spec['source_hash']}`. No source or engine change in this task. The repository-wide engine fingerprint has changed since the historical run as the Lab gained other capabilities; exact same-slippage fills and metadata are independently required to match those earlier results. Both engine identities are recorded. Dataset `research_2020_2026`; Development NY dates 2020-01-01 inclusive to 2024-01-01 exclusive. All three saved run IDs/configuration hashes are in the reproducibility manifest.

**67 exact candidates / 58 unique dates / 58 selected trades / 9 DAILY_LIMIT_REACHED rejections** in every scenario. Missing=0, extra=0, duplicate mappings=0. Candidate preflight reproduced the original gate before run results were interpreted. All selected signals remain first-touch-episode events. Audit-native skip reasons are retained separately.

## Actual fee schedule

Commission $0.25 + exchange $0.35 + clearing $0.12 + NFA $0.01 = **$0.73 per side per micro**, **$1.46 round trip**. User-supplied actual observed fee; one micro, no inferred broker charge.

## Cost scenarios

{table(of,['slippage_ticks','trades','wins','losses','session_close_exits','win_rate','gross_pnl_usd','total_fees_usd','net_pnl_usd','gross_pf','net_pf','gross_average_r','net_average_r','median_net_r','total_net_r','max_drawdown_usd','max_drawdown_r'])}

## All requested diagnostic metrics

{table(of.set_index('slippage_ticks').T.reset_index().rename(columns={'index':'metric',0:'0 ticks',1:'1 tick PRIMARY',2:'2 ticks'}))}

## Year-by-year, all scenarios

{table(yf,['slippage_ticks','year','trades','wins','losses','win_rate','gross_pnl_usd','total_fees_usd','net_pnl_usd','net_pf','net_average_r','total_net_r','max_drawdown_usd','max_drawdown_r','average_risk_points','median_risk_points'])}

2022 is shown without exclusion or repair. The combined result does not establish robustness.

## Fee economics

{table(pd.DataFrame(economics))}

Primary total fee drag is ${primary['total_fees_usd']:.2f}; average {econ['average_fee_drag_r']:.6f}R per trade. Break-even fee is ${econ['break_even_all_in_fee_per_side']:.6f} per side, leaving only ${econ['actual_fee_margin']:.6f} per side above actual cost. Net dollars per trade: ${econ['net_profit_per_trade']:.6f}. This is fee-sensitive.

## Structural risk and concentration

{table(pd.DataFrame(riskrows))}

Top five largest-risk trades in the primary scenario:

{table(pd.DataFrame(largest).query('slippage_ticks == 1'))}

The primary top-five-risk trades contribute ${riskrows[1]['top5_net_pnl']:.2f} against ${primary['net_pnl_usd']:.2f} total net P&L; their share of absolute trade P&L is {riskrows[1]['top5_abs_pnl_share_pct']:.2f}%. Dollar profit is a small residual of large wins/losses; risk variation matters materially. Average R weights each trade equally after dividing by its own risk, while fixed-quantity dollar P&L gives large-risk trades much more monetary weight. Thus positive average R does not imply a comfortable dollar edge. These trades remain included. Signed contribution to the actual maximum USD drawdown is ${riskrows[1]['top5_signed_usd_drawdown_contribution']:.2f}. No alternate risk-filtered simulation was run.

## Drawdown intervals

{table(pd.DataFrame(ddrows))}

## Readiness and verification

{classification}. See `validation_readiness.md` for the unchanged gate and each pass/fail condition. The primary broad screens pass, but only a thin dollar margin remains after fees. The designation is conditional on a separately authorized, unchanged Validation test, not a claim that the strategy is validated or economically robust.

Three independent worker repeats produced byte-identical full result JSON. Existing no-fee fills, entries, stops, targets, excursions and signal audits matched exactly within each same-slippage scenario; only costs and derived net metrics changed. {len(checks)} report assertions passed. Prior Development artifacts and source market-data SHA256 hashes remained unchanged. No production engine changes, paid download, Validation/OOS outcome access or push occurred. See `methodology_and_caveats.md` for execution and fee limitations.
"""
    (P / "FEE_CORRECTED_DEVELOPMENT_REPORT.md").write_text(report_text)
    files = {
        str(p.relative_to(P)): sha(p)
        for p in sorted(P.glob("*"))
        if p.is_file()
        and p.name
        not in ("reproducibility_manifest.json", "report_repeat_verification.json")
        and p.suffix in (".csv", ".json", ".md")
    }
    save(
        P / "reproducibility_manifest.json",
        {
            "version_id": VERSION,
            "source_hash": spec["source_hash"],
            "dataset_identity": spec["dataset_identity"],
            "engine_version": read(P / "frozen_strategy_identity.json")[
                "engine_version"
            ],
            "runs": info["runs"],
            "run_artifact_fingerprints": artifact_hashes,
            "analysis_source_hashes": {
                str(p.relative_to(ROOT)): sha(p)
                for p in [
                    ROOT / "scripts/pdh_fee_corrected_development.py",
                    ROOT / "scripts/pdh_fee_corrected_report.py",
                    ROOT / "tests/test_pdh_fee_diagnostics.py",
                ]
            },
            "files": files,
            "scope": "Development only; no Validation/OOS outcome query",
            "independent_worker_repeats_byte_identical": True,
            "prior_artifacts_unchanged": True,
            "production_code_changed": False,
        },
    )
    print(
        of[
            [
                "slippage_ticks",
                "net_pnl_usd",
                "net_pf",
                "net_average_r",
                "max_drawdown_usd",
                "max_drawdown_r",
            ]
        ].to_string(index=False)
    )
    print(classification, len(checks), "checks")
