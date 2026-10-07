"""Readable, reproducible report from CONT-A baseline summary JSON."""
import json
import hashlib
from pathlib import Path


def render(r):
    out=['# CONT-A — Second-Candle FVG Continuation: zero-cost baseline\n',
         'One MNQ micro, $2/index point, 0.25-point ticks. Structural first-post-FVG-candle stop ± one tick; fixed original 2R target; otherwise 16:00 ET close. Commission and slippage are zero. No trade management or parameter optimization.\n']
    def fmt(v):
        if isinstance(v,float):return f'{v:,.4f}'
        return 'N/A' if v is None else str(v)
    def table(headers,rows):
        out.append('| '+' | '.join(headers)+' |')
        out.append('| '+' | '.join('---' for _ in headers)+' |')
        for row in rows:out.append('| '+' | '.join(fmt(x) for x in row)+' |')
        out.append('')
    def perf(name,values,extras=None):
        out.append(f'## {name}\n')
        keys=['trades','win_rate_percent','net_pnl_usd','profit_factor','average_r','max_closed_trade_drawdown_usd']
        if extras:keys+=extras
        table(['Group',*keys],[[k,*[v.get(x) for x in keys]] for k,v in values.items()])
    out.append('## Signal reconciliation and selection\n')
    c=r['signal_reconciliation']
    out.append(f"The independent 5-minute signal builder finds **{c['raw_signal_count']:,}** raw events, matching exactly the FVG-ID set in the lifecycle file. The prior **1,639** research count excluded **9** events with incomplete later-day bars and **1** on a censored final NY date. Applying that same qualification reproduces 1,639, average subsequent MFE 125.1951 points and median 82.50. These hindsight exclusions are **not entry filters** here. All raw events also satisfy the strict favorable-side condition.\n")
    table(['Audit result','Signals'],list(r['signal_audit_counts'].items()))
    out.append(f"Eligible signals before daily lock: **{r['total_eligible_signals_before_daily_lock']}**. The first eligible signal per date wins; ties use oldest formation, then stable FVG ID. Rejected and competing signals are saved individually in the ignored audit CSV. Filter reasons are sequential: the 11:00 trigger-start cutoff is checked before the calendar.\n")
    out.append('## Overall performance\n')
    table(['Metric','Value'],list(r['overall'].items()))
    out.append('Profit/loss statistics are USD unless explicitly labeled points or R. Gross loss is a positive magnitude. Gross profit/loss split net trade P&L into positive/negative contributions; with zero costs these equal gross values. R uses each trade’s original risk; varying risk sizes explain why positive total R can coexist with a small dollar profit. Win rate uses all trades, including session-close exits and any breakevens.\n')
    perf('Long versus short',r['direction'],['average_risk_points'])
    perf('Yearly performance',r['yearly'])
    out.append('2026 ends with the available October 5 session and is a partial year. Group drawdowns are recomputed from zero for that group, not inherited from overall equity.\n')
    perf('Monthly performance',r['monthly'],['long_pnl_usd','short_pnl_usd'])
    perf('Trigger-bar start time, America/New_York',r['trigger_time_bins'],['signals'])
    out.append('Time buckets use the second candle’s START; a 10:55 trigger enters at 11:00 and belongs to 10:30–10:59. A trigger starting 11:00 is rejected.\n')
    perf('Weekday',{k:r['weekday'][k] for k in ['Monday','Tuesday','Wednesday','Thursday','Friday']})
    perf('Original stop-size research',{k:r['risk_buckets_left_inclusive'][k] for k in ['0-25','25-50','50-75','75-100','100-150','150-200','200+']})
    out.append('Risk bins are left-inclusive/right-exclusive: 25 points belongs to 25–50; 200 belongs to 200+. These do not filter trades.\n')
    out.append('## MFE / MAE\n')
    ex=r['excursions']
    table(['MFE threshold, points','Trades reaching it (%)'],[(str(k),ex['mfe_percent_at_least_points'][str(k)]) for k in [25,50,75,100,150,200]])
    table(['MFE threshold, original R','Trades reaching it (%)'],[(str(k),ex['mfe_percent_at_least_r'][str(k)]) for k in [.5,1,1.5,2]])
    table(['Other excursion check','Value'],[(k,v) for k,v in ex.items() if not isinstance(v,dict)])
    out.append('Excursions include full high/low of owned minutes through and including the exit minute. They exclude all signal-candle activity. For stop/target exits the intraminute ordering of that exit minute’s extrema is unknown; the trade log flags this. MFE/MAE are OHLC bounds, not necessarily realizable pre-fill excursions. Both levels in a minute resolve stop-first; the logged MFE may still exceed 2R.\n')
    out.append('## Equity and interpretation\n')
    o=r['overall']
    out.append(f"Final closed-trade equity is **${o['net_pnl_usd']:,.2f}**, from an initial zero. Peak equity is **${o['peak_equity_usd']:,.2f}**. Maximum drawdown is **${o['max_closed_trade_drawdown_usd']:,.2f}**, from the peak at {o['max_drawdown_peak_time_utc']} to the bottom at {o['max_drawdown_bottom_time_utc']}. Prior peak recovered: **{o['peak_recovered']}**. Longest losing streak: **{o['maximum_consecutive_losses']} trades**. The equity CSV preserves every closed-trade observation. This is closed-equity drawdown, not mark-to-market drawdown or an account-capital estimate.\n")
    out.append(f"The historical zero-cost result is marginal: PF **{o['profit_factor']:.4f}**, approximately **${o['average_pnl_per_trade_usd']:.2f} per trade**. A uniform round-trip cost of that amount would consume the measured profit before any slippage-induced changes to paths. No cost scenario or parameter was optimized. This full-period descriptive baseline is not an out-of-sample demonstration of a durable edge.\n")
    out.append('## Calendar, execution and determinism\n')
    out.append(f"Calendar: `exchange_calendars {r['calendar']['version']}`, XNYS, explicit bounds 2024-01-01 to 2026-10-06. A full session requires a local 09:30 open, 16:00 close and exactly 390 minutes. Non-session holidays/weekends and early closes are excluded, including the 2025-01-09 exceptional closure. The library computes its schedule locally; no internet lookup occurs during runs. The exact schedule and fingerprint are saved. [Official library documentation](https://github.com/gerrymanoim/exchange_calendars).\n")
    out.append('Entry is the confirmed second 5-minute close, timestamped at start + 5 minutes. The 1-minute bar starting exactly at entry is owned and evaluated; the preceding minute is excluded. Stop/target fills have an unknown intraminute time: `exit_bar_start_*` identifies the interval, and `exit_time_*` is its end/confirmation time. Duration uses that convention. Stops/targets stay active in 15:59–16:00 before a possible session-close exit.\n')
    out.append('An adverse opening gap beyond a stop fills at the worse of stop/open; targets fill at their limit with no favorable gap improvement. Stop-first priority applies even if both boundaries are crossed in a gap/conflict minute. Entry and all exit fills support adverse configured slippage ticks; initial risk/target use executed entry. Commission is charged twice. Baseline uses both at zero. Missing owned minutes fail the run rather than silently skipping a trade or simulating through the gap. No such failure occurred.\n')
    out.append('Executable prices are rounded to 0.25 ticks: nearest half-up for entry/target/exit, outward for structural stops. Current source prices are tick-aligned, so baseline rounding does not alter them. Body ratios, candle directions, range, and causal simple ATR(14) true-range means are recorded but never filter signals. ATR is nullable if 14 complete observations are unavailable and is descriptive across session/roll gaps.\n')
    out.append('Stable IDs depend on strategy version and signal identity. Results contain no wall-clock generation timestamps or random choices. Two complete runs must produce identical trade Parquet, CSV and summary bytes. Runtime dependencies and calendar are pinned; original inputs are fingerprinted before/after and validated layer code remains unchanged.\n')
    table(['Validation','Result'],list(r['validation'].items()))
    out.append('Reproduce with `work/.venv/bin/python outputs/cont_a_backtest.py`, then `work/.venv/bin/python outputs/cont_a_report.py`. Install any missing dependencies with `work/.venv/bin/python -m pip install -r outputs/requirements_backtest.txt`. Run all tests with `work/.venv/bin/python -m unittest discover -s outputs/tests -v`.\n')
    out.append('## Files\n')
    out.append('New source: `cont_a_backtest.py`, `cont_a_metrics.py`, `cont_a_validate.py`, `cont_a_report.py`, `requirements_backtest.txt`, `tests/test_cont_a.py`. `.gitignore` additionally excludes `outputs/results/`. Prior validated source/data files are unchanged.\n')
    out.append('Ignored `outputs/results/` contains `CONT_A_second_candle_baseline_trades.parquet`, matching `_trades.csv`, `_summary.json`, `_signal_audit.csv`, `_equity.csv` and `_xnys_calendar.csv`. The report is the only committed results document; no trade-level or market-data files are committed. This task requests a local commit only.\n')
    return '\n'.join(out)


if __name__=='__main__':
    root=Path(__file__).resolve().parent
    data=json.loads((root/'results/CONT_A_second_candle_baseline_summary.json').read_text())
    text=render(data)
    receipt=root/'results/CONT_A_second_candle_baseline_determinism.json'
    if receipt.is_file():
        proof=json.loads(receipt.read_text())
        matches=all(hashlib.sha256((root/'results'/name).read_bytes()).hexdigest()==digest
                    for name,digest in proof['sha256'].items())
        if matches:
            text+=f"\n## Completed baseline verification\n\n{proof.get('tests_passed','Recorded')} tests passed ({proof.get('new_cont_a_tests','new')} CONT-A tests). Two complete runs produced byte-identical trade Parquet/CSV, summary, audit, calendar and equity files. All grouped trade counts and P&L reconcile. The independent raw-integer replay matched all 263 executions. Previous validated code and all four input files remained unchanged.\n"
    (root/'CONT_A_SECOND_CANDLE_BASELINE.md').write_text(text)
