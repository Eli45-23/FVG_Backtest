"""Descriptive lifecycle summaries. These are not trade returns or P&L."""
from decimal import Decimal, ROUND_HALF_EVEN, localcontext

THRESHOLDS = [10, 25, 50, 75, 100, 150, 200]
MFE_THRESHOLDS = [25, 50, 100, 150, 200]


def numeric_summary(values, thresholds=()):
    v = sorted(Decimal(str(x)) for x in values if x is not None)
    with localcontext() as ctx:
        ctx.prec = 38
        ctx.rounding = ROUND_HALF_EVEN
        def rounded(x):
            return str(x.quantize(Decimal('0.000001')))
        n = len(v)
        return {'observations': n,
                'average': rounded(sum(v) / n) if n else None,
                'median': rounded(v[n//2] if n%2 else (v[n//2-1]+v[n//2])/2) if n else None,
                'percent_at_least': {str(t): round(100*sum(x >= t for x in v)/n, 6) if n else None for t in thresholds}}


def summary(records):
    def base(rows):
        # Censored dates and skipped incomplete observations are not "never touched" evidence.
        clean = [r for r in rows if r['research_day_eligible']]
        touched = [r for r in clean if r['touched']]
        never = [r for r in clean if not r['touched']]
        return {'records': len(rows), 'research_day_eligible': len(clean),
                'censored_records': sum(r['observation_censored'] for r in rows),
                'records_with_skipped_incomplete_bars': sum(r['incomplete_bars_skipped'] > 0 for r in rows),
                'touched_in_observed_window': sum(r['touched'] for r in rows),
                'untouched_in_observed_window': sum(not r['touched'] for r in rows),
                'touched_same_day': len(touched), 'never_touched_same_day': len(never),
                'fully_filled_same_day':sum(r['fully_filled'] for r in clean),
                'close_invalidated_same_day':sum(r['close_invalidated'] for r in clean),
                'wick_invalidated_same_day':sum(r['wick_invalidated'] for r in clean),
                'expired_untouched_qualified':sum(r['expired_untouched'] for r in clean),
                'expired_after_touch_qualified':sum(r['expired_after_touch'] for r in clean),
                'fully_filled_observed': sum(r['fully_filled'] for r in rows),
                'close_invalidated_observed': sum(r['close_invalidated'] for r in rows),
                'wick_invalidated_observed': sum(r['wick_invalidated'] for r in rows),
                'expired_untouched': sum(r['expired_untouched'] for r in rows),
                'expired_after_touch': sum(r['expired_after_touch'] for r in rows),
                'close_method_expired': sum(r['close_expired_same_day'] for r in rows),
                'wick_method_expired': sum(r['wick_expired_same_day'] for r in rows),
                'percent_touched_same_day': round(100*len(touched)/len(clean),6) if clean else None,
                'percent_never_touched_same_day': round(100*len(never)/len(clean),6) if clean else None,
                'bars_until_first_touch': numeric_summary([r['bars_until_first_touch'] for r in touched]),
                'maximum_distance_before_touch_or_expiry': numeric_summary([r['maximum_points_away_before_touch'] for r in clean]),
                'maximum_distance_before_touch_touched_only': numeric_summary([r['maximum_points_away_before_touch'] for r in touched])}

    def untouched(rows):
        v = [r for r in rows if r['research_day_eligible'] and not r['touched']]
        return {'count': len(v), 'bullish':sum(r['direction']=='bullish' for r in v),
                'bearish':sum(r['direction']=='bearish' for r in v),
                'maximum_points_away':numeric_summary([r['maximum_points_away_before_touch'] for r in v], THRESHOLDS)}

    def second(rows):
        eligible = [r for r in rows if r['research_day_eligible'] and r['first_two_bars_untouched']]
        events = [r for r in eligible if r['second_candle_research_trigger']]
        return {'first_two_untouched_denominator':len(eligible), 'trigger_count':len(events),
                'trigger_percent':round(100*len(events)/len(eligible),6) if eligible else None,
                'mfe':numeric_summary([r['second_candle_mfe_points'] for r in events],MFE_THRESHOLDS),
                'no_future_complete_bar':sum(r['second_candle_mfe_points'] is None for r in events)}

    def pause(rows, kind):
        eligible=[r for r in rows if r['research_day_eligible'] and r[f'{kind}_pause_time'] is not None]
        events=[r for r in eligible if r[f'{kind}_trigger_time'] is not None]
        return {'pause_count_while_untouched':len(eligible), 'trigger_count':len(events),
                'trigger_percent_of_pauses':round(100*len(events)/len(eligible),6) if eligible else None,
                'mfe':numeric_summary([r[f'{kind}_mfe_points'] for r in events],MFE_THRESHOLDS),
                'no_future_complete_bar':sum(r[f'{kind}_mfe_points'] is None for r in events)}

    def split(function):
        return {k:function(records if k=='all' else [r for r in records if r['direction']==k]) for k in ['all','bullish','bearish']}

    bins={
        '09:30-09:59':(570,600),'10:00-10:29':(600,630),
        '10:30-10:59':(630,660),'11:00-and-later':(660,1440)}
    return {'denominator_policy':'Full NY date within coverage and no incomplete post-formation bars; scheduled/nontrading gaps are not filled. Partial-date and incomplete-bar records are retained but excluded from research summaries.',
            'lifecycle':split(base), 'untouched_continuation':split(untouched),
            'untouched_by_formation_time':{label:{d:untouched([r for r in records if lo<=r['formation_bar_start_ny'].hour*60+r['formation_bar_start_ny'].minute<hi and (d=='all' or r['direction']==d)]) for d in ['all','bullish','bearish']} for label,(lo,hi) in bins.items()},
            'second_candle':split(second),
            'pullback_no_new_extreme':split(lambda rows:pause(rows,'no_new_extreme')),
            'pullback_opposite_close':split(lambda rows:pause(rows,'opposite_close'))}
