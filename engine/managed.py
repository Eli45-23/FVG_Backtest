"""Opt-in causal managed execution. Unmanaged execution remains the legacy function.
At minute close, fills win before callbacks. Requests activate at the next minute start.
"""

import hashlib
from decimal import Decimal as D, ROUND_FLOOR, ROUND_CEILING
import pandas as pd
from engine.legacy import reference
from engine.strategy import Bar, ManagementContext, MoveStop, StopChange

ONE = reference.ONE
FIVE = reference.FIVE
TICK = reference.TICK
VALUE = reference.VALUE
tick = reference.tick
MANAGEMENT_VERSION = "minute-close-next-start-v1"


def execute(s, minute_frame, config, manager, parameters, complete_bars):
    entry = s["entry_price"]
    stop = s["stop_price"]
    target = s["target_price"]
    long = s["direction"] == "LONG"
    sign = D(1) if long else D(-1)
    at = s["entry_time_utc"]
    end = pd.Timestamp(s["entry_time_ny"].date(), tz="America/New_York") + pd.Timedelta(
        hours=16
    )
    end = end.tz_convert("UTC")
    minutes = (
        minute_frame.set_index("ts_event", drop=False)
        if "ts_event" in minute_frame.columns
        else minute_frame
    )
    events = []
    history = []
    trade_id = hashlib.sha256(("CONT-A-v1|" + s["signal_id"]).encode()).hexdigest()
    peak = entry
    trough = entry
    conflict = False
    gap = False
    bars = 0
    while at < end:
        if at not in minutes.index:
            raise ValueError(
                f"Missing execution minute {at}; no synthetic fill or silent skip"
            )
        row = minutes.loc[at]
        if isinstance(row, pd.DataFrame):
            raise ValueError("Duplicate execution minute")
        # Exits and excursions only from the owned interval, including the exit minute.
        high = row.high
        low = row.low
        op = row.open
        cl = row.close
        if high < max(op, cl) or low > min(op, cl) or high < low:
            raise ValueError("Invalid execution OHLC")
        peak = max(peak, high)
        trough = min(trough, low)
        bars += 1
        hit_stop = low <= stop if long else high >= stop
        hit_target = high >= target if long else low <= target
        conflict = hit_stop and hit_target
        if hit_stop:
            # Adverse gap stop executes at worse open; same-minute stop priority is unconditional.
            base = min(stop, op) if long else max(stop, op)
            gap = base != stop
            reason = "STOP"
        elif hit_target:
            base = target
            reason = "TARGET"
        elif at + ONE == end:
            base = cl
            reason = "SESSION_CLOSE"
        else:
            observed = at + ONE
            minute = Bar(at, op, high, low, cl, int(getattr(row, "volume", 0)))
            completed = complete_bars.get(observed - FIVE)
            if completed is not None and completed.timestamp < s["entry_time_utc"]:
                completed = None
            requests = []
            for event, bar in [("minute_close", None)] + (
                [("bar_5m_close", completed)] if completed else []
            ):
                ctx = ManagementContext(
                    observed,
                    event,
                    s["entry_time_utc"],
                    entry,
                    s["stop_price"],
                    stop,
                    target,
                    s["direction"],
                    s["risk_points"],
                    max(D(0), peak - entry if long else entry - trough),
                    max(D(0), entry - trough if long else peak - entry),
                    minute,
                    bar,
                    tuple(history),
                )
                try:
                    response = manager.manage(ctx, parameters)
                except Exception as exc:
                    raise ValueError(
                        f"Management callback failed at {observed}: {exc}"
                    ) from exc
                for request in (
                    []
                    if response is None
                    else response if isinstance(response, (list, tuple)) else [response]
                ):
                    if not isinstance(request, MoveStop):
                        raise ValueError(
                            "Management must return MoveStop, a list, or None"
                        )
                    requested = D(str(request.price))
                    if not requested.is_finite():
                        raise ValueError("Invalid management stop: must be finite")
                    if (requested - stop) * sign < 0:
                        raise ValueError("Management may not loosen stop")
                    effective = tick(requested, ROUND_FLOOR if long else ROUND_CEILING)
                    if (effective - stop) * sign < 0:
                        raise ValueError("Rounded management stop would loosen risk")
                    if (target - effective) * sign <= 0:
                        raise ValueError(
                            "Managed stop must remain strictly inside fixed target"
                        )
                    if effective != stop:
                        requests.append((effective, requested, request, event))
            if requests:
                effective, requested, request, event = max(
                    requests, key=lambda x: x[0] * sign
                )
                eid = hashlib.sha256(
                    (
                        trade_id + "|" + str(observed.value) + "|" + str(len(events))
                    ).encode()
                ).hexdigest()
                events.append(
                    {
                        "event_id": eid,
                        "trade_id": trade_id,
                        "timestamp": observed,
                        "source_event": event,
                        "trigger_type": request.trigger_type,
                        "trigger_value": request.trigger_value,
                        "previous_stop": stop,
                        "requested_stop": requested,
                        "effective_stop": effective,
                        "activation_timestamp": observed,
                        "reason": request.reason,
                        "metadata": {"policy_version": MANAGEMENT_VERSION},
                    }
                )
                history.append(
                    StopChange(observed, observed, stop, effective, request.reason)
                )
                stop = effective
            at += ONE
            continue
        exit_price = tick(base) - sign * TICK * config.slippage_ticks
        break
    else:
        raise ValueError("Entry is outside allowed execution session")
    gross_points = (exit_price - entry) * sign
    gross_usd = gross_points * VALUE
    commission = config.commission_per_side_usd * 2
    net = gross_usd - commission
    mfe = max(D(0), peak - entry if long else entry - trough)
    mae = max(D(0), entry - trough if long else peak - entry)
    exit_time = (
        at + ONE
    )  # OHLC reveals an interval, not an exact intraminute fill instant.
    r = {
        **s,
        "trade_id": hashlib.sha256(
            ("CONT-A-v1|" + s["signal_id"]).encode()
        ).hexdigest(),
        "quantity": 1,
        "exit_bar_start_utc": at,
        "exit_bar_start_ny": at.tz_convert("America/New_York"),
        "exit_time_utc": exit_time,
        "exit_time_ny": exit_time.tz_convert("America/New_York"),
        "exit_price": exit_price,
        "exit_reason": reason,
        "pnl_points": gross_points,
        "pnl_usd": net,
        "gross_pnl_points": gross_points,
        "net_pnl_points": net / VALUE,
        "gross_pnl_usd": gross_usd,
        "net_pnl_usd": net,
        "commission_usd": commission,
        "result_r": float(net / s["risk_usd"]),
        "gross_result_r": float(gross_points / s["risk_points"]),
        "mfe_points": mfe,
        "mae_points": mae,
        "mfe_r": float(mfe / s["risk_points"]),
        "mae_r": float(mae / s["risk_points"]),
        "duration_minutes": int((exit_time - s["entry_time_utc"]).total_seconds() / 60),
        "duration_1m_bars": bars,
        "same_minute_stop_target_conflict": conflict,
        "adverse_stop_gap": gap,
        "exit_minute_extrema_order_unknown": reason != "SESSION_CLOSE",
        "entry_hour": s["entry_time_ny"].hour,
        "entry_minute": s["entry_time_ny"].minute,
        "weekday": s["entry_time_ny"].day_name(),
        "month": s["entry_time_ny"].month,
        "year": s["entry_time_ny"].year,
    }
    r.update(
        final_stop_price=stop,
        management_exit=reason == "STOP" and stop != s["stop_price"],
        management_event_count=len(events),
        locked_r_at_exit=float((stop - entry) * sign / s["risk_points"]),
    )
    return r, events
