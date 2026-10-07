"""Load trusted Python only inside a worker. This is not a sandbox."""

import inspect
from dataclasses import asdict
from types import MappingProxyType
from engine.strategy import Input


def load(source, values=None):
    ns = {"__name__": "lab_strategy"}
    exec(compile(source, "strategy.py", "exec"), ns)
    strategy = ns.get("Strategy")
    if not inspect.isclass(strategy):
        raise ValueError("Define class Strategy with on_bar(self, ctx, params)")
    obj = strategy()
    if not callable(getattr(obj, "on_bar", None)):
        raise ValueError("Missing on_bar hook")
    if len(inspect.signature(obj.on_bar).parameters) != 2:
        raise ValueError("on_bar requires ctx and params")
    if hasattr(obj, "on_position"):
        raise ValueError("Use manage(ctx, params), not on_position")
    if hasattr(obj, "manage") and (
        not callable(obj.manage) or len(inspect.signature(obj.manage).parameters) != 2
    ):
        raise ValueError("manage requires ctx and params")
    if getattr(obj, "feature", "bars") not in ("bars", "fvg_second"):
        raise ValueError("Unsupported feature provider")
    inputs = getattr(obj, "inputs", [])
    ids = [i.id for i in inputs if isinstance(i, Input)]
    if len(ids) != len(inputs) or len(set(ids)) != len(ids):
        raise ValueError("Inputs must have unique IDs")
    supplied = values or {}
    if set(supplied) - set(ids):
        raise ValueError(
            "Unknown input IDs: " + ",".join(sorted(set(supplied) - set(ids)))
        )
    params = {i.id: i.validate(supplied.get(i.id, i.default)) for i in inputs}
    return obj, MappingProxyType(params), [asdict(i) for i in inputs]
