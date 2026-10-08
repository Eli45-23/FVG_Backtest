"""Opt-in flat position executor. Stop-first, next-minute updates, auditable leg fills."""

from decimal import Decimal as D, ROUND_FLOOR, ROUND_CEILING
from types import MappingProxyType
import pandas as pd
from engine.legacy import reference as ref
from engine.position import PositionPlan, TargetLeg, PositionManagementContext
from engine.strategy import MoveStop, StopChange, Bar
from engine.canonical import digest


def execute(s, minutes, cfg, quantity, plan, manager, params, complete_bars, end):
    sign = D(1) if s["direction"] == "LONG" else D(-1)
    entry = s["entry_price"]
    risk = s["risk_points"]
    stop = s["stop_price"]
    legs = (
        list(plan.legs)
        if isinstance(plan, PositionPlan)
        else [TargetLeg(quantity, D(str(plan.target_r)))]
    )
    if (
        not legs
        or any(not isinstance(x.quantity, int) or x.quantity <= 0 for x in legs)
        or sum(x.quantity for x in legs) != quantity
    ):
        raise ValueError("Target leg quantities must sum to initial quantity")
    pending = []
    for i, leg in enumerate(legs):
        rr = D(str(leg.target_r)) if leg.target_r is not None else None
        if rr is not None and (not rr.is_finite() or rr <= 0):
            raise ValueError("Target R must be finite and positive")
        pending.append(
            {
                "name": leg.name,
                "index": i,
                "quantity": leg.quantity,
                "price": ref.tick(entry + sign * risk * rr) if rr is not None else None,
            }
        )
    if "ts_event" in minutes:
        minutes = minutes.set_index("ts_event", drop=False)
    at = s["entry_time_utc"]
    remaining = quantity
    fills = []
    updates = []
    history = []
    peak = trough = entry
    bars = 0
    conflicts = 0
    tp1 = False
    id = digest(["extended-v1", s["signal_id"]])

    def fill(q, price, reason, leg):
        nonlocal remaining
        exit_price = ref.tick(price) - sign * ref.TICK * cfg.slippage_ticks
        commission = cfg.commission_per_side_usd * 2 * q
        fills.append(
            dict(
                leg=leg,
                quantity=q,
                exit_price=exit_price,
                timestamp=at + ref.ONE,
                reason=reason,
                gross_pnl_usd=(exit_price - entry) * sign * ref.VALUE * q,
                commission_usd=commission,
                net_pnl_usd=(exit_price - entry) * sign * ref.VALUE * q - commission,
                remaining_quantity=remaining - q,
            )
        )
        remaining -= q

    while at < end and remaining:
        if at not in minutes.index:
            raise ValueError(f"Missing execution minute {at}; no synthetic fill")
        r = minutes.loc[at]
        if isinstance(r, pd.DataFrame):
            raise ValueError("Duplicate execution minute")
        if r.high < max(r.open, r.close, r.low) or r.low > min(r.open, r.close):
            raise ValueError("Invalid execution OHLC")
        bars += 1
        peak = max(peak, r.high)
        trough = min(trough, r.low)
        stop_hit = r.low <= stop if sign == 1 else r.high >= stop
        targets = [
            x
            for x in pending
            if x["price"] is not None
            and (r.high >= x["price"] if sign == 1 else r.low <= x["price"])
        ]
        if stop_hit:
            conflicts += bool(targets)
            fill(
                remaining,
                min(stop, r.open) if sign == 1 else max(stop, r.open),
                "STOP",
                "remaining",
            )
            break
        for leg in sorted(targets, key=lambda x: (x["price"] * sign, x["index"])):
            fill(leg["quantity"], leg["price"], "TARGET", leg["name"])
            pending.remove(leg)
            tp1 = True
        if not remaining:
            break
        if at + ref.ONE == end:
            fill(remaining, r.close, "SESSION_CLOSE", "remaining")
            break
        observed = at + ref.ONE
        requests = []
        if (
            tp1
            and isinstance(plan, PositionPlan)
            and plan.break_even_after_tp1
            and (entry - stop) * sign > 0
        ):
            requests.append(MoveStop(entry, "TP1 -> BE", "partial_fill"))
        minute = Bar(at, r.open, r.high, r.low, r.close, int(r.volume))
        completed = complete_bars.get(observed - ref.FIVE)
        if completed is not None and completed.timestamp < s["entry_time_utc"]:
            completed = None
        if manager is not None:
            for kind, b in [("minute_close", None)] + (
                [("bar_5m_close", completed)] if completed else []
            ):
                active_targets = [x["price"] for x in pending if x["price"] is not None]
                target = (
                    min(active_targets, key=lambda x: x * sign)
                    if active_targets
                    else s["target_price"]
                )
                ctx = PositionManagementContext(
                    observed,
                    kind,
                    s["entry_time_utc"],
                    entry,
                    s["stop_price"],
                    stop,
                    target,
                    s["direction"],
                    risk,
                    max(D(0), peak - entry if sign == 1 else entry - trough),
                    max(D(0), entry - trough if sign == 1 else peak - entry),
                    minute,
                    b,
                    tuple(history),
                    ref.TICK,
                    quantity,
                    remaining,
                    tuple(MappingProxyType(f.copy()) for f in fills),
                )
                response = manager.manage(ctx, params)
                requests.extend(
                    []
                    if response is None
                    else (
                        list(response)
                        if isinstance(response, (list, tuple))
                        else [response]
                    )
                )
        effective = []
        for request in requests:
            if not isinstance(request, MoveStop):
                raise ValueError("Management returns MoveStop only")
            value = D(str(request.price))
            if not value.is_finite() or (value - stop) * sign < 0:
                raise ValueError("Invalid/loosening stop")
            value = ref.tick(value, ROUND_FLOOR if sign == 1 else ROUND_CEILING)
            if any(
                x["price"] is not None and (x["price"] - value) * sign <= 0
                for x in pending
            ):
                raise ValueError("Stop must remain inside remaining targets")
            if value != stop:
                effective.append((value, request))
        if effective:
            value, request = max(effective, key=lambda x: x[0] * sign)
            updates.append(
                dict(
                    event_id=digest([id, str(observed), len(updates)]),
                    trade_id=id,
                    previous_stop=stop,
                    effective_stop=value,
                    requested_stop=request.price,
                    activation_timestamp=observed,
                    timestamp=observed,
                    reason=request.reason,
                    remaining_quantity=remaining,
                )
            )
            history.append(StopChange(observed, observed, stop, value, request.reason))
            stop = value
        at += ref.ONE
    if remaining:
        raise ValueError("Position not closed within session")
    gross = sum(f["gross_pnl_usd"] for f in fills)
    fees = sum(f["commission_usd"] for f in fills)
    net = gross - fees
    weighted = sum(f["exit_price"] * f["quantity"] for f in fills) / quantity
    mfe = max(D(0), peak - entry if sign == 1 else entry - trough)
    mae = max(D(0), entry - trough if sign == 1 else peak - entry)
    exit_time = at + ref.ONE
    trade = {
        **s,
        "trade_id": id,
        "quantity": quantity,
        "initial_quantity": quantity,
        "remaining_quantity": 0,
        "partial_execution_history": fills,
        "exit_price": weighted,
        "weighted_exit": weighted,
        "exit_time_utc": exit_time,
        "exit_time_ny": exit_time.tz_convert("America/New_York"),
        "exit_bar_start_utc": at,
        "exit_bar_start_ny": at.tz_convert("America/New_York"),
        "exit_reason": fills[-1]["reason"],
        "risk_usd": risk * ref.VALUE * quantity,
        "pnl_usd": net,
        "net_pnl_usd": net,
        "gross_pnl_usd": gross,
        "commission_usd": fees,
        "pnl_points": gross / ref.VALUE / quantity,
        "gross_pnl_points": gross / ref.VALUE / quantity,
        "net_pnl_points": net / ref.VALUE / quantity,
        "result_r": float(net / (risk * ref.VALUE * quantity)),
        "gross_result_r": float(gross / (risk * ref.VALUE * quantity)),
        "mfe_points": mfe,
        "mae_points": mae,
        "mfe_r": float(mfe / risk),
        "mae_r": float(mae / risk),
        "duration_minutes": int((exit_time - s["entry_time_utc"]).total_seconds() / 60),
        "duration_1m_bars": bars,
        "same_minute_stop_target_conflict": bool(conflicts),
        "management_exit": fills[-1]["reason"] == "STOP" and stop != s["stop_price"],
        "final_stop_price": stop,
        "management_event_count": len(updates),
        "locked_r_at_exit": float((stop - entry) * sign / risk),
        "weekday": s["entry_time_ny"].day_name(),
        "month": s["entry_time_ny"].month,
        "year": s["entry_time_ny"].year,
        "entry_hour": s["entry_time_ny"].hour,
        "entry_minute": s["entry_time_ny"].minute,
    }
    return trade, updates
