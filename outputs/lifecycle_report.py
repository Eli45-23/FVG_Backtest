"""Render the saved lifecycle validation JSON as readable research tables."""
import json
from pathlib import Path


def render(report):
    out=['# MNQ same-day FVG lifecycle research\n',
         'Descriptive observations only. No entries, fills of orders, positions, exits, stops, targets or P&L are simulated.\n',
         'Primary research denominator: full NY date covered, with no incomplete post-formation bars skipped. All records remain in Parquet; censoring and quality exclusions affect summaries only. Missing empty clock buckets are not synthesized and may include scheduled closures.\n']
    def table(headers, rows):
        out.append('| '+' | '.join(headers)+' |')
        out.append('| '+' | '.join('---' for _ in headers)+' |')
        for row in rows:out.append('| '+' | '.join(str(x) if x is not None else 'N/A' for x in row)+' |')
        out.append('')
    def fmt(v):
        return f'{float(v):,.2f}' if v is not None else None
    out.append('## Lifecycle counts and denominators\n')
    groups=report['lifecycle']
    keys=['records','research_day_eligible','censored_records','records_with_skipped_incomplete_bars',
          'touched_in_observed_window','untouched_in_observed_window','touched_same_day','never_touched_same_day',
          'fully_filled_observed','close_invalidated_observed','wick_invalidated_observed',
          'fully_filled_same_day','close_invalidated_same_day','wick_invalidated_same_day',
          'expired_untouched','expired_after_touch','expired_untouched_qualified','expired_after_touch_qualified',
          'close_method_expired','wick_method_expired','percent_touched_same_day','percent_never_touched_same_day']
    table(['Metric','All','Bullish','Bearish'],[[k,*[groups[d][k] for d in ['all','bullish','bearish']]] for k in keys])
    out.append('“Observed” totals include established events on partial or quality-flagged histories. The same-day counts and percentages use the qualified denominator. Shared expiration means neither method invalidated; per-method expiration totals are retained separately.\n')
    for title,key in [('Bars until first touch (touched qualified records only)','bars_until_first_touch'),
                      ('Maximum points away before touch or expiry (all qualified records)','maximum_distance_before_touch_or_expiry'),
                      ('Maximum points away before first touch (touched qualified records only)','maximum_distance_before_touch_touched_only')]:
        out.append(f'### {title}\n')
        table(['Direction','N','Average','Median'],[[d,groups[d][key]['observations'],fmt(groups[d][key]['average']),fmt(groups[d][key]['median'])] for d in groups])
    out.append('## Never-touched continuation\n')
    out.append('This is a hindsight cohort: membership requires observing the entire date. It is not a real-time selection rule. No invalidation method is used as a research filter. A gap-through can invalidate without satisfying the overlap definition of touch.\n')
    table(['Cohort','Total','Bullish','Bearish','Avg away','Median away','>=10 %','>=25 %','>=50 %','>=75 %','>=100 %','>=150 %','>=200 %'],
          [[d,v['count'],v['bullish'],v['bearish'],fmt(v['maximum_points_away']['average']),fmt(v['maximum_points_away']['median']),
            *[v['maximum_points_away']['percent_at_least'][str(t)] for t in [10,25,50,75,100,150,200]]] for d,v in report['untouched_continuation'].items()])
    out.append('### By Candle 3 start time, America/New_York\n')
    table(['Time','Direction','N','Avg away','Median away','>=10 %','>=25 %','>=50 %','>=75 %','>=100 %','>=150 %','>=200 %'],
          [[label,d,v['count'],fmt(v['maximum_points_away']['average']),fmt(v['maximum_points_away']['median']),
            *[v['maximum_points_away']['percent_at_least'][str(t)] for t in [10,25,50,75,100,150,200]]]
           for label,g in report['untouched_by_formation_time'].items() for d,v in g.items()])
    out.append('## Second-candle continuation research\n')
    out.append('Denominator: both exact +5/+10-minute post-formation bars exist, are complete and have no zone overlap. Numerator: second close strictly exceeds the first high (bullish) or is below its low (bearish). MFE starts strictly after that second candle.\n')
    table(['Direction','First two untouched','Occurrences','Frequency %','MFE N','Avg MFE','Median MFE','>=25 %','>=50 %','>=100 %','>=150 %','>=200 %'],
          [[d,v['first_two_untouched_denominator'],v['trigger_count'],v['trigger_percent'],v['mfe']['observations'],fmt(v['mfe']['average']),fmt(v['mfe']['median']),
            *[v['mfe']['percent_at_least'][str(t)] for t in [25,50,100,150,200]]] for d,v in report['second_candle'].items()])
    out.append('## Pullback-continuation research\n')
    out.append('The first pause of each kind is recorded while still untouched. An occurrence requires a strictly later untouched candle to close beyond that pause’s running pre-pause extreme. Only one first occurrence per definition per FVG is counted; the definitions can overlap.\n')
    table(['Pause definition','Direction','Pauses','Occurrences','Frequency %','MFE N','Avg MFE','Median MFE','>=25 %','>=50 %','>=100 %','>=150 %','>=200 %'],
          [[label,d,v['pause_count_while_untouched'],v['trigger_count'],v['trigger_percent_of_pauses'],v['mfe']['observations'],fmt(v['mfe']['average']),fmt(v['mfe']['median']),
            *[v['mfe']['percent_at_least'][str(t)] for t in [25,50,100,150,200]]]
           for label,key in [('No new extreme','pullback_no_new_extreme'),('Opposite close','pullback_opposite_close')] for d,v in report[key].items()])
    out.append('MFE is the nonnegative favorable extreme from the research occurrence close through later complete candles on the same NY date. It includes later price observations even after zone touch/invalidation, and excludes the occurrence candle itself. No subsequent complete candle means null MFE, not zero; these records remain in occurrence counts but are excluded from MFE averages and threshold denominators. Multiple FVGs can share candles, so counts are not independent trades.\n')
    out.append('## Validation\n')
    table(['Check','Passed'],[[k,v] for k,v in report['validation'].items()])
    out.append(f"Input files unchanged: {report['inputs_unchanged']}.\n")
    out.append('See [LIFECYCLE_LAYER.md](LIFECYCLE_LAYER.md) for field semantics, censoring, tests and reproducible commands. Full-precision summaries are retained in ignored `outputs/data/MNQ_FVG_LIFECYCLE_validation.json`.\n')
    return '\n'.join(out)


if __name__=='__main__':
    root=Path(__file__).resolve().parent
    report=json.loads((root/'data/MNQ_FVG_LIFECYCLE_validation.json').read_text())
    (root/'LIFECYCLE_RESEARCH.md').write_text(render(report))
