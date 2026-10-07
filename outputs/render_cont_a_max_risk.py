"""Render the controlled variant report without running any strategy."""
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent

def render(r,replacements):
    out=['# CONT-A — Second-Candle Continuation — Max Risk <100\n',
    'A true controlled backtest, not a filtered baseline CSV. The only changed strategy rule is original structural risk strictly below 100 points, applied before the daily lock. Baseline source, results and all validated inputs remain unchanged. Zero costs, one MNQ, unchanged original structural stop and fixed 2R target.\n']
    def fmt(x):
        if x is None:return 'N/A'
        if isinstance(x,float):return f'{x:,.4f}'
        return str(x)
    def table(headers,rows):
        out.append('| '+' | '.join(headers)+' |');out.append('| '+' | '.join('---' for _ in headers)+' |')
        out.extend('| '+' | '.join(fmt(v) for v in row)+' |' for row in rows);out.append('')
    def perf(title,groups,extra=()):
        out.append('## '+title+'\n')
        keys=['trades','win_rate_percent','net_pnl_usd','profit_factor','average_r','max_closed_trade_drawdown_usd',*extra]
        table(['Group',*keys],[[k,*['∞' if x=='profit_factor' and v.get('profit_factor_status')=='no_losses' else v[x] for x in keys]] for k,v in groups.items()])
    out.append('## Signal accounting\n');table(['Stage','Count'],r['signal_accounting'].items())
    table(['Audit reason','Signals'],r['signal_audit_counts'].items())
    out.append('Cutoff and calendar precede risk eligibility. All otherwise-eligible signals with risk ≥100 are marked MAX_RISK_FILTER, including signals occurring after an actual entry; only risk-eligible later signals count as daily-lock competition. Rejection never consumes the daily slot. The baseline selector is reused to preserve chronological order and oldest-formation/FVG-ID ties. No signal generation or execution implementation is copied or altered.\n')
    out.append('Raw 1,649 events still exactly match lifecycle IDs. The prior qualified 1,639 excludes 9 later-day incomplete histories and 1 censored date; those future-known qualifications remain reconciliation only, not filters.\n')
    out.append('## Baseline and historical-subset comparison\n')
    keys=['trades','winners','losers','win_rate_percent','net_pnl_usd','gross_profit_usd','gross_loss_usd','profit_factor',
          'average_pnl_per_trade_usd','average_r','median_r','total_r','average_winner_usd','average_loser_usd',
          'max_closed_trade_drawdown_usd','maximum_consecutive_losses','average_risk_points','median_risk_points']
    groups={'Original baseline':r['comparison']['baseline'],'Old descriptive <100 subset':r['comparison']['historical_under_100_subset'],'True <100 variant':r['overall']}
    table(['Metric',*groups],[[k,*[v[k] for v in groups.values()]] for k in keys])
    rep=r['comparison']['replacement_trades'];o=r['overall']
    out.append(f"All 222 old subset trades remain byte-for-value identical across their original fields. The true run adds **{rep['trades']}** replacement trades with **${rep['net_pnl_usd']:,.2f}** net P&L ({rep['winners']} winners, {rep['losers']} losers). Thus $4,303.50 + ({rep['net_pnl_usd']}) = ${o['net_pnl_usd']:,.2f}. Of 41 original wide-risk trade dates, 13 receive a later eligible trade and 28 have no qualifying replacement. The variant retains original signal-derived trade IDs for matching; its separate filename identifies the variant.\n")
    out.append('## Replacement-trade audit\n')
    out.append('Full identifiers and all trade details are in the ignored replacement CSV. Times below are America/New_York, including UTC offset.\n')
    cols=['formation_date','direction','rejected_baseline_entry_time_ny','rejected_baseline_risk_points','entry_time_ny','risk_points','net_pnl_usd','exit_reason']
    table(cols,[[t[c] for c in cols] for t in replacements])
    perf('Trigger time (second candle start, New York)',r['trigger_time_bins'],['signals','average_risk_points'])
    out.append('The true 10:00–10:29 result is −$124.50, PF 0.9792, versus +$529 in the old subset. Five replacement trades in this window all lost, totaling −$653.50. Eight replacements in 10:30–10:59 added +$627.00.\n')
    out.append('Signals in this table are eligible after the strict max-risk filter and before the daily lock. The 10:00–10:29 window remains included.\n')
    perf('Long versus short',r['direction'],['average_risk_points'])
    perf('Yearly',r['yearly'])
    out.append('2026 improves from baseline −$1,238 to −$522, but remains negative. Its six replacements all lost (−$830), reversing the old subset’s +$308. Long P&L improves from −$558.50 to +$1,944.50; short P&L improves from +$1,084 to +$2,332.50.\n')
    out.append('2026 is partial through the existing input period ending 2026-10-06 (exclusive). Group drawdowns restart from zero within each group.\n')
    perf('Monthly',r['monthly'],['long_pnl_usd','short_pnl_usd'])
    table(['Monthly statistic','Value'],r['month_statistics'].items())
    out.append('The longest losing-month sequence runs December 2024 through March 2025 (four months). A zero-P&L or no-trade month breaks a losing-month sequence. October 2026 is partial with no trades.\n')
    perf('Entry distance from favorable FVG boundary (points)',{k:r['entry_distance_buckets'][k] for k in ['0-25','25-50','50-75','75-100','100+']})
    out.append('Distance is entry − FVG top for longs and FVG bottom − entry for shorts. Bins include the lower bound and exclude the upper bound. This is descriptive only. Risk = distance − first-bar clearance + 0.25, so distance can exceed 100 despite risk <100.\n')
    out.append('## MFE / MAE\n')
    exc=r['excursions'];table(['Metric','Value'],[(k,v) for k,v in exc.items() if not isinstance(v,dict)])
    table(['MFE points reached','Percent'],[(n,exc['mfe_percent_at_least_points'][str(n)]) for n in [25,50,75,100,150,200]])
    table(['MFE original R reached','Percent'],[(n,exc['mfe_percent_at_least_r'][str(n)]) for n in [.5,1,1.5,2]])
    out.append('## Equity\n')
    table(['Metric','Value'],[(k,o[k]) for k in ['net_pnl_usd','peak_equity_usd','max_closed_trade_drawdown_usd',
         'max_drawdown_peak_time_utc','max_drawdown_bottom_time_utc','peak_recovered','recovery_time_utc',
         'maximum_consecutive_wins','maximum_consecutive_losses']])
    table(['Longest time below prior peak','Value'],r['longest_time_below_peak'].items())
    out.append('Underwater duration is elapsed calendar time from the prior observed equity peak to the first equal-or-higher closed equity, or to the last recorded close if unrecovered. Initial zero is anchored at first entry if necessary. It is not mark-to-market. The longest episode and maximum-dollar drawdown need not be the same episode.\n')
    out.append('## Interpretation\n')
    out.append(f"The single-variable change improves net P&L by ${o['net_pnl_usd']-r['comparison']['baseline']['net_pnl_usd']:,.2f} and lowers maximum closed drawdown, while the longest losing streak increases from 10 to {o['maximum_consecutive_losses']}. Replacement trades slightly reduce profit relative to the historical subset. The long side improves materially, but 2026 remains weaker than earlier years. This is an in-sample controlled comparison prompted by research on the same history, not independent evidence of a durable edge. No other thresholds or filters were tested.\n")
    out.append('## Unchanged execution and reproducibility\n')
    out.append('The variant calls the original signal builder, level calculation, calendar, execution and metrics functions. Entry uses the confirmed second-candle close; ownership starts with the 1-minute bar beginning at entry. Stop-first resolves same-minute conflicts. Adverse gaps fill at the worse of stop/open; targets receive no favorable improvement. The 15:59 minute is evaluated before session-close exit. Missing owned minutes fail the run. Exit timestamps indicate minute-end confirmation. MFE/MAE include the full exit-minute range, whose intraminute order is unknown. No stop movement, protection, trailing, partial exits, candle-strength, ATR, distance or new time filters are present.\n')
    out.append('The original pinned exchange_calendars/XNYS full-session schedule is reused offline. Risk and executable prices use Decimal and 0.25-point ticks. 99.75 is allowed; 100.00 and 100.25 are rejected. Costs remain zero.\n')
    table(['Validation','Result'],r['validation'].items())
    out.append('Run: `work/.venv/bin/python outputs/cont_a_max_risk.py`. Render: `work/.venv/bin/python outputs/render_cont_a_max_risk.py`. Tests: `work/.venv/bin/python -m unittest discover -s outputs/tests -v`. A second run can use `--output-dir work/cont_a_max_risk_repeat`. No baseline runner is invoked.\n')
    out.append('New files: `cont_a_max_risk.py`, `render_cont_a_max_risk.py`, `tests/test_cont_a_max_risk.py`, and this report. All variant trades, summary, audit, replacements, equity and verification receipts remain ignored under `outputs/results/`. No baseline source or results files are changed.\n')
    receipt=ROOT/'results/CONT_A_max_risk_100_verification.json'
    if receipt.exists():
        proof=json.loads(receipt.read_text())
        import hashlib
        if not all(hashlib.sha256((ROOT/'results'/name).read_bytes()).hexdigest()==value for name,value in proof['sha256'].items()):raise ValueError('Verification receipt is stale')
        out.append(f"Completed verification: **{proof['tests_passed']} tests passed**, including {proof['new_variant_tests']} new variant tests. Two full runs yielded byte-identical trade Parquet, trade CSV, summary, audit, replacements and equity files. Independent raw-integer execution verification matched all {o['trades']} trades. Protected baseline files and inputs were unchanged.\n")
    return '\n'.join(out)

if __name__=='__main__':
    r=json.loads((ROOT/'results/CONT_A_max_risk_100_summary.json').read_text())
    replacement=pd.read_csv(ROOT/'results/CONT_A_max_risk_100_replacement_trades.csv').to_dict('records')
    (ROOT/'CONT_A_MAX_RISK_100.md').write_text(render(r,replacement))
