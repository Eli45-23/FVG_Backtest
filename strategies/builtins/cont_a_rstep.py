from decimal import Decimal as D
from engine.strategy import Float, Bool, Time, Entry, MoveStop


class Strategy:
    name = "CONT-A Quality R-Step"
    feature = "fvg_second"
    inputs = [
        Bool("management_enabled", "Enable causal R-Step management", True),
        Float(
            "max_risk", "Maximum structural risk (0 = disabled)", 100, min=0, step=0.25
        ),
        Float("target_r", "Target R", 2, min=0.25, max=20, step=0.25),
        Bool("exclude_middle", "Exclude trigger 10:00–10:29", True),
        Time("entry_before", "Trigger must start before", "11:00"),
    ]

    def on_bar(self, ctx, p):
        if ctx.bar.time >= p["entry_before"]:
            return None
        if p["exclude_middle"] and "10:00" <= ctx.bar.time < "10:30":
            return None
        f, a, b = ctx.fvg, ctx.bar1, ctx.bar2
        cap = D(str(p["max_risk"])) or None
        target = D(str(p["target_r"]))
        if (
            f.direction == "bullish"
            and a.low > f.top
            and b.low > f.top
            and b.close > a.high
        ):
            return Entry("LONG", a.low - ctx.tick_size, target, cap)
        if (
            f.direction == "bearish"
            and a.high < f.bottom
            and b.high < f.bottom
            and b.close < a.low
        ):
            return Entry("SHORT", a.high + ctx.tick_size, target, cap)
        return None

    def manage(self, ctx, p):
        # Whole later bars must start after the initial +5 activation.
        if not ctx.stop_history:
            if ctx.event == "minute_close" and ctx.touched_profit_points(50):
                price = ctx.entry_price + ctx.direction_sign * 5
                if (ctx.target - price) * ctx.direction_sign > 0:
                    return MoveStop(price, "+50 touch → +5", "points_touch", 50)
            return None
        if (
            ctx.completed_bar is None
            or ctx.completed_bar.timestamp < ctx.stop_history[0].activation_timestamp
        ):
            return None
        requests = []
        for held, locked in [("1", "1"), ("1.5", "1.25"), ("1.75", "1.5")]:
            price = ctx.price_at_r(locked)
            if (
                ctx.completed_bar_holds_beyond_r(held)
                and (price - ctx.current_stop) * ctx.direction_sign > 0
            ):
                requests.append(
                    MoveStop(
                        price, f"{held}R hold → +{locked}R", "complete_5m_hold", held
                    )
                )
        return requests
