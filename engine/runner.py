"""Generic flat-entry strategy adapter over the unchanged minute fill engine."""

from decimal import Decimal as D, localcontext, ROUND_FLOOR, ROUND_CEILING
from dataclasses import dataclass, field
from datetime import date
import hashlib, statistics
import pandas as pd
from engine.legacy import reference as ref, metrics
from engine.strategy import Entry
from engine.strategy.loading import load
from engine.data import dataset, contexts, execution_days, candle
from engine.canonical import digest, clean


@dataclass(frozen=True)
class RunConfig:
    start: str = "2024-01-01"
    end: str = "2026-10-06"  # NY calendar date exclusive
    quantity: int = 1
    commission: str = "0"
    slippage: int = 0
    instrument: str = "MNQ"
    timeframe: str = "5m"
    dataset_profile: str = "legacy_2024_2026"
    execution_mode: str = "legacy_v1"
    max_trades_per_day: int | None = 1
    sizing_mode: str = "FIXED_QUANTITY"
    risk_budget: str = "100"
    frame_config: dict = field(
        default_factory=lambda: {
            "anchor": "00:00",
            "timezone": "UTC",
            "session": "extended",
        }
    )
    feature_config: dict = field(default_factory=dict)

    def validate(self):
        a, b = date.fromisoformat(self.start), date.fromisoformat(self.end)
        from engine.research.profiles import profile

        profile(self.dataset_profile).validate(self.start, self.end)
        if not isinstance(self.quantity, int) or not 1 <= self.quantity <= 100:
            raise ValueError("Quantity must be 1–100")
        from engine.timeframes import MINUTES, FrameConfig

        if self.instrument != "MNQ" or self.timeframe not in MINUTES:
            raise ValueError("Supported: MNQ, 1m/5m/15m/4h")
        FrameConfig(**self.frame_config).validate()
        if self.execution_mode not in ("legacy_v1", "extended_v1"):
            raise ValueError("Unknown execution mode")
        if self.max_trades_per_day is not None and (
            type(self.max_trades_per_day) is not int or self.max_trades_per_day < 1
        ):
            raise ValueError("Daily limit must be positive or null for unlimited")
        if (
            self.sizing_mode not in ("FIXED_QUANTITY", "FIXED_DOLLAR_RISK")
            or not D(self.risk_budget).is_finite()
            or D(self.risk_budget) <= 0
        ):
            raise ValueError("Invalid risk sizing")
        ref.Config(D(self.commission), self.slippage)


def signal(ctx, direction):
    f = ctx.fvg
    at = ctx.timestamp
    ny = at.tz_convert("America/New_York")
    sid = (
        f.id
        if f
        else hashlib.sha256(
            ("bars|" + str(ctx.bar.timestamp.value) + "|" + direction).encode()
        ).hexdigest()
    )
    formed = f.formation if f else ctx.bar.timestamp
    r = {
        "signal_id": sid + "@" + str(at.value),
        "fvg_id": sid,
        "direction": direction,
        "formation_date": ny.date(),
        "formation_time_utc": formed,
        "formation_time_ny": formed.tz_convert("America/New_York"),
        "opening_exception": f.opening_exception if f else False,
        "fvg_top": f.top if f else D(0),
        "fvg_bottom": f.bottom if f else D(0),
        "fvg_size_points": f.top - f.bottom if f else D(0),
        "entry_time_utc": at,
        "entry_time_ny": ny,
        "signal_close_price": ctx.bar.close,
        "atr14_simple_points": None,
    }
    for name, c in [("first", ctx.bar1), ("second", ctx.bar2)]:
        r[f"{name}_bar_time_utc"] = c.timestamp
        r[f"{name}_bar_time_ny"] = c.timestamp.tz_convert("America/New_York")
        for k in ["open", "high", "low", "close"]:
            r[f"{name}_bar_{k}"] = getattr(c, k)
        r[f"{name}_bar_body_ratio"] = (
            float(abs(c.close - c.open) / (c.high - c.low)) if c.high != c.low else None
        )
        r[f"{name}_bar_direction"] = (
            "bullish" if c.close > c.open else "bearish" if c.close < c.open else "doji"
        )
        r[f"{name}_bar_range"] = c.high - c.low
    return r


