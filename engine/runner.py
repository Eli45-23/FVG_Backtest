"""Generic flat-entry strategy adapter over the unchanged minute fill engine."""
from decimal import Decimal as D,localcontext,ROUND_FLOOR,ROUND_CEILING
from dataclasses import dataclass
from datetime import date
import hashlib,statistics
import pandas as pd
from engine.legacy import reference as ref,metrics
from engine.strategy import Entry
from engine.strategy.loading import load
from engine.data import dataset,contexts,execution_days
from engine.canonical import digest,clean

@dataclass(frozen=True)
class RunConfig:
    start:str='2024-01-01'
    end:str='2026-10-06' # NY calendar date exclusive
    quantity:int=1
    commission:str='0'
    slippage:int=0
    instrument:str='MNQ'
    timeframe:str='5m'
    def validate(self):
        a,b=date.fromisoformat(self.start),date.fromisoformat(self.end)
        if not date(2024,1,1)<=a<b<=date(2026,10,6):raise ValueError('Date range must lie within 2024-01-01 to 2026-10-06 (end exclusive)')
        if not isinstance(self.quantity,int) or not 1<=self.quantity<=100:raise ValueError('Quantity must be 1–100')
        if self.instrument!='MNQ' or self.timeframe!='5m':raise ValueError('Engine v1 supports MNQ / 5m only')
        ref.Config(D(self.commission),self.slippage)


def signal(ctx,direction):
    f=ctx.fvg;at=ctx.timestamp;ny=at.tz_convert('America/New_York')
    sid=f.id if f else hashlib.sha256(('bars|'+str(ctx.bar.timestamp.value)+'|'+direction).encode()).hexdigest()
    formed=f.formation if f else ctx.bar.timestamp
    r={'signal_id':sid+'@'+str(at.value),'fvg_id':sid,'direction':direction,'formation_date':ny.date(),
       'formation_time_utc':formed,'formation_time_ny':formed.tz_convert('America/New_York'),
       'opening_exception':f.opening_exception if f else False,'fvg_top':f.top if f else D(0),
       'fvg_bottom':f.bottom if f else D(0),'fvg_size_points':f.top-f.bottom if f else D(0),
       'entry_time_utc':at,'entry_time_ny':ny,'signal_close_price':ctx.bar.close,'atr14_simple_points':None}
    for name,c in [('first',ctx.bar1),('second',ctx.bar2)]:
        r[f'{name}_bar_time_utc']=c.timestamp;r[f'{name}_bar_time_ny']=c.timestamp.tz_convert('America/New_York')
        for k in ['open','high','low','close']:r[f'{name}_bar_{k}']=getattr(c,k)
        r[f'{name}_bar_body_ratio']=float(abs(c.close-c.open)/(c.high-c.low)) if c.high!=c.low else None
        r[f'{name}_bar_direction']='bullish' if c.close>c.open else 'bearish' if c.close<c.open else 'doji'
        r[f'{name}_bar_range']=c.high-c.low
    return r


def run(source,params,config=RunConfig(),data=None,progress=lambda stage:None):
    config.validate();strategy,p,_=load(source,params);data=data if data is not None else dataset()
    days,_=ref.full_sessions();chosen=[];eligible=[];locked=set();audit=[];metadata={}
    cfg=ref.Config(D(config.commission),config.slippage)
    progress('Evaluating confirmed-bar strategy callbacks')
    with localcontext() as dec:
        dec.prec=38
        for ctx in contexts(data,getattr(strategy,'feature','bars')):
            ny=ctx.timestamp.tz_convert('America/New_York');day=ny.date().isoformat()
            # v1 exchange/session and no-overnight contract; strategy supplies its own cutoff.
            if not config.start<=day<config.end or day not in days or not '09:30'<=ctx.bar.time<'16:00' or ny.strftime('%H:%M')>='16:00':continue
            order=strategy.on_bar(ctx,p)
            if order is None:continue
            if not isinstance(order,Entry) or order.direction not in ('LONG','SHORT'):raise ValueError('on_bar must return Entry(LONG/SHORT) or None')
            sign=D(1) if order.direction=='LONG' else D(-1)
            price=ref.tick(ctx.bar.close)+sign*ref.TICK*config.slippage
            stop=D(str(order.stop));rr=D(str(order.target_r))
            if not stop.is_finite() or not rr.is_finite() or rr<=0:raise ValueError('Stop and target R must be finite; target R positive')
            stop=ref.tick(stop,ROUND_FLOOR if sign==1 else ROUND_CEILING);risk=(price-stop)*sign
            if order.max_risk is not None and (not D(str(order.max_risk)).is_finite() or D(str(order.max_risk))<=0):raise ValueError('Maximum risk must be finite and positive')
            s=signal(ctx,order.direction)
            reason='NON_POSITIVE_RISK' if risk<=0 else 'MAX_RISK_FILTER' if order.max_risk is not None and risk>=D(str(order.max_risk)) else 'ELIGIBLE'
            if reason=='ELIGIBLE':
                eligible.append(s)
                if day in locked:reason='DAILY_LOCK_COMPETING_SIGNAL'
                else:
                    locked.add(day);reason='SELECTED';metadata[s['signal_id']]=clean(order.metadata)
                    chosen.append({**s,'entry_price':price,'stop_price':stop,'target_price':ref.tick(price+sign*rr*risk),'risk_points':risk,'risk_usd':risk*ref.VALUE})
            audit.append({'signal_id':s['signal_id'],'reason':reason})
        progress('Executing selected entries with validated 1-minute fills')
        groups=execution_days(data['minutes']) if chosen else {}
        trades=[ref.execute(s,groups[s['formation_date']],cfg) for s in chosen]
        if config.quantity!=1:
            for t in trades:
                t['quantity']=config.quantity
                for k in ['risk_usd','pnl_usd','gross_pnl_usd','net_pnl_usd','commission_usd']:t[k]*=config.quantity
        # Preserve the reference decimal128(24,9) artifact contract.
        if trades:trades=ref.frame_table(trades).to_pylist()
        for t in trades:t['metadata']=metadata.get(t['signal_id'],{})
        progress('Calculating metrics')
        summary=metrics.summary(trades,eligible)
        # Generic strategies can enter outside CONT-A's three morning bins.
        for minute in range(660,960,30):
            label=f'{minute//60:02}:{minute%60:02}-{(minute+29)//60:02}:{(minute+29)%60:02}'
            clock=lambda t:t['second_bar_time_ny'].hour*60+t['second_bar_time_ny'].minute
            summary['trigger_time_bins'][label]={**metrics.performance([t for t in trades if minute<=clock(t)<minute+30]),'signals':sum(minute<=clock(s)<minute+30 for s in eligible)}
        pnl=[float(t['net_pnl_usd']) for t in trades];equity=0;trough=0;runup=0
        for x in pnl:equity+=x;trough=min(trough,equity);runup=max(runup,equity-trough)
        summary['overall'].update(median_trade_usd=statistics.median(pnl) if pnl else None,max_runup_usd=runup if pnl else None)
        for f in ['mfe_r','mae_r']:summary['excursions']['average_'+f]=statistics.mean(t[f] for t in trades) if trades else None
        _,curve=metrics.drawdown(trades)
        return {'trades':trades,'summary':summary,'equity':curve,'audit':audit}
