import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from decimal import Decimal, localcontext
import tempfile
import unittest
import pandas as pd
import pyarrow.parquet as pq
from pandas.testing import assert_frame_equal
import detect_fvgs as m


def fixture(direction='bullish', start='2024-02-05 14:30Z'):
    triples = ([[100,102,99,101], [101,106,100,105], [106,109,105,108]] if direction == 'bullish'
               else [[110,112,109,111], [109,110,104,105], [104,106,101,102]])
    ts = pd.date_range(start, periods=3, freq='5min').as_unit('ns')
    return pd.DataFrame({'timestamp_utc': ts, 'timestamp_ny': ts.tz_convert('America/New_York'),
                        'is_complete_5m': [True]*3, 'minute_count':[5]*3,
                        **{p:[Decimal(triples[i][j]) for i in range(3)] for j,p in enumerate(m.OHLC)}})


class DetectionTests(unittest.TestCase):
    def test_bullish_and_zone(self):
        f=m.detect(fixture());self.assertEqual(len(f),1)
        r=f.iloc[0];self.assertEqual(r.direction,'bullish')
        self.assertEqual((r.bottom,r.top,r.size_points),(Decimal(102),Decimal(105),Decimal(3)))
        m.validate(fixture(),f)

    def test_bearish_and_zone(self):
        f=m.detect(fixture('bearish'));self.assertEqual(len(f),1)
        r=f.iloc[0];self.assertEqual(r.direction,'bearish')
        self.assertEqual((r.bottom,r.top,r.size_points),(Decimal(106),Decimal(109),Decimal(3)))
        m.validate(fixture('bearish'),f)

    def test_overlap_no_gap(self):
        b=fixture();b.loc[2,'low']=Decimal(101)
        self.assertTrue(m.detect(b).empty)

    def test_equal_wicks_not_gap(self):
        for direction,field,value in [('bullish','low',102),('bearish','high',109)]:
            b=fixture(direction);b.loc[2,field]=Decimal(value)
            self.assertTrue(m.detect(b).empty)

    def test_each_incomplete_position_rejected(self):
        for pos in range(3):
            b=fixture();b.loc[pos,'is_complete_5m']=False;b.loc[pos,'minute_count']=4
            self.assertTrue(m.detect(b).empty)

    def test_missing_interval_rejected(self):
        for pos in [1,2]:
            b=fixture()
            b.loc[pos:,'timestamp_utc']+=m.FIVE
            b.timestamp_ny=b.timestamp_utc.dt.tz_convert('America/New_York')
            self.assertTrue(m.detect(b).empty)

    def test_opening_exception(self):
        for direction in ['bullish','bearish']:
            b=fixture(direction,'2024-02-05 14:25Z');f=m.detect(b)
            self.assertEqual(len(f),1);self.assertTrue(f.opening_exception.iloc[0])
            self.assertEqual(str(f.formation_date_ny.iloc[0]),'2024-02-05')
            self.assertEqual(f.formation_bar_start_ny.iloc[0].strftime('%H:%M'),'09:35')
            m.validate(b,f)

    def test_earlier_premarket_disallowed(self):
        for start in ['14:15','14:20']:
            self.assertTrue(m.detect(fixture(start=f'2024-02-05 {start}Z')).empty)

    def test_normal_rth(self):
        f=m.detect(fixture());self.assertEqual(len(f),1)
        self.assertFalse(f.opening_exception.iloc[0])

    def test_session_end_boundary(self):
        self.assertEqual(len(m.detect(fixture(start='2024-02-05 20:45Z'))),1)
        self.assertTrue(m.detect(fixture(start='2024-02-05 20:50Z')).empty)

    def test_summer_opening_and_dst(self):
        for date in ['2024-03-11','2024-07-09']:
            f=m.detect(fixture(start=f'{date} 13:25Z'))
            self.assertTrue(f.opening_exception.iloc[0])
            self.assertEqual(f.formation_bar_start_ny.iloc[0].utcoffset().total_seconds(),-14400)

    def test_candle2_no_direction_requirement(self):
        b=fixture();b.loc[1,m.OHLC]=[Decimal(105),Decimal(120),Decimal(90),Decimal(95)]
        self.assertEqual(len(m.detect(b)),1)

    def test_ids_stable_and_no_duplicates(self):
        b=pd.concat([fixture(),fixture('bearish','2024-02-06 14:30Z')],ignore_index=True)
        a=m.detect(b);z=m.detect(b.sample(frac=1,random_state=3))
        assert_frame_equal(a,z)
        self.assertFalse(a.fvg_id.duplicated().any())
        self.assertEqual(a.fvg_id.iloc[0],m.detect(fixture()).fvg_id.iloc[0])
        self.assertTrue(a.fvg_id.str.fullmatch('[0-9a-f]{64}').all())

    def test_duplicate_source_rejected(self):
        b=fixture()
        with self.assertRaisesRegex(ValueError,'Duplicate'):m.detect(pd.concat([b,b.iloc[:1]]))

    def test_source_unchanged(self):
        b=fixture();original=b.copy(deep=True);m.detect(b);assert_frame_equal(b,original)

    def test_empty_and_fewer_than_three_bars(self):
        for n in range(3):
            b=fixture().iloc[:n];f=m.detect(b)
            self.assertTrue(f.empty);self.assertEqual(list(f.columns),m.COLUMNS)
            m.validate(b,f)
            self.assertIsNone(m.statistics(b,f)['average_bullish_size'])

    def test_decimal_precision_context_independent(self):
        b=fixture()
        b.loc[0,'high']=Decimal('102.000000001')
        b.loc[2,'low']=Decimal('102.000000002')
        with localcontext() as ctx:
            ctx.prec=6
            self.assertEqual(m.detect(b).size_points.iloc[0],Decimal('0.000000001'))

    def test_parquet_roundtrip_and_deterministic_bytes(self):
        for b in [fixture(),fixture().iloc[:0]]:
            f=m.detect(b)
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'one.parquet';q=Path(d)/'two.parquet'
                m.write_output(f,p,'hash');m.write_output(f,q,'hash')
                self.assertEqual(p.read_bytes(),q.read_bytes())
                assert_frame_equal(f,pq.read_table(p).to_pandas())

    def test_validation_catches_missing_and_bad_records(self):
        b=fixture();f=m.detect(b)
        with self.assertRaisesRegex(ValueError,'counts'):m.validate(b,f.iloc[:0])
        f.loc[0,'bottom']=Decimal(0)
        with self.assertRaisesRegex(ValueError,'record'):m.validate(b,f)

    def test_inconsistent_completeness_rejected(self):
        b=fixture();b.loc[0,'minute_count']=4
        with self.assertRaisesRegex(ValueError,'contradicts'):m.detect(b)

    def test_invalid_timestamp_or_prices_rejected(self):
        b=fixture();b.timestamp_utc=b.timestamp_utc.dt.tz_localize(None)
        with self.assertRaisesRegex(ValueError,'timezone-aware'):m.detect(b)
        b=fixture();b.loc[0,'low']=Decimal('NaN')
        with self.assertRaisesRegex(ValueError,'finite'):m.detect(b)

    def test_randomized_stream_matches_independent_oracle(self):
        import random
        rng=random.Random(42)
        frames=[]
        for start in ['2024-02-05 14:20Z','2024-03-11 13:20Z']:
            ts=pd.date_range(start,periods=100,freq='5min').as_unit('ns')
            rows=[]
            for t in ts:
                low=rng.randint(90,120);high=low+rng.randint(1,8)
                complete=rng.random()>0.08
                rows.append({'timestamp_utc':t,'timestamp_ny':t.tz_convert('America/New_York'),
                             'open':Decimal(rng.randint(low,high)), 'high':Decimal(high),
                             'low':Decimal(low), 'close':Decimal(rng.randint(low,high)),
                             'is_complete_5m':complete,'minute_count':5 if complete else 4})
            frames.append(pd.DataFrame(rows).drop(index=[20,21,55]))
        bars=pd.concat(frames,ignore_index=True)
        fvgs=m.detect(bars)
        self.assertGreater(len(fvgs),0)
        self.assertTrue(m.validate(bars,fvgs)['independent_oracle_matches_all_records'])

    def test_statistics(self):
        b=pd.concat([fixture(),fixture('bearish','2024-02-06 14:30Z')],ignore_index=True)
        stats=m.statistics(b,m.detect(b))
        self.assertEqual(stats['total_fvgs'],2)
        self.assertEqual(stats['fvg_count_by_month'],{'2024-02':2})
        self.assertEqual(stats['median_bullish_size'],'3.000000000')


if __name__=='__main__':unittest.main()
