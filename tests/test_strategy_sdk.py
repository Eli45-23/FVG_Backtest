from dataclasses import FrozenInstanceError
from decimal import Decimal as D
import pytest
from engine.strategy import Float, Int, Bool, Choice, Time, Session, String, Entry
from engine.strategy.loading import load
from engine.runner import RunConfig, run
from engine.data import contexts
from engine.legacy import ROOT


@pytest.mark.parametrize(
    "field,value",
    [
        (Float("a", "A", 1, min=0, step=0.25), 1.25),
        (Int("a", "A", 1), 2),
        (Bool("a", "A"), True),
        (Choice("a", "A", "x", ["x", "y"]), "y"),
        (Time("a", "A", "10:00"), "10:30"),
        (Session("a", "A", "09:30-16:00"), "10:00-11:00"),
        (String("a", "A"), "text"),
    ],
)
def test_input_types(field, value):
    assert field.validate(value) == value


@pytest.mark.parametrize(
    "field,value",
    [
        (Float("a", "A", 1, min=0), -1),
        (Float("a", "A", 1), float("nan")),
        (Int("a", "A", 1), 1.5),
        (Bool("a", "A"), "false"),
        (Choice("a", "A", "x", ["x"]), "y"),
        (Time("a", "A", "10:00"), "24:01"),
        (Session("a", "A", "x"), "bad"),
    ],
)
def test_invalid_inputs(field, value):
    with pytest.raises(ValueError):
        field.validate(value)


def test_discovery_and_override():
    s = (ROOT / "strategies/builtins/cont_a.py").read_text()
    obj, p, fields = load(s, {"max_risk": 75})
    assert p["max_risk"] == 75 and len(fields) == 4
    with pytest.raises(TypeError):
        p["max_risk"] = 100


@pytest.mark.parametrize(
    "source",
    [
        "x =",
        "class Strategy: pass",
        "class Strategy:\n def on_bar(self): pass",
        "class Strategy:\n def on_bar(self,c,p): pass\n def on_position(self): pass",
    ],
)
def test_bad_source(source):
    with pytest.raises((ValueError, SyntaxError)):
        load(source)


def test_dates_rejected():
    with pytest.raises(ValueError):
        RunConfig(start="2025-02-03", end="2025-01-01").validate()


def test_context_no_future():
    import sys

    sys.path.insert(0, str(ROOT / "outputs/tests"))
    from test_cont_a import setup

    bars, fvgs = setup()
    ctx = list(contexts({"bars": bars, "fvgs": fvgs}, "fvg_second"))[0]
    assert all(b.timestamp < ctx.timestamp for b in ctx.history)
    assert not hasattr(ctx, "data")
    with pytest.raises(FrozenInstanceError):
        ctx.timestamp = None


def test_new_non_fvg_strategy():
    import sys

    sys.path.insert(0, str(ROOT / "outputs/tests"))
    from test_cont_a import setup, minutes, signal

    bars, fvgs = setup()
    s = signal()
    # Generic code enters only at the last confirmed fixture bar, no FVG hooks.
    code = """from engine.strategy import Entry
class Strategy:
 def on_bar(self,ctx,p):
  if ctx.bar.close == 114: return Entry('LONG',ctx.bar.low-ctx.tick_size)
"""
    m = minutes(s, [[114, 140, 113, 130]])
    for k in ["open", "high", "low", "close"]:
        m[k] = m[k].map(lambda x: int(x * 10**9))
    result = run(
        code,
        {},
        RunConfig(start="2024-02-05", end="2024-02-06"),
        {"bars": bars, "fvgs": fvgs, "minutes": m},
    )
    assert len(result["trades"]) == 1 and result["trades"][0]["exit_reason"] == "TARGET"


def test_empty_strategy_result():
    import sys

    sys.path.insert(0, str(ROOT / "outputs/tests"))
    from test_cont_a import setup

    b, f = setup()
    r = run(
        (ROOT / "strategies/builtins/template.py").read_text(),
        {},
        data={"bars": b, "fvgs": f, "minutes": b.iloc[:0]},
    )
    assert r["trades"] == [] and r["summary"]["overall"]["profit_factor"] is None
