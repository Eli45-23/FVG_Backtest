import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from decimal import Decimal as D
import tempfile
import unittest
import pandas as pd
import pyarrow.parquet as pq
import detect_fvgs as detector
import fvg_lifecycle as m
from test_detect_fvgs import fixture
from lifecycle_stats import summary

END=pd.Timestamp('2024-02-06T05:00Z')


def scenario(prices=(),direction='bullish',offsets=None,complete=None):
    base=fixture(direction)
    f=detector.detect(base)
    start=base.timestamp_utc.iloc[-1]
    rows=[]
    for i,p in enumerate(prices):
        t=start+(offsets[i] if offsets else i+1)*m.FIVE
        good=complete[i] if complete else True
        rows.append({'timestamp_utc':t,'timestamp_ny':t.tz_convert('America/New_York'),
                     **{c:D(str(x)) for c,x in zip(detector.OHLC,p)},
                     'is_complete_5m':good,'minute_count':5 if good else 4})
    bars=pd.concat([base,pd.DataFrame(rows)],ignore_index=True) if rows else base
    return bars,f


def one(prices=(),direction='bullish',**kwargs):
    b,f=scenario(prices,direction,**kwargs)
    return m.build(b,f,END)[0]


class LifecycleTests(unittest.TestCase):
    def test_candle3_cannot_touch_itself(self):
        r=one()
        self.assertFalse(r['touched']);self.assertIsNone(r['first_touch_time'])
        self.assertEqual(r['bars_untouched'],0)

    def test_begins_next_bar_and_touch(self):
        r=one([[108,109,104,106]])
        self.assertEqual(r['first_touch_time'],r['formation_bar_start_utc']+m.FIVE)
        self.assertEqual(r['bars_until_first_touch'],1)
        self.assertEqual(r['minutes_untouched'],0)

    def test_bullish_full_fill_equal_not_invalidation(self):
        r=one([[106,108,102,104]])
        self.assertTrue(r['fully_filled']);self.assertFalse(r['wick_invalidated']);self.assertFalse(r['close_invalidated'])

    def test_bearish_full_fill_equal_not_invalidation(self):
        r=one([[103,109,101,105]],'bearish')
        self.assertTrue(r['fully_filled']);self.assertFalse(r['wick_invalidated']);self.assertFalse(r['close_invalidated'])

    def test_bullish_close_and_wick_invalidation(self):
        r=one([[106,107,100,101]])
        self.assertTrue(r['close_invalidated']);self.assertTrue(r['wick_invalidated'])
        self.assertEqual(r['close_terminal_state'],'invalidated')

    def test_bearish_close_and_wick_invalidation(self):
        r=one([[104,111,102,110]],'bearish')
        self.assertTrue(r['close_invalidated']);self.assertTrue(r['wick_invalidated'])

    def test_wick_then_close_methods_independent(self):
        r=one([[106,108,101,104],[104,105,100,101]])
        self.assertLess(r['wick_invalidation_time'],r['close_invalidation_time'])
        self.assertEqual(r['first_touch_time'],r['wick_invalidation_time'])

    def test_wick_only_separate_expiration(self):
        r=one([[106,108,101,104]])
        self.assertTrue(r['wick_invalidated']);self.assertFalse(r['close_invalidated'])
        self.assertTrue(r['close_expired_same_day']);self.assertFalse(r['wick_expired_same_day'])
        self.assertFalse(r['expired_same_day'])

    def test_same_day_expiration(self):
        r=one([[108,111,106,110]])
        self.assertTrue(r['expired_same_day']);self.assertTrue(r['expired_untouched'])
        self.assertEqual(r['expiration_time_ny'],pd.Timestamp('2024-02-06T00:00',tz='America/New_York'))

    def test_touched_can_expire(self):
        r=one([[107,110,104,108]])
        self.assertTrue(r['expired_after_touch']);self.assertFalse(r['expired_untouched'])

    def test_next_day_ignored(self):
        b,f=scenario([[107,110,103,105]])
        b.loc[3,'timestamp_utc']=pd.Timestamp('2024-02-06T14:45Z')
        b.timestamp_ny=b.timestamp_utc.dt.tz_convert('America/New_York')
        r=m.build(b,f,pd.Timestamp('2024-02-07T05:00Z'))[0]
        self.assertFalse(r['touched']);self.assertIsNone(r['next_bar_start_utc'])

    def test_bullish_untouched_distance_excludes_touch_bar(self):
        r=one([[108,112,106,110],[110,115,108,114],[114,200,104,108]])
        self.assertEqual(r['highest_high_before_touch'],D(115))
        self.assertEqual(r['highest_close_before_touch'],D(114))
        self.assertEqual(r['maximum_points_away_before_touch'],D(10))
        self.assertEqual(r['bars_untouched'],2);self.assertEqual(r['minutes_untouched'],10)
        self.assertEqual(r['bars_until_first_touch'],3)

    def test_bearish_untouched_distance(self):
        r=one([[102,105,98,99],[99,102,95,96]],'bearish')
        self.assertEqual(r['lowest_low_before_touch'],D(95))
        self.assertEqual(r['lowest_close_before_touch'],D(96))
        self.assertEqual(r['maximum_points_away_before_touch'],D(11))

    def test_first_bar_fields_and_classification(self):
        r=one([[108,112,106,111]])
        self.assertEqual(r['next_bar_open'],D(108));self.assertTrue(r['next_is_bullish_candle'])
        self.assertTrue(r['next_remained_favorable_side']);self.assertFalse(r['next_touched_fvg'])
        self.assertTrue(r['next_closed_above_reference_high'])

    def test_second_bar_fields_mirrored(self):
        r=one([[102,105,98,99],[99,101,95,96]],'bearish')
        self.assertEqual(r['second_bar_close'],D(96))
        self.assertEqual(r['second_bar_direction'],'bearish')
        self.assertTrue(r['second_closed_below_reference_low'])
        self.assertTrue(r['second_candle_research_trigger'])

    def test_no_new_high_pause_and_pre_extreme(self):
        r=one([[108,115,106,113],[113,114,110,112],[112,118,111,117]])
        self.assertEqual(r['no_new_extreme_pause_time'],r['second_bar_start_utc'])
        self.assertEqual(r['no_new_extreme_pre_pause_extreme'],D(115))
        self.assertEqual(r['no_new_extreme_trigger_time'],r['formation_bar_start_utc']+3*m.FIVE)

    def test_no_new_low_pause_and_pre_extreme(self):
        r=one([[102,105,95,96],[96,101,96,100],[100,102,92,94]],'bearish')
        self.assertEqual(r['no_new_extreme_pre_pause_extreme'],D(95))
        self.assertIsNotNone(r['no_new_extreme_trigger_time'])

    def test_opposite_close_both_directions(self):
        for direction,prices in [('bullish',[[108,115,106,113],[113,117,110,112]]),('bearish',[[102,105,95,96],[96,101,93,100]])]:
            r=one(prices,direction)
            self.assertEqual(r['opposite_close_pause_time'],r['second_bar_start_utc'])

    def test_first_pause_can_reference_c3_without_counting_its_extreme_as_distance(self):
        r=one([[108,109,106,107]])
        self.assertEqual(r['no_new_extreme_pause_time'],r['next_bar_start_utc'])
        self.assertEqual(r['no_new_extreme_pre_pause_extreme'],D(109))
        self.assertEqual(r['highest_high_before_touch'],D(109))

    def test_pause_not_on_touch_bar_and_trigger_not_on_pause(self):
        r=one([[108,115,106,113],[113,114,104,112]])
        self.assertIsNone(r['no_new_extreme_pause_time'])
        r=one([[108,109,106,107]])
        self.assertIsNone(r['no_new_extreme_trigger_time'])

    def test_mfe_excludes_trigger_high_and_continues_after_touch(self):
        r=one([[108,112,106,110],[110,200,108,114],[114,120,104,108],[108,125,100,102]])
        self.assertTrue(r['second_candle_research_trigger'])
        self.assertEqual(r['second_candle_mfe_points'],D(11))

    def test_pause_trigger_mfe_excludes_trigger_bar(self):
        r=one([[108,115,106,113],[113,114,110,112],[112,200,111,117],[117,120,104,110]])
        self.assertEqual(r['no_new_extreme_mfe_points'],D(3))

    def test_incomplete_slots_and_no_gap_pause_comparison(self):
        r=one([[108,200,90,108],[108,112,106,110]],complete=[False,True])
        self.assertFalse(r['touched']);self.assertIsNone(r['next_bar_start_utc'])
        self.assertIsNotNone(r['second_bar_start_utc']);self.assertIsNone(r['second_closed_above_reference_high'])
        self.assertFalse(r['research_day_eligible']);self.assertFalse(r['first_two_bars_untouched'])
        self.assertIsNone(r['no_new_extreme_pause_time'])

    def test_missing_exact_post_slots_not_shifted(self):
        r=one([[108,110,106,109]],offsets=[3])
        self.assertIsNone(r['next_bar_start_utc']);self.assertIsNone(r['second_bar_start_utc'])

    def test_partial_date_censored(self):
        b,f=scenario([[108,112,106,110]])
        r=m.build(b,f,b.timestamp_utc.iloc[-1]+m.FIVE)[0]
        self.assertTrue(r['observation_censored']);self.assertFalse(r['expired_same_day'])
        self.assertFalse(r['research_day_eligible'])
        self.assertEqual(summary([r])['untouched_continuation']['all']['count'],0)

    def test_jump_through_fill_without_touch(self):
        r=one([[100,101,98,99],[103,104,102,103]])
        self.assertTrue(r['gap_through_without_overlap'])
        self.assertLess(r['first_full_fill_time'],r['first_touch_time'])
        self.assertLess(r['close_invalidation_time'],r['first_touch_time'])

    def test_no_future_bar_mfe_is_null(self):
        r=one([[108,112,106,110],[110,118,108,114]])
        self.assertTrue(r['second_candle_research_trigger']);self.assertIsNone(r['second_candle_mfe_points'])

    def test_deterministic_records_roundtrip_and_one_per_fvg(self):
        b,f=scenario([[108,112,106,110],[110,118,108,114],[114,120,108,119]])
        records=m.build(b,f,END)
        self.assertEqual(records,m.build(b.sample(frac=1,random_state=8),f,END))
        self.assertEqual(len(records),len(f));self.assertEqual(len({r['fvg_id'] for r in records}),len(f))
        self.assertTrue(all(m.validate_records(b,f,records).values()))
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.parquet';c=Path(d)/'b.parquet'
            m.write_output(records,a,{});m.write_output(records,c,{})
            self.assertEqual(a.read_bytes(),c.read_bytes())
            self.assertEqual(pq.read_table(a).num_rows,1)

    def test_validator_rejects_corrupted_pause_threshold(self):
        b,f=scenario([[108,115,106,113],[113,114,110,112],[112,118,111,117]])
        records=m.build(b,f,END)
        records[0]['no_new_extreme_pre_pause_extreme']=D(999)
        with self.assertRaisesRegex(ValueError,'Pre-pause'):m.validate_records(b,f,records)

    def test_validator_rejects_candle3_as_touch(self):
        b,f=scenario([[108,112,106,110]])
        records=m.build(b,f,END)
        records[0]['first_touch_time']=records[0]['formation_bar_start_utc']
        with self.assertRaisesRegex(ValueError,'First event'):m.validate_records(b,f,records)

    def test_bearish_mfe_excludes_trigger_low(self):
        r=one([[102,105,98,99],[99,101,50,96],[96,100,90,93]],'bearish')
        self.assertTrue(r['second_candle_research_trigger'])
        self.assertEqual(r['second_candle_mfe_points'],D(6))

    def test_expiration_dst_calendar_boundary(self):
        b=fixture('bullish','2024-03-10T13:30Z');f=detector.detect(b)
        r=m.build(b,f,pd.Timestamp('2024-03-11T04:00Z'))[0]
        self.assertEqual(r['expiration_time_ny'],pd.Timestamp('2024-03-11T00:00',tz='America/New_York'))
        self.assertTrue(r['expired_same_day'])

    def test_summary_denominators_and_missing_mfe(self):
        r=one([[108,112,106,110],[110,118,108,114]])
        stats=summary([r])
        self.assertEqual(stats['second_candle']['all']['trigger_count'],1)
        self.assertEqual(stats['second_candle']['all']['mfe']['observations'],0)
        r['research_day_eligible']=False;r['incomplete_bars_skipped']=1
        stats=summary([r])
        self.assertEqual(stats['untouched_continuation']['all']['count'],0)
        self.assertEqual(stats['lifecycle']['all']['records'],1)

    def test_duplicate_input_fvg_rejected(self):
        b,f=scenario()
        with self.assertRaisesRegex(ValueError,'Duplicate'):m.build(b,pd.concat([f,f]),END)

    def test_bearish_wick_only(self):
        r=one([[104,110,102,108]],'bearish')
        self.assertTrue(r['wick_invalidated']);self.assertFalse(r['close_invalidated'])

    def test_bar_count_is_clock_distance_and_elapsed_separate(self):
        r=one([[108,112,106,110],[108,110,104,106]],offsets=[1,5])
        self.assertEqual(r['bars_until_first_touch'],5)
        self.assertEqual(r['bars_untouched'],1);self.assertEqual(r['minutes_untouched'],5)
        self.assertEqual(r['elapsed_minutes_until_touch_or_horizon'],20)

    def test_method_expiration_keeps_event_history(self):
        r=one([[106,108,102,104]])
        self.assertTrue(r['fully_filled']);self.assertTrue(r['touched'])
        self.assertEqual(r['close_terminal_state'],'expired_same_day')


if __name__=='__main__':unittest.main()