def run(source, params, config=RunConfig(), data=None, progress=lambda stage: None):
    config.validate()
    if (
        config.execution_mode == "extended_v1"
        or config.max_trades_per_day != 1
        or config.timeframe != "5m"
        or config.sizing_mode != "FIXED_QUANTITY"
    ):
        from engine.extended_runner import run as extended

        return extended(source, params, config, data, progress)
    strategy, p, _ = load(source, params)
    from engine.execution_profiles import load_data

    data = (
        data
        if data is not None
        else load_data(config, getattr(strategy, "feature", "bars"))
    )
    days, _ = ref.full_sessions(config.start, config.end)
    chosen = []
    eligible = []
    locked = set()
    audit = []
    metadata = {}
    cfg = ref.Config(D(config.commission), config.slippage)
    progress("Evaluating confirmed-bar strategy callbacks")
    with localcontext() as dec:
        dec.prec = 38
        for ctx in contexts(data, getattr(strategy, "feature", "bars")):
            ny = ctx.timestamp.tz_convert("America/New_York")
            day = ny.date().isoformat()
            # v1 exchange/session and no-overnight contract; strategy supplies its own cutoff.
            if (
                not config.start <= day < config.end
                or day not in days
                or not "09:30" <= ctx.bar.time < "16:00"
                or ny.strftime("%H:%M") >= "16:00"
            ):
                continue
            order = strategy.on_bar(ctx, p)
            if order is None:
                continue
            from engine.position import PositionPlan

            if isinstance(order, PositionPlan):
                raise ValueError("PositionPlan requires extended_v1 execution mode")
            if not isinstance(order, Entry) or order.direction not in ("LONG", "SHORT"):
                raise ValueError("on_bar must return Entry(LONG/SHORT) or None")
            sign = D(1) if order.direction == "LONG" else D(-1)
            price = ref.tick(ctx.bar.close) + sign * ref.TICK * config.slippage
            stop = D(str(order.stop))
            rr = D(str(order.target_r))
            if not stop.is_finite() or not rr.is_finite() or rr <= 0:
                raise ValueError("Stop and target R must be finite; target R positive")
            stop = ref.tick(stop, ROUND_FLOOR if sign == 1 else ROUND_CEILING)
            risk = (price - stop) * sign
            if order.max_risk is not None and (
                not D(str(order.max_risk)).is_finite() or D(str(order.max_risk)) <= 0
            ):
                raise ValueError("Maximum risk must be finite and positive")
            s = signal(ctx, order.direction)
            reason = (
                "NON_POSITIVE_RISK"
                if risk <= 0
                else (
                    "MAX_RISK_FILTER"
                    if order.max_risk is not None and risk >= D(str(order.max_risk))
                    else "ELIGIBLE"
                )
            )
            if reason == "ELIGIBLE":
                eligible.append(s)
                if day in locked:
                    reason = "DAILY_LOCK_COMPETING_SIGNAL"
                else:
                    locked.add(day)
                    reason = "SELECTED"
                    metadata[s["signal_id"]] = clean(order.metadata)
                    chosen.append(
                        {
                            **s,
                            "entry_price": price,
                            "stop_price": stop,
                            "target_price": ref.tick(price + sign * rr * risk),
                            "risk_points": risk,
                            "risk_usd": risk * ref.VALUE,
                        }
                    )
            audit.append({"signal_id": s["signal_id"], "reason": reason})
        progress("Executing selected entries with validated 1-minute fills")
        groups = execution_days(data["minutes"]) if chosen else {}
        management_events = []
        managed = callable(getattr(strategy, "manage", None)) and p.get(
            "management_enabled", True
        )
        if managed:
            from engine.managed import execute as execute_managed

            complete_bars = {
                r.timestamp_utc: candle(r)
                for r in data["bars"].itertuples(index=False)
                if r.is_complete_5m
            }
            trades = []
            for selected in chosen:
                # A fresh manager prevents entry precomputation from leaking future state.
                manager, _, _ = load(source, dict(p))
                trade, events = execute_managed(
                    selected,
                    groups[selected["formation_date"]],
                    cfg,
                    manager,
                    p,
                    complete_bars,
                )
                trades.append(trade)
                management_events.extend(events)
        else:
            trades = [ref.execute(s, groups[s["formation_date"]], cfg) for s in chosen]
        if config.quantity != 1:
            for t in trades:
                t["quantity"] = config.quantity
                for k in [
                    "risk_usd",
                    "pnl_usd",
                    "gross_pnl_usd",
                    "net_pnl_usd",
                    "commission_usd",
                ]:
                    t[k] *= config.quantity
        # Preserve the reference decimal128(24,9) artifact contract.
        if trades:
            trades = ref.frame_table(trades).to_pylist()
        for t in trades:
            t["metadata"] = metadata.get(t["signal_id"], {})
        progress("Calculating metrics")
        summary = metrics.summary(trades, eligible)
        # Generic strategies can enter outside CONT-A's three morning bins.
        for minute in range(660, 960, 30):
            label = f"{minute//60:02}:{minute%60:02}-{(minute+29)//60:02}:{(minute+29)%60:02}"
            clock = (
                lambda t: t["second_bar_time_ny"].hour * 60
                + t["second_bar_time_ny"].minute
            )
            summary["trigger_time_bins"][label] = {
                **metrics.performance(
                    [t for t in trades if minute <= clock(t) < minute + 30]
                ),
                "signals": sum(minute <= clock(s) < minute + 30 for s in eligible),
            }
        pnl = [float(t["net_pnl_usd"]) for t in trades]
        equity = 0
        trough = 0
        runup = 0
        for x in pnl:
            equity += x
            trough = min(trough, equity)
            runup = max(runup, equity - trough)
        summary["overall"].update(
            median_trade_usd=statistics.median(pnl) if pnl else None,
            max_runup_usd=runup if pnl else None,
        )
        for f in ["mfe_r", "mae_r"]:
            summary["excursions"]["average_" + f] = (
                statistics.mean(t[f] for t in trades) if trades else None
            )
        _, curve = metrics.drawdown(trades)
        result = {"trades": trades, "summary": summary, "equity": curve, "audit": audit}
        if managed:
            summary["management"] = {
                "events": len(management_events),
                "management_exit_count": sum(t["management_exit"] for t in trades),
                "average_locked_r_at_exit": (
                    statistics.mean(t["locked_r_at_exit"] for t in trades)
                    if trades
                    else None
                ),
                "profit_protected_usd": None,
                "version": "minute-close-next-start-v1",
            }
            result["management_events"] = management_events
        return result
