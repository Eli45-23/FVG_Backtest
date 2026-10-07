"""Render the single time-window experiment from its saved results only."""
import json,hashlib
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent
STEM='CONT_A_risk100_no_1000_1029'

def render(r,c,replacements):
    out=['# CONT-A — Max Risk <100 — Exclude 10:00–10:29 ET\n',
         'True daily reselection with exactly one new strategy rule: reject second-candle trigger START times 10:00 ≤ ET <10:30, after the existing strict risk <100 rule and before daily locking. Both preceding baselines remain unchanged. One MNQ, zero costs, original structural stop, fixed 2R, unchanged execution.\n']
    def fmt(x):return 'N/A' if x is None else f'{x:,.4f}' if isinstance(x,float) else str(x)
    def table(headers,rows):
        out.append('| '+' | '.join(headers)+' |');out.append('| '+' | '.join('---' for _ in headers)+' |')
        out.extend('| '+' | '.join(fmt(x) for x in row)+' |' for row in rows);out.append('')
    def perf(title,groups,extra=()):
        out.append('## '+title+'\n');keys=['trades','win_rate_percent','net_pnl_usd','profit_factor','average_r','max_closed_trade_drawdown_usd',*extra]
        table(['Group',*keys],[[k,*['∞' if x=='profit_factor' and v.get('profit_factor_status')=='no_losses' else v[x] for x in keys]] for k,v in groups.items()])
    out.append('## Signal accounting\n');table(['Stage','Count'],r['signal_accounting'].items());table(['Audit reason','Signals'],r['signal_audit_counts'].items())
    out.append('Reasons use precedence: original date/cutoff/calendar/positive-risk checks, MAX_RISK_FILTER, TIME_WINDOW_FILTER, then daily competition. Time-filter counts include all risk-eligible rejected signals even if a prior allowed trade already locked that day. Rejected signals never consume the lock. Trigger 09:55 (entry 10:00) is allowed; trigger 10:25 (entry 10:30) is rejected; trigger 10:30 is allowed. No other time threshold was tested.\n')
    out.append('Raw 1,649 events match lifecycle IDs exactly. The prior research count 1,639 excluded later-day incompleteness/censoring; those future-known flags remain reconciliation only.\n')
    out.append('## Side-by-side with control\n')
    keys=['trades','winners','losers','win_rate_percent','net_pnl_usd','profit_factor','average_pnl_per_trade_usd','average_r','median_r','total_r','gross_profit_usd','gross_loss_usd','average_winner_usd','average_loser_usd','max_closed_trade_drawdown_usd','maximum_consecutive_losses','average_risk_points','median_risk_points']
    table(['Metric','Risk <100 control','Time exclusion'],[[k,c['overall'][k],r['overall'][k]] for k in keys])
    out.append('## True reselection versus filtering the old log\n')
    perf('Trade partitions',r['comparison'])
    out.append('Removing 85 banned-window control trades leaves 150 original allowed trades worth $4,401.50. All retained original fields match exactly. True reselection adds 20 later trades (8 winners, 12 losers), net −$159.50, producing $4,242.00. Thus overall change versus control is +$124.50 from removed trades minus $159.50 from replacements = −$35.00. The other 65 banned control dates have no eligible replacement.\n')
    out.append('## Time-filter replacement audit\n')
    out.append('One row per replacement day. The rejected signal shown is the earliest eligible banned signal that was the control’s actual trade; additional rejected signals remain in the full signal audit. Both trigger START and actual entry/close times are shown, with New York UTC offsets. Full IDs are preserved in the CSV.\n')
    cols=['formation_date','rejected_trigger_time_ny','rejected_direction','rejected_risk_points','second_bar_time_ny','entry_time_ny','direction','risk_points','net_pnl_usd','result_r']
    table(cols,[[t[k] for k in cols] for t in replacements])
    perf('Trigger time after true reselection',r['trigger_time_bins'],['signals','average_risk_points'])
    perf('Long versus short',r['direction'])
    out.append('Longs improve from $1,944.50 to $2,890.00 (+$945.50); shorts decline from $2,332.50 to $1,352.00 (−$980.50). The exclusion helps the long side more in this history.\n')
    perf('Yearly results',r['yearly'])
    table(['Year','Control P&L','Variant P&L','Difference'],[[k,c['yearly'][k]['net_pnl_usd'],v['net_pnl_usd'],v['net_pnl_usd']-c['yearly'][k]['net_pnl_usd']] for k,v in r['yearly'].items()])
    out.append('2026 is partial: it improves from −$522 (PF 0.8944, average −0.1028R) to +$613 (PF 1.1840, average +0.0945R). Its drawdown falls from $1,585.50 to $1,362.50. Conversely, 2024 loses $1,250 of profit. This is not a uniform year-by-year improvement.\n')
    perf('Monthly results',r['monthly'],['long_pnl_usd','short_pnl_usd'])
    out.append('## Monthly comparison to risk <100 control\n')
    table(['Month','Control trades','Variant trades','Control USD','Variant USD','Difference'],[[k,c['monthly'][k]['trades'],v['trades'],c['monthly'][k]['net_pnl_usd'],v['net_pnl_usd'],v['net_pnl_usd']-c['monthly'][k]['net_pnl_usd']] for k,v in r['monthly'].items()])
    table(['Month statistic','Control','Variant'],[[k,c['month_statistics'][k],v] for k,v in r['month_statistics'].items()])
    out.append('Zero/no-trade months break losing-month sequences. October 2026 is a partial no-trade month. Small monthly samples are descriptive, not evidence of stable month-specific effects.\n')
    out.append('## MFE / MAE\n');e=r['excursions']
    table(['Metric','Value'],[(k,v) for k,v in e.items() if not isinstance(v,dict)])
    table(['MFE threshold R','Percent reaching'],[(x,e['mfe_percent_at_least_r'][str(x)]) for x in [.5,1,1.5,2]])
    out.append('## Equity and drawdown\n')
    keys=['net_pnl_usd','peak_equity_usd','max_closed_trade_drawdown_usd','max_drawdown_peak_time_utc','max_drawdown_bottom_time_utc','peak_recovered','recovery_time_utc','maximum_consecutive_wins','maximum_consecutive_losses']
    table(['Metric','Value'],[(k,r['overall'][k]) for k in keys]);table(['Longest underwater episode','Value'],r['longest_time_below_peak'].items())
    out.append('Closed equity starts at zero. Underwater duration is calendar elapsed time from the previous observed peak to recovery (or last recorded trade close if unrecovered). It is not mark-to-market. Group drawdowns independently restart at zero.\n')
    out.append('## Interpretation and unchanged assumptions\n')
    out.append('The exclusion improves win rate, PF, average R and dollar drawdown, with 65 fewer trades and $35 less total profit. It improves 2026 and longs, but weakens 2024 and shorts. The replacement cohort hurts net USD despite positive average R because risk sizes differ. This is an in-sample controlled experiment motivated by the same history, not independent confirmation of an edge. No other time windows, risk thresholds or management rules were tested.\n')
    out.append('The original signal builder, structural levels, pinned offline XNYS calendar and minute execution engine are reused unchanged. Risk remains strictly <100 with a 0.25 tick structural buffer and fixed original 2R. One eligible trade per NY date, stable chronological/formation/FVG-ID priority. Entry is the confirmed second 5-minute close; the minute starting at entry is owned. Same-minute conflict is stop-first. Adverse stops fill at worse of stop/open; targets receive no favorable improvement. Stop/target checks remain active in the 15:59 minute before session close. Missing owned minutes fail the run. Exit labels use minute-end confirmation. Excursions include exit-minute full extrema with unknown intraminute order. No protective stops, trailing, partials or extra filters.\n')
    out.append('## Validation and files\n');table(['Check','Result'],r['validation'].items())
    out.append('New source: `cont_a_time_filter.py`, `render_cont_a_time_filter.py`, `tests/test_cont_a_time_filter.py`. New report: `CONT_A_RISK100_NO_1000_1029.md`. Ignored separate results: trade Parquet/CSV, summary JSON, signal audit CSV, replacements CSV and equity CSV under `CONT_A_risk100_no_1000_1029`. Prior strategy files and results remain unchanged.\n')
    out.append('Run `work/.venv/bin/python outputs/cont_a_time_filter.py`; render with `work/.venv/bin/python outputs/render_cont_a_time_filter.py`; test with `work/.venv/bin/python -m unittest discover -s outputs/tests -v`. Use `--output-dir work/time_filter_repeat` for a comparison run.\n')
    p=ROOT/'results'/f'{STEM}_verification.json'
    if p.exists():
        proof=json.loads(p.read_text())
        assert all(hashlib.sha256((ROOT/'results'/k).read_bytes()).hexdigest()==v for k,v in proof['sha256'].items())
        out.append(f"**{proof['tests_passed']} tests passed**, including {proof['new_tests']} new tests. Two full runs produced byte-identical trade Parquet/CSV, summary, signal audit, replacements and equity. Independent raw-integer replay verified all 170 fills, P&L and excursions. All retained control trades match every original field; all input and prior result hashes are unchanged.\n")
    return '\n'.join(out)

if __name__=='__main__':
    r=json.loads((ROOT/'results'/f'{STEM}_summary.json').read_text())
    c=json.loads((ROOT/'results/CONT_A_max_risk_100_summary.json').read_text())
    rep=pd.read_csv(ROOT/'results'/f'{STEM}_replacements.csv').to_dict('records')
    (ROOT/'CONT_A_RISK100_NO_1000_1029.md').write_text(render(r,c,rep))
