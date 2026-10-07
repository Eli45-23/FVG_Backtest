from decimal import Decimal as D
from engine.strategy import Float, Bool, Time, Entry


class Strategy:
    name = "CONT-A Second Candle"
    feature = "fvg_second"
    inputs = [
        Float(
            "max_risk", "Maximum structural risk (0 = disabled)", 0, min=0, step=0.25
        ),
        Float("target_r", "Target R", 2, min=0.25, max=20, step=0.25),
        Bool("exclude_middle", "Exclude trigger 10:00–10:29", False),
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
