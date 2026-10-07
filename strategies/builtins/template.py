from decimal import Decimal as D
from engine.strategy import Float, Entry


class Strategy:
    name = "My Strategy"
    feature = "bars"
    inputs = [Float("target_r", "Target R", 2, min=0.25, step=0.25)]

    def on_bar(self, ctx, p):
        # Only confirmed candles are exposed. Replace False with your setup.
        if False:
            return Entry("LONG", ctx.bar.low - ctx.tick_size, D(str(p["target_r"])))
        return None
