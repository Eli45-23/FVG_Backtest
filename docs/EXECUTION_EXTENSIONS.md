# Explicit execution extensions

Legacy runs default to `legacy_2024_2026`, `legacy_v1`, fixed quantity, 5m,
and one entry/day. The legacy fill path remains intact. New run snapshots contain
profile identity, source SHA-256 and row counts. Research profile execution reads
local 2020–2026 Parquet; no download or source rewrite occurs. End dates are exclusive.

`extended_v1` enables flat-only sequential positions. A signal at or after the
previous exit confirmation can enter; earlier signals receive POSITION_OPEN.
Daily limits count actual entries, with DAILY_TRADE_LIMIT auditing. `null` means
unlimited. Timeframe/daily-limit/sizing changes automatically select extended execution.
Full XNYS entry days remain required. Missing owned execution minutes fail explicitly.

SDK additions (old Entry unchanged):

```python
from engine.strategy import PositionPlan, TargetLeg
from decimal import Decimal
# Run quantity must be 2, execution mode extended_v1.
return PositionPlan('LONG', ctx.bar.low - ctx.tick_size,
    legs=(TargetLeg(1, Decimal('1'), 'TP1'),
          TargetLeg(1, None, 'runner')),
    break_even_after_tp1=True)
```

A leg with no target exits at the remaining stop or session close. Quantities must
sum exactly to sized entry quantity. Active original/current stop has priority over
ALL targets in the same minute. Otherwise targets fill in price-distance order.
TP1-triggered breakeven activates next minute, never retroactively. Multiple target
hits can fill before a newly requested stop becomes active. Existing MoveStop hooks
remain requests at minute/5m confirmation and may only tighten. No overlap/hedging.
MFE/MAE retain full exit-minute OHLC uncertainty. Each partial records quantity,
price, time, reason, gross/net P&L; trade exit is quantity-weighted. Commission is
charged each side per contract. All exits receive the configured adverse slippage, including target fills,
matching the existing execution convention. See the implementation tests for exact cases.

FIXED_DOLLAR_RISK floors budget / (entry-to-stop points × $2 + adverse stop slippage
× $2 + roundtrip commission). Entry slippage is already included in entry-to-stop
risk. Quantity caps at 100; zero yields ZERO_RISK_QUANTITY. Fixed-quantity is default.
Explicit leg quantities must match the sized quantity (no implicit proportional sizing).

`ctx.frames` contains only last confirmed Bar per 1m/5m/15m/4h frame.
`ctx.features` holds immutable per-timeframe snapshots; `ctx.levels` and `ctx.zones`
are causal snapshots. Primary timeframe chooses callback frequency. The execution
resolution remains 1 minute. Advanced feature definitions are described separately.

Advanced plans retain a legacy reference `target_price` for compatibility; `target_legs` is
the authoritative set of planned targets. Charts show leg targets and actual fill markers,
not the weighted average as if it were an executed final fill.
