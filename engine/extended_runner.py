"""Explicit extended execution: sequential flat positions, same trusted minute conventions."""

from decimal import Decimal as D, ROUND_FLOOR, ROUND_CEILING
from dataclasses import replace
from collections import defaultdict
import pandas as pd
from engine.strategy import Context, Entry
from engine.strategy.loading import load
from engine.position import PositionPlan
from engine.execution_profiles import load_data
from engine.data import candle, execution_days, contexts
from engine.timeframes import aggregate, FrameConfig, MINUTES
from engine.features import FeatureHub, frozen
from engine.legacy import reference as ref, metrics
from engine.research.levels import schedule, SessionConfig
from engine.partial_execution import execute


def run(source, params, config, data=None, progress=lambda stage: None):
    from engine.runner import signal

    strategy, p, _ = load(source, params)
    data = (
        data
        if data is not None
        else load_data(config, getattr(strategy, "feature", "bars"))
    )
    start = pd.Timestamp(config.start, tz="America/New_York").tz_convert(
        "UTC"
    ) - pd.Timedelta(days=30)
    end = pd.Timestamp(config.end, tz="America/New_York").tz_convert("UTC")
    raw = data["minutes"]
    times = raw.ts_event if "ts_event" in raw else raw.index
    raw = raw.loc[(times >= start) & (times < end)]
    data = {
        **data,
        "bars": data["bars"].loc[
            (data["bars"].timestamp_utc >= start) & (data["bars"].timestamp_utc < end)
        ],
    }
    framecfg = FrameConfig(**config.frame_config)
    frames = {tf: aggregate(raw, tf, framecfg) for tf in ["1m", "15m", "4h"]}
    frames["5m"] = data["bars"]
    hub = FeatureHub(
        frames,
        settings=config.feature_config,
        session=SessionConfig(**config.feature_config.get("session", {})),
    )
    groups = execution_days(raw)
    sessions = schedule()
    days, _ = ref.full_sessions(config.start, config.end)
    if getattr(strategy, "feature", "bars") == "fvg_second":
        if config.timeframe != "5m":
            raise ValueError("FVG feature requires 5m primary")
        source_contexts = contexts(data, "fvg_second")
    else:

        def generated():
            history = []
            duration = pd.Timedelta(minutes=MINUTES[config.timeframe])
            for r in frames[config.timeframe].itertuples(index=False):
                if not r.is_complete_5m:
                    history = []
                    continue
                b = candle(r)
                if history and b.timestamp - history[-1].timestamp != duration:
                    history = []
                previous = history[-1] if history else None
                history = (history + [b])[-256:]
                yield Context(
                    b.timestamp + duration,
                    b,
                    previous,
                    tuple(history),
                    bar1=previous or b,
                    bar2=b,
                )

        source_contexts = generated()
    trades = []
    eligible = []
    audit = []
    management = []
    counts = defaultdict(int)
    busy_until = None
    complete = {
        r.timestamp_utc: candle(r)
        for r in data["bars"].itertuples(index=False)
        if r.is_complete_5m
    }
    progress("Processing causal extended execution")
    for ctx in source_contexts:
        at = ctx.timestamp
        day = str(at.tz_convert("America/New_York").date())
        hub.advance(at)
        session = sessions.get(day)
        if (
            not config.start <= day < config.end
            or not session
            or (config.session_policy == "XNYS_FULL" and day not in days)
            or not session[0] <= ctx.bar.timestamp < at < session[1]
        ):
            continue
        views, features = hub.snapshots()
        ctx = replace(
            ctx,
            frames=views,
            features=features,
            levels=hub.active_levels(at),
            zones=frozen(hub.zones["4h"].zones),
        )
        order = strategy.on_bar(ctx, p)
        if order is None:
            continue
        if not isinstance(order, Entry):
            raise ValueError("Return Entry or PositionPlan")
        s = signal(ctx, order.direction)
        reason = None
        sign = D(1) if order.direction == "LONG" else D(-1)
        if order.direction not in ("LONG", "SHORT"):
            raise ValueError("Invalid direction")
        entry = ref.tick(ctx.bar.close) + sign * ref.TICK * config.slippage
        stop = D(str(order.stop))
        rr = D(str(order.target_r))
        if not stop.is_finite() or not rr.is_finite() or rr <= 0:
            raise ValueError("Invalid stop/target")
        stop = ref.tick(stop, ROUND_FLOOR if sign == 1 else ROUND_CEILING)
        if order.max_risk is not None and (
            not D(str(order.max_risk)).is_finite() or D(str(order.max_risk)) <= 0
        ):
            raise ValueError("Invalid maximum risk")
        risk = (entry - stop) * sign
        if risk <= 0:
            reason = "NON_POSITIVE_RISK"
        elif order.max_risk is not None and risk >= D(str(order.max_risk)):
            reason = "MAX_RISK_FILTER"
        elif busy_until is not None and at < busy_until:
            reason = "POSITION_OPEN"
        elif (
            config.max_trades_per_day is not None
            and counts[day] >= config.max_trades_per_day
        ):
            reason = "DAILY_TRADE_LIMIT"
        unit_cost = (risk + ref.TICK * config.slippage) * ref.VALUE + 2 * D(
            config.commission
        )
        raw_quantity = (
            D(config.quantity)
            if config.sizing_mode == "FIXED_QUANTITY"
            else D(config.risk_budget) / unit_cost if unit_cost > 0 else D(0)
        )
        quantity = (
            config.quantity
            if config.sizing_mode == "FIXED_QUANTITY"
            else min(100, int(raw_quantity.to_integral_value(rounding=ROUND_FLOOR)))
        )
        if reason is None and quantity < 1:
            reason = "ZERO_RISK_QUANTITY"
        if reason:
            audit.append(
                {"signal_id": s["signal_id"], "timestamp": at, "reason": reason}
            )
            continue
        eligible.append(s)
        counts[day] += 1
        s.update(
            entry_price=entry,
            stop_price=stop,
            target_price=ref.tick(entry + sign * rr * risk),
            risk_points=risk,
            risk_usd=risk * ref.VALUE * quantity,
            trade_sequence_number=counts[day],
            sizing_mode=config.sizing_mode,
            risk_budget=config.risk_budget,
            raw_calculated_quantity=str(raw_quantity),
            final_quantity=quantity,
            estimated_stop_risk=unit_cost * quantity,
            actual_executed_risk=risk * ref.VALUE * quantity,
            metadata=order.metadata,
        )
        manager, _, _ = load(source, dict(p))
        managed = callable(getattr(manager, "manage", None)) and p.get(
            "management_enabled", True
        )
        trade, events = execute(
            s,
            groups[ctx.timestamp.tz_convert("America/New_York").date()],
            ref.Config(D(config.commission), config.slippage),
            quantity,
            order,
            manager if managed else None,
            p,
            complete,
            session[1],
        )
        busy_until = trade["exit_time_utc"]
        trades.append(trade)
        management.extend(events)
        audit.append(
            {"signal_id": s["signal_id"], "timestamp": at, "reason": "SELECTED"}
        )
    summary = metrics.summary(trades, eligible)
    from engine.reporting import extend

    extend(summary, trades, eligible, management, metrics)
    _, curve = metrics.drawdown(trades)
    return dict(
        trades=trades,
        summary=summary,
        equity=curve,
        audit=audit,
        management_events=management,
    )
