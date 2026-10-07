"""Public Strategy Research Lab SDK v1. No internal imports required."""
from dataclasses import dataclass,field
from decimal import Decimal
from typing import Literal
import re

@dataclass(frozen=True)
class Input:
    id:str
    label:str
    type:str
    default:object
    min:float|None=None
    max:float|None=None
    step:float|None=None
    choices:tuple=()
    description:str=''
    def validate(self,value):
        if self.type=='bool':
            if not isinstance(value,bool):raise ValueError(f'{self.id}: expected boolean')
        elif self.type in ('float','int'):
            if isinstance(value,bool):raise ValueError(f'{self.id}: expected number')
            try:n=Decimal(str(value))
            except Exception:raise ValueError(f'{self.id}: expected number') from None
            if not n.is_finite() or (self.type=='int' and n!=int(n)):raise ValueError(f'{self.id}: invalid number')
            if self.min is not None and n<Decimal(str(self.min)):raise ValueError(f'{self.id}: below minimum')
            if self.max is not None and n>Decimal(str(self.max)):raise ValueError(f'{self.id}: above maximum')
            if self.step is not None and (n-Decimal(str(self.min or 0)))%Decimal(str(self.step))!=0:raise ValueError(f'{self.id}: off step')
            value=int(n) if self.type=='int' else float(n)
        else:
            if not isinstance(value,str):raise ValueError(f'{self.id}: expected text')
            if self.type=='choice' and value not in self.choices:raise ValueError(f'{self.id}: invalid choice')
            if self.type=='time' and not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d',value):raise ValueError(f'{self.id}: expected HH:MM')
            if self.type=='session':
                bits=value.split('-')
                if len(bits)!=2 or any(not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d',s) for s in bits):raise ValueError(f'{self.id}: expected HH:MM-HH:MM')
        return value

def Float(id,label,default,**kw):return Input(id,label,'float',default,**kw)
def Int(id,label,default,**kw):return Input(id,label,'int',default,**kw)
def Bool(id,label,default=False,**kw):return Input(id,label,'bool',default,**kw)
def String(id,label,default='',**kw):return Input(id,label,'string',default,**kw)
def Choice(id,label,default,choices,**kw):return Input(id,label,'choice',default,choices=tuple(choices),**kw)
def Time(id,label,default,**kw):return Input(id,label,'time',default,**kw)
def Session(id,label,default,**kw):return Input(id,label,'session',default,**kw)

@dataclass(frozen=True)
class Bar:
    timestamp:object
    open:Decimal
    high:Decimal
    low:Decimal
    close:Decimal
    volume:int=0
    @property
    def time(self):return self.timestamp.tz_convert('America/New_York').strftime('%H:%M')

@dataclass(frozen=True)
class FVG:
    id:str
    direction:str
    top:Decimal
    bottom:Decimal
    formation:object
    opening_exception:bool

@dataclass(frozen=True)
class Context:
    timestamp:object # current confirmed bar CLOSE, UTC
    bar:Bar
    previous_bar:Bar|None
    history:tuple[Bar,...]
    fvg:FVG|None=None
    bar1:Bar|None=None
    bar2:Bar|None=None
    instrument:str='MNQ'
    tick_size:Decimal=Decimal('.25')
    position:None=None # v1 is flat-only entry callbacks, one actual trade/day

@dataclass(frozen=True)
class Entry:
    direction:Literal['LONG','SHORT']
    stop:Decimal
    target_r:Decimal=Decimal('2')
    max_risk:Decimal|None=None
    metadata:dict=field(default_factory=dict)

@dataclass(frozen=True)
class StopUpdate:
    """Reserved request contract. V1 rejects management hooks; no retroactive fills."""
    price:Decimal
    effective_after:object
