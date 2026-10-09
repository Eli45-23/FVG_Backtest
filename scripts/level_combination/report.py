"""Predeclared opportunity-based inference and inspectable Lab report."""

import sys, json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
import numpy as np
from scripts.level_combination.run import P, write

LEVELS = ["PDH", "PDL", "PMH", "PML", "O5H", "O5L", "O15H", "O15L"]


def metrics(g):
    v = g[g.execution_status == "COMPLETED"]
    n = v.net_pnl_usd
    loss = -n[n < 0].sum()
    return dict(
        signals=len(g),
        trades=len(v),
        dates=v.date.nunique(),
        nonpositive=int(g.execution_status.eq("NON_POSITIVE_RISK").sum()),
        at_close=int(g.execution_status.eq("NO_POST_ENTRY_SESSION_MINUTES").sum()),
        missing_execution=int(
            g.execution_status.eq("EXECUTION_DATA_UNAVAILABLE").sum()
        ),
        win_pct=(n > 0).mean() * 100,
        net_usd=n.sum(),
        fees_usd=v.commission_usd.sum(),
        pf=n[n > 0].sum() / loss if loss else None,
        avg_net_r=v.result_r.mean(),
        median_net_r=v.result_r.median(),
        mean_risk=v.risk_points.mean(),
        median_risk=v.risk_points.median(),
        mean_mfe_r=v.mfe_r.mean(),
        mean_mae_r=v.mae_r.mean(),
        conflicts=int(v.same_minute_stop_target_conflict.eq(True).sum()),
    )


def grouped(frame, cols):
    return pd.DataFrame(
        [
            dict(zip(cols, key if isinstance(key, tuple) else (key,)), **metrics(g))
            for key, g in frame.groupby(cols, dropna=False, sort=True)
        ]
    )


def inference(g):
    days = g.groupby("date").effect.mean().to_numpy(float)
    if not len(days):
        return dict(
            events=0,
            dates=0,
            effect=None,
            ci_low=None,
            ci_high=None,
            p_value=1.0,
            small_sample=True,
        )
    mean = days.mean()
    rng = np.random.default_rng(1729)
    boot = days[rng.integers(0, len(days), (2000, len(days)))].mean(axis=1)
    return dict(
        events=len(g),
        dates=len(days),
        effect=mean,
        ci_low=np.quantile(boot, 0.025),
        ci_high=np.quantile(boot, 0.975),
        p_value=(1 + np.sum(np.abs(boot - mean) >= abs(mean))) / 2001,
        small_sample=len(days) < 30,
    )


def bh(p):
    p = np.asarray(p, float)
    order = np.argsort(p, kind="stable")
    out = np.empty(len(p))
    out[order] = np.minimum(
        1,
        np.minimum.accumulate((p[order] * len(p) / np.arange(1, len(p) + 1))[::-1])[
            ::-1
        ],
    )
    return out


