import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from decimal import Decimal, localcontext
import tempfile
import unittest
import pandas as pd
import pyarrow.parquet as pq
from pandas.testing import assert_frame_equal
import build_5m as m


def fixture(start='2024-02-05 14:20:00Z', n=15):
    return pd.DataFrame({'ts_event': pd.date_range(start, periods=n, freq='min'),
        'open': [100*m.SCALE+i*m.SCALE for i in range(n)],
        'high': [102*m.SCALE+i*m.SCALE for i in range(n)],
        'low': [99*m.SCALE+i*m.SCALE for i in range(n)],
        'close': [101*m.SCALE+i*m.SCALE for i in range(n)],
        'volume': list(range(1,n+1)), 'instrument_id': [123]*n, 'rtype': [33]*n})


class BarTests(unittest.TestCase):
    def test_fixed_point_exact(self):
        with localcontext() as ctx:
            ctx.prec=6
            self.assertEqual(m.fixed_to_decimal(17018750000000), Decimal('17018.750000000'))
            self.assertEqual(m.fixed_to_decimal(1234567891), Decimal('1.234567891'))
            self.assertEqual(m.fixed_to_decimal(-250000000), Decimal('-0.250000000'))

    def test_ohlc_volume_aggregation(self):
        b=m.build_bars(fixture(n=5)).iloc[0]
        self.assertEqual([b.open,b.high,b.low,b.close],list(map(Decimal,['100','106','99','105'])))
        self.assertEqual(b.volume,15)
        self.assertEqual(b.minute_count,5)
        self.assertTrue(b.is_complete_5m)

    def test_standard_clock_not_rolling(self):
        b=m.build_bars(fixture('2024-02-05 14:22Z',n=8))
        self.assertEqual(list(b.ny_time),['09:20:00','09:25:00'])
        self.assertEqual(list(b.minute_count),[3,5])

    def test_ny_winter_summer(self):
        for start,offset in [('2024-02-05 14:30Z',-5),('2024-07-09 13:30Z',-4)]:
            b=m.build_bars(fixture(start,n=5)).iloc[0]
            self.assertEqual(b.ny_time,'09:30:00')
            self.assertEqual(b.timestamp_ny.utcoffset().total_seconds()/3600,offset)
            self.assertEqual(b.timestamp_utc,b.timestamp_ny)

    def test_special_alignment(self):
        for day,utc in [('2024-02-05','14:25'),('2024-07-09','13:25')]:
            b=m.build_bars(fixture(f'{day} {utc}Z',15))
            self.assertEqual(list(b.ny_time),['09:25:00','09:30:00','09:35:00'])
            self.assertEqual(list(b.is_rth),[False,True,True])
            self.assertEqual(list(b.is_premarket),[True,False,False])

    def test_incomplete_no_synthetic_minutes(self):
        raw=fixture(n=15).drop(index=[1,5,6,7,8,9])
        b=m.build_bars(raw)
        self.assertEqual(list(b.ny_time),['09:20:00','09:30:00'])
        self.assertEqual(list(b.minute_count),[4,5])
        self.assertEqual(list(b.is_complete_5m),[False,True])
        self.assertEqual(int(b.volume.sum()),int(raw.volume.sum()))

    def test_no_output_duplicates_and_determinism(self):
        raw=fixture(n=45)
        b=m.build_bars(raw)
        self.assertFalse(b.timestamp_utc.duplicated().any())
        assert_frame_equal(b,m.build_bars(raw.sample(frac=1,random_state=42)))
        m.validate_all(raw,b)

    def test_duplicate_minutes_rejected(self):
        raw=fixture(n=5)
        with self.assertRaisesRegex(ValueError,'duplicate'):
            m.build_bars(pd.concat([raw,raw.iloc[:1]]))

    def test_naive_or_off_grid_rejected(self):
        raw=fixture(n=5); raw.ts_event=raw.ts_event.dt.tz_localize(None)
        with self.assertRaisesRegex(ValueError,'timezone-aware'):m.build_bars(raw)
        raw=fixture(n=5); raw.ts_event+=pd.Timedelta(seconds=1)
        with self.assertRaisesRegex(ValueError,'minute boundaries'):m.build_bars(raw)

    def test_invalid_ohlc_rejected(self):
        for value in [m.UNDEF_PRICE,1]:
            raw=fixture(n=5); raw.loc[0,'high']=value
            with self.assertRaisesRegex(ValueError,'OHLC'):m.build_bars(raw)

    def test_session_boundaries(self):
        b=m.build_bars(fixture('2024-02-05 20:55Z',n=10))
        self.assertEqual(list(b.ny_time),['15:55:00','16:00:00'])
        self.assertEqual(list(b.is_rth),[True,False])
        self.assertEqual(list(b.is_postmarket),[False,True])

    def test_calendar_date_not_futures_trading_day(self):
        b=m.build_bars(fixture('2024-02-05 00:00Z',5)).iloc[0]
        self.assertEqual(str(b.ny_date),'2024-02-04')
        self.assertEqual(b.ny_time,'19:00:00')
        self.assertTrue(b.is_postmarket)

    def test_dst_fall_repeated_wall_clock_distinct_instants(self):
        b=m.build_bars(fixture('2024-11-03 05:00Z',n=120))
        self.assertFalse(b.timestamp_utc.duplicated().any())
        self.assertFalse(b.timestamp_ny.duplicated().any())
        self.assertEqual(int(b.ny_time.eq('01:00:00').sum()),2)
        self.assertNotEqual(b.timestamp_ny.iloc[0].utcoffset(),b.timestamp_ny.iloc[12].utcoffset())

    def test_dst_spring_no_fake_local_hour(self):
        b=m.build_bars(fixture('2024-03-10 06:55Z',n=10))
        self.assertEqual(list(b.ny_time),['01:55:00','03:00:00'])

    def test_contract_boundary_flagged(self):
        raw=fixture(n=5);raw.loc[4,'instrument_id']=456
        b=m.build_bars(raw).iloc[0]
        self.assertTrue(b.is_complete_5m)
        self.assertTrue(b.is_mixed_contract)
        self.assertEqual(b.instrument_count,2)

    def test_parquet_exact_decimal_and_timezones(self):
        b=m.build_bars(fixture(n=10))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bars.parquet';m.write_parquet(b,p,'test-hash')
            t=pq.read_table(p)
            self.assertEqual(str(t.schema.field('open').type),'decimal128(20, 9)')
            self.assertEqual(t.schema.field('timestamp_ny').type.tz,'America/New_York')
            self.assertEqual(t.schema.field('timestamp_utc').type.tz,'UTC')
            assert_frame_equal(b,t.to_pandas())

    def test_independent_reconciliation_detects_bad_aggregation(self):
        raw=fixture(n=10);b=m.build_bars(raw);b.loc[0,'volume']+=1
        with self.assertRaisesRegex(ValueError,'Volume'):m.validate_all(raw,b)

    def test_parquet_bytes_deterministic(self):
        b=m.build_bars(fixture(n=15))
        with tempfile.TemporaryDirectory() as d:
            p1=Path(d)/'one.parquet';p2=Path(d)/'two.parquet'
            m.write_parquet(b,p1,'same-source')
            m.write_parquet(b,p2,'same-source')
            self.assertEqual(p1.read_bytes(),p2.read_bytes())

    def test_source_not_mutated(self):
        raw=fixture(n=15);before=raw.copy(deep=True)
        m.build_bars(raw)
        assert_frame_equal(raw,before)


if __name__=='__main__':unittest.main()