def main():
    t = pd.read_csv(P / "all_executions.csv", low_memory=False)
    signals = pd.read_csv(P / "causal_signals.csv", low_memory=False)
    audit = pd.read_csv(P / "waiting_opportunities.csv")
    primary = t[(t.ticks == 1) & (t.target_r == 1)].copy()
    assert len(primary) == len(signals) and primary.entry_id.is_unique
    allsummary = grouped(t, ["level_type", "direction", "policy", "ticks", "target_r"])
    write("fee_slippage_sensitivity.csv", allsummary)
    write(
        "primary_results.csv",
        allsummary[(allsummary.ticks == 1) & (allsummary.target_r == 1)],
    )
    years = grouped(
        t[t.ticks == 1], ["level_type", "direction", "policy", "target_r", "year"]
    )
    write("yearly_results.csv", years)
    reject = t[t.policy == "REJECTION"]
    cluster = grouped(
        reject, ["level_type", "direction", "cluster_group", "ticks", "target_r"]
    )
    write("rejection_cluster_results.csv", cluster)
    write(
        "rejection_cluster_yearly.csv",
        grouped(
            reject[reject.ticks == 1],
            ["level_type", "direction", "cluster_group", "target_r", "year"],
        ),
    )
    evidence = []
    samples = []
    policyrows = []
    year_evidence = []
    for level in LEVELS:
        for side in ["UP", "DOWN"]:
            p = primary[(primary.level_type == level) & (primary.direction == side)]
            a = audit[(audit.level_type == level) & (audit.direction == side)]
            immediate = p[p.policy == "IMMEDIATE"].set_index("opportunity_id")
            waiting = p[p.policy == "WAIT_CLEAR_HOLD"].set_index("opportunity_id")
            paired = []
            for r in a.itertuples():
                i = immediate.loc[r.opportunity_id]
                w = waiting.loc[r.opportunity_id] if r.wait_entered else None
                complete = i.execution_status == "COMPLETED" and (
                    w is None or w.execution_status == "COMPLETED"
                )
                paired.append(
                    dict(
                        opportunity_id=r.opportunity_id,
                        date=r.date,
                        year=r.year,
                        level_type=level,
                        direction=side,
                        comparison="WAIT_MINUS_IMMEDIATE",
                        complete_pair=complete,
                        entered=r.wait_entered,
                        reason=r.reason,
                        immediate_net_r=i.result_r if complete else None,
                        waiting_net_r=(
                            (w.result_r if w is not None else 0) if complete else None
                        ),
                        immediate_usd=i.net_pnl_usd if complete else None,
                        waiting_usd=(
                            (w.net_pnl_usd if w is not None else 0)
                            if complete
                            else None
                        ),
                        effect=(
                            ((w.result_r if w is not None else 0) - i.result_r)
                            if complete
                            else None
                        ),
                    )
                )
            df = pd.DataFrame(paired)
            if len(df):
                policyrows.extend(paired)
                d = df[df.complete_pair].copy()
            else:
                d = pd.DataFrame(
                    columns=[
                        "date",
                        "effect",
                        "year",
                        "immediate_net_r",
                        "waiting_net_r",
                        "immediate_usd",
                        "waiting_usd",
                        "entered",
                    ]
                )
            e = dict(
                level_type=level,
                direction=side,
                comparison="WAIT_MINUS_IMMEDIATE",
                **inference(d),
                raw_opportunities=len(a),
                unmatched=0,
                excluded_execution=len(a) - len(d),
                event_mean_net_r=d.waiting_net_r.mean(),
                baseline_mean_net_r=d.immediate_net_r.mean(),
                waiting_entries=int(d.entered.sum()) if len(d) else 0,
            )
            evidence.append(e)
            for y in range(2020, 2024):
                year_evidence.append(
                    dict(
                        level_type=level,
                        direction=side,
                        comparison=e["comparison"],
                        year=y,
                        **inference(d[d.year == y]),
                    )
                )
            samples.extend(d.to_dict("records"))
            r = p[
                (p.policy == "REJECTION") & (p.execution_status == "COMPLETED")
            ].copy()
            strata = ["year", "time_bucket", "volatility_bucket", "full_level_coverage"]
            iso = r[r.cluster_group == "ISOLATED"]
            cl = r[r.cluster_group == "CLUSTERED"]
            base = (
                iso.groupby(strata, dropna=False)
                .agg(
                    baseline_mean=("result_r", "mean"), baseline_n=("result_r", "size")
                )
                .reset_index()
            )
            matched = cl.merge(base, on=strata, how="left", validate="many_to_one")
            supported = matched[matched.baseline_mean.notna()].copy()
            supported["effect"] = supported.result_r - supported.baseline_mean
            supported["comparison"] = "CLUSTERED_MINUS_MATCHED_ISOLATED"
            evidence.append(
                dict(
                    level_type=level,
                    direction=side,
                    comparison="CLUSTERED_MINUS_MATCHED_ISOLATED",
                    **inference(supported),
                    raw_opportunities=len(cl),
                    unmatched=len(cl) - len(supported),
                    excluded_execution=int(
                        (
                            (p.policy == "REJECTION")
                            & (p.execution_status != "COMPLETED")
                        ).sum()
                    ),
                    event_mean_net_r=supported.result_r.mean(),
                    baseline_mean_net_r=supported.baseline_mean.mean(),
                    waiting_entries=None,
                )
            )
            for y in range(2020, 2024):
                year_evidence.append(
                    dict(
                        level_type=level,
                        direction=side,
                        comparison="CLUSTERED_MINUS_MATCHED_ISOLATED",
                        year=y,
                        **inference(supported[supported.year == y]),
                    )
                )
            samples.extend(supported.to_dict("records"))
    evidence = pd.DataFrame(evidence)
    assert len(evidence) == 32
    evidence["q_value"] = bh(evidence.p_value)
    year_evidence = pd.DataFrame(year_evidence)
    pos = year_evidence.groupby(["level_type", "direction", "comparison"]).effect.apply(
        lambda x: int((x > 0).sum())
    )
    evidence = evidence.merge(
        pos.rename("positive_years").reset_index(),
        on=["level_type", "direction", "comparison"],
        validate="one_to_one",
    )
    write("statistical_evidence.csv", evidence)
    write("evidence_yearly.csv", year_evidence)
    write("paired_waiting_policies.csv", policyrows)
    write("statistical_rows.csv", samples)
    policy = pd.DataFrame(policyrows)
    opportunity = []
    for key, g in policy.groupby(["level_type", "direction"]):
        v = g[g.complete_pair]
        opportunity.append(
            dict(
                level_type=key[0],
                direction=key[1],
                opportunities=len(g),
                completed_pairs=len(v),
                confirmation_signals=int(g.entered.sum()),
                executable_waits=int(v.entered.sum()),
                confirmation_coverage_pct=100 * g.entered.mean(),
                immediate_usd_per_opportunity=v.immediate_usd.mean(),
                wait_usd_per_opportunity=v.waiting_usd.mean(),
                immediate_r_per_opportunity=v.immediate_net_r.mean(),
                wait_r_per_opportunity=v.waiting_net_r.mean(),
            )
        )
    write("waiting_opportunity_results.csv", opportunity)
    overlap = (
        signals[signals.policy != "WAIT_CLEAR_HOLD"]
        .groupby(["timestamp_utc", "direction", "policy"])
        .agg(
            events=("entry_id", "size"),
            levels=("level_type", lambda x: "|".join(sorted(x))),
        )
        .reset_index()
    )
    write("overlap_audit.csv", overlap)
    quality = (
        signals.groupby(["policy", "level_type", "direction"])
        .agg(
            events=("entry_id", "size"),
            dates=("date", "nunique"),
            atr_available=("atr14", "count"),
            full_coverage=("full_level_coverage", "sum"),
            cluster_contact_events=(
                "cluster_candle_contacts",
                lambda x: int((x > 0).sum()),
            ),
        )
        .reset_index()
    )
    write("context_coverage.csv", quality)
    room = primary.copy()
    room["room_group"] = np.where(
        room.room_atr.isna(),
        "UNAVAILABLE_OR_NO_KNOWN_FORWARD_LEVEL",
        np.where(room.room_atr <= 1, "WITHIN_1_ATR", "BEYOND_1_ATR"),
    )
    write(
        "room_diagnostics.csv",
        grouped(room, ["level_type", "direction", "policy", "room_group"]),
    )
    summary = dict(
        status="DEVELOPMENT_RESEARCH_NOT_VALIDATED",
        raw_events=int((signals.policy != "WAIT_CLEAR_HOLD").sum()),
        waiting_opportunities=len(audit),
        waiting_confirmation_signals=int(audit.wait_entered.sum()),
        waiting_entries=int(
            (
                (primary.policy == "WAIT_CLEAR_HOLD")
                & (primary.execution_status == "COMPLETED")
            ).sum()
        ),
        no_waiting_confirmation=int((~audit.wait_entered).sum()),
        primary_hypotheses=32,
        positive_corrected_comparisons=int(
            ((evidence.effect > 0) & (evidence.q_value < 0.05)).sum()
        ),
        negative_corrected_comparisons=int(
            ((evidence.effect < 0) & (evidence.q_value < 0.05)).sum()
        ),
        overlapping_candle_groups=int((overlap.events > 1).sum()),
        selected_strategy=None,
    )
    (P / "study_summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    make_report(
        summary,
        evidence,
        pd.DataFrame(opportunity),
        allsummary,
        cluster,
        years,
        year_evidence,
        quality,
        audit,
    )
    print(json.dumps(summary), flush=True)


def make_report(
    summary, evidence, opportunity, allsummary, cluster, years, ye, quality, audit
):
    primary = allsummary[(allsummary.ticks == 1) & (allsummary.target_r == 1)]
    positive = evidence[(evidence.effect > 0) & (evidence.q_value < 0.05)]
    headline = (
        "Some comparisons improve the measured result; improvement is not proof of a profitable strategy."
        if len(positive)
        else "This comparison does not establish a corrected positive advantage from combining levels."
    )
    notes = [
        headline,
        f"{summary['raw_events']:,} raw causal break/rejection signals. {summary['waiting_opportunities']:,} break opportunities had a known level ahead within one ATR. Waiting produced {summary['waiting_confirmation_signals']:,} confirmation signals and {summary['waiting_entries']:,} completed primary diagnostic trades; {summary['no_waiting_confirmation']:,} opportunities never confirmed.",
        f"The primary family contains 32 comparisons: {summary['positive_corrected_comparisons']} positive and {summary['negative_corrected_comparisons']} negative differences have BH q < 0.05. Compare absolute after-fee expectancy too: avoiding a losing trade can improve a policy even if its entered trades remain unprofitable.",
        "Development only, 2020–2023. Long and short are shown separately. This uses previously examined Development data, not independent validation. No Validation/OOS outcome access, final strategy choice, time filter or parameter search.",
        "Waiting freezes nearby levels at the original break and requires a later close beyond the farthest one, then an immediately adjacent full candle beyond it. Root-level reclaim, missing adjacency or session end cancels waiting. The original signal-candle stop is unchanged, so later entry commonly changes risk. No-entry has zero exposure in opportunity comparisons; conditional trade results must not replace that denominator.",
        "Clusters mean another known level within one ATR of the root, not two independent confirmations or proof both were touched. Missing levels cannot establish true isolation. Coverage and actual cluster-contact counts are exported. Rejections are matched to isolated observations by year, half-hour, volatility and full-level coverage; unsupported matches are reported, not filled.",
        "Primary execution: 1R target, 1 adverse tick on each side, $0.73 fee per side, one micro. Secondary diagnostics: 2R and 0/2 ticks, with no winner chosen. Stop is the ORIGINAL signal candle extreme plus one tick. Actual session-close exit; zero post-entry minutes is non-executable, not future-outcome filtering.",
        "The Primary trades table includes ALL immediate signals but only confirmed waiting signals; it is not a matched comparison. Use Waiting opportunities and Evidence for the same-root policy comparison. Independent overlapping diagnostic trades are not an investable portfolio. Dollar sums and PF cannot be added across levels as independent evidence. Stop-first one-minute fills are production engine fills, independently checked. MFE/MAE include exit-minute extrema whose order is unknown.",
        "Statistical effect is equal-date mean after-fee R difference, not hit-rate percentage points. CIs use 2,000 date-cluster bootstrap resamples; all 32 p-values share one BH correction. Rejection intervals condition on the empirical isolated benchmark; they do not account for refitting it. Year tables are descriptive, not separate corrected discoveries.",
    ]
    cols = [
        "level_type",
        "direction",
        "comparison",
        "events",
        "dates",
        "effect",
        "ci_low",
        "ci_high",
        "p_value",
        "q_value",
        "positive_years",
        "unmatched",
        "excluded_execution",
    ]
    sections = [
        ("Evidence", evidence[cols]),
        ("Waiting opportunities", opportunity),
        (
            "Primary trades",
            primary[
                [
                    "level_type",
                    "direction",
                    "policy",
                    "signals",
                    "trades",
                    "dates",
                    "net_usd",
                    "pf",
                    "avg_net_r",
                    "mean_risk",
                    "mean_mfe_r",
                    "mean_mae_r",
                ]
            ],
        ),
        (
            "Clustered rejection",
            cluster[(cluster.ticks == 1) & (cluster.target_r == 1)][
                [
                    "level_type",
                    "direction",
                    "cluster_group",
                    "signals",
                    "trades",
                    "dates",
                    "net_usd",
                    "pf",
                    "avg_net_r",
                    "mean_risk",
                ]
            ],
        ),
        ("Yearly evidence", ye),
        ("Yearly trades", years),
        ("Costs and targets", allsummary),
        ("Coverage", quality),
        (
            "Waiting cancellations",
            audit.groupby("reason").size().rename("opportunities").reset_index(),
        ),
    ]
    text = "# Do nearby levels improve entries?\n\n" + "\n\n".join(notes) + "\n"
    for title, df in sections:
        text += "\n## " + title + "\n\n" + markdown_table(df) + "\n"
    text += "\n## Reproduction\n\nSee docs/LEVEL_COMBINATION_REPRODUCTION.md. Exact source hashes, immutable source event IDs, original opportunity IDs, all fills and inference rows accompany this report. The protocol is frozen in docs/LEVEL_COMBINATION_STUDY_V1.md.\n"
    (P / "LEVEL_COMBINATION_REPORT.md").write_text(text)
    (ROOT / "outputs/LEVEL_COMBINATION_STUDY_V1.md").write_text(text)
    navigation = "".join(
        f'<button onclick="show({i})">{html.escape(title)}</button>'
        for i, (title, _) in enumerate(sections)
    )
    tables = "".join(
        f'<section class="tab" id="tab{i}" {"hidden" if i else ""}><h2>{html.escape(title)}</h2><p>Use the level and direction filters to inspect every comparison; exports retain all rows.</p><div class="scroll">{df.to_html(index=False,na_rep="—",float_format=lambda v:f"{v:,.5f}",classes="results",border=0)}</div></section>'
        for i, (title, df) in enumerate(sections)
    )
    data_links = [
        "LEVEL_COMBINATION_REPORT.md",
        "statistical_evidence.csv",
        "yearly_results.csv",
        "waiting_opportunity_results.csv",
        "causal_signals.csv",
        "all_executions.csv",
        "study_summary.json",
        "study_bundle.zip",
    ]
    links = " · ".join(
        f'<a href="{name}" download>{html.escape(name)}</a>' for name in data_links
    )
    # Simple forest figure with honest effect axis; full precision resides in table/export.
    finite = evidence[evidence.effect.notna()]
    lo = min(-0.05, finite.ci_low.min())
    hi = max(0.05, finite.ci_high.max())
    span = hi - lo
    x = lambda v: 310 + 650 * (v - lo) / span
    svg = f'<svg viewBox="0 0 1000 {50+len(finite)*24}" role="img" aria-label="After-fee R differences with date-clustered 95 percent confidence intervals"><line x1="{x(0)}" x2="{x(0)}" y1="25" y2="{45+len(finite)*24}" stroke="#94a3b8"/>'
    for i, r in enumerate(finite.itertuples()):
        y = 42 + i * 24
        color = "#34d399" if r.effect > 0 else "#fb7185"
        label = f"{r.level_type} {r.direction} " + (
            "Wait" if r.comparison.startswith("WAIT") else "Cluster"
        )
        svg += f'<text x="8" y="{y+4}" fill="#e2e8f0" font-size="12">{label}</text><line x1="{x(r.ci_low)}" x2="{x(r.ci_high)}" y1="{y}" y2="{y}" stroke="{color}"/><circle cx="{x(r.effect)}" cy="{y}" r="3" fill="{color}"/>'
    svg += f'<text x="310" y="14" fill="#cbd5e1" font-size="12">{lo:.3f}R</text><text x="930" y="14" fill="#cbd5e1" font-size="12">{hi:.3f}R</text></svg>'
    htmltext = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Level combinations · Development</title><style>body{margin:0;background:#0b1120;color:#e2e8f0;font:15px system-ui}main{max-width:1500px;margin:auto;padding:28px}h1{font-size:30px}p{max-width:1100px;line-height:1.6}a{color:#7dd3fc}nav{display:flex;flex-wrap:wrap;gap:6px;margin:20px 0}button,select{background:#1e293b;color:#e2e8f0;border:1px solid #475569;border-radius:4px;padding:9px;cursor:pointer}.scroll{overflow:auto;max-height:650px}table{border-collapse:collapse;font-size:13px;white-space:nowrap;width:100%}th,td{padding:9px;border-bottom:1px solid #334155;text-align:right}th{position:sticky;top:0;background:#1e293b}td:first-child,th:first-child{text-align:left}details{margin:18px 0}svg{max-width:1100px;width:100%}.hint{color:#94a3b8}</style><main><p class="hint">Strategy Research Lab · Development only · 2020–2023</p><h1>Do nearby levels improve entries?</h1>"""
    htmltext += (
        "".join("<p>" + html.escape(n) + "</p>" for n in notes[:3])
        + "<details><summary>Definitions, costs and interpretation limits</summary>"
        + "".join("<p>" + html.escape(n) + "</p>" for n in notes[3:])
        + "</details>"
    )
    htmltext += (
        "<details><summary>Compare effect and uncertainty visually</summary>"
        + svg
        + "</details>"
    )
    htmltext += (
        '<label>Level <select id="level" onchange="filterRows()"><option value="">All levels</option>'
        + "".join(f"<option>{l}</option>" for l in LEVELS)
        + '</select></label> <label>Direction <select id="direction" onchange="filterRows()"><option value="">Both directions</option><option>UP</option><option>DOWN</option></select></label> <button onclick="clearFilters()">Clear filters</button><nav>'
        + navigation
        + "</nav>"
        + tables
    )
    htmltext += (
        "<details><summary>Source preview and identity</summary><p>Source: verified eight-level Development study, causal entry records and daily level availability. Unit: one level-specific signal; multiple levels can share a candle. Source hashes and all source IDs are retained in the execution verification and signal export.</p>"
        + pd.read_csv(P / "causal_signals.csv", nrows=5)[
            [
                "date",
                "level_type",
                "direction",
                "policy",
                "original_timestamp",
                "known_level_count",
            ]
        ].to_html(index=False)
        + "</details><h2>Complete exports</h2><p>"
        + links
        + "</p></main>"
    )
    htmltext += """<script>function show(i){document.querySelectorAll('.tab').forEach((e,j)=>e.hidden=i!==j);filterRows()}function filterRows(){const l=document.getElementById('level').value,d=document.getElementById('direction').value;document.querySelectorAll('.results').forEach(t=>{const h=[...t.querySelectorAll('th')].map(x=>x.dataset.key||x.textContent);const li=h.indexOf('level_type'),di=h.indexOf('direction');t.querySelectorAll('tbody tr').forEach(r=>{const c=r.children;r.hidden=!!((l&&li>=0&&c[li].textContent!==l)||(d&&di>=0&&c[di].textContent!==d))})})}function clearFilters(){document.getElementById('level').value='';document.getElementById('direction').value='';filterRows()}</script></html>"""
    # Display labels only; preserve original keys for filters and exact values in CSV.
    pretty = """<script>
const labels={level_type:'Level',direction:'Direction',comparison:'Comparison',events:'Observations',dates:'Trading dates',effect:'Difference (net R)',ci_low:'95% CI low',ci_high:'95% CI high',p_value:'p-value',q_value:'BH q-value',positive_years:'Positive years',unmatched:'Unmatched',excluded_execution:'Unresolved / non-executable',opportunities:'Original opportunities',completed_pairs:'Comparable opportunities',confirmation_signals:'Confirmations',executable_waits:'Waiting trades',confirmation_coverage_pct:'Confirmed (%)',immediate_usd_per_opportunity:'Immediate $ / opportunity',wait_usd_per_opportunity:'Waiting $ / opportunity',immediate_r_per_opportunity:'Immediate R / opportunity',wait_r_per_opportunity:'Waiting R / opportunity',policy:'Entry policy',signals:'Signals',trades:'Trades',net_usd:'Net P&L ($)',fees_usd:'Fees ($)',pf:'Profit factor',avg_net_r:'Average net R',median_net_r:'Median net R',mean_risk:'Average risk (pts)',median_risk:'Median risk (pts)',mean_mfe_r:'Average MFE (R)',mean_mae_r:'Average MAE (R)',cluster_group:'Level context',target_r:'Target (R)',ticks:'Slippage ticks / side',nonpositive:'Invalid risk',at_close:'At session close',missing_execution:'Missing execution data',win_pct:'Win rate (%)',conflicts:'Stop/target conflicts',atr_available:'ATR available',full_coverage:'All 8 levels available',cluster_contact_events:'Other nearby level touched',reason:'Waiting outcome',small_sample:'Small sample',year:'Year'};
const values={IMMEDIATE:'Immediate break',WAIT_CLEAR_HOLD:'Clear + full hold',REJECTION:'Rejection',CLUSTERED:'Nearby level',ISOLATED:'Isolated',UNKNOWN:'Unknown',WAIT_MINUS_IMMEDIATE:'Waiting − immediate',CLUSTERED_MINUS_MATCHED_ISOLATED:'Clustered − matched isolated',CONFIRMED:'Clearance + hold confirmed',ROOT_RECLAIMED:'Original level reclaimed',SESSION_ENDED:'Session ended before confirmation'};
document.querySelectorAll('.results').forEach(t=>{const heads=[...t.querySelectorAll('th')];const keys=heads.map(h=>h.textContent);heads.forEach((h,i)=>{h.dataset.key=keys[i];h.textContent=labels[keys[i]]||keys[i].replaceAll('_',' ')});t.querySelectorAll('tbody tr').forEach(row=>[...row.cells].forEach((c,i)=>{const raw=c.textContent,key=keys[i];c.title=raw;if(values[raw])c.textContent=values[raw];else if(raw.trim()!==''&&Number.isFinite(Number(raw))){const n=Number(raw);if(key==='year')return;const decimals=['p_value','q_value'].includes(key)?5:(key.includes('usd')||key.includes('pct')||['mean_risk','median_risk'].includes(key))?2:Number.isInteger(n)?0:4;c.textContent=n.toLocaleString('en-US',{minimumFractionDigits:0,maximumFractionDigits:decimals})}}))});
</script>"""
    htmltext = htmltext.replace("</html>", pretty + "</html>")
    (P / "study.html").write_text(htmltext)


def markdown_table(df):
    def val(x):
        return (
            "—"
            if pd.isna(x)
            else f"{x:.6g}" if isinstance(x, (float, np.floating)) else str(x)
        )

    return (
        "| "
        + " | ".join(df.columns)
        + " |\n| "
        + " | ".join(["---"] * len(df.columns))
        + " |\n"
        + "\n".join(
            "| " + " | ".join(val(v) for v in r) + " |"
            for r in df.itertuples(index=False, name=None)
        )
    )


if __name__ == "__main__":
    main()
