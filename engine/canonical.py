"""Stable exact serialization for reference equivalence and immutable artifacts."""

import hashlib, json
from decimal import Decimal
from datetime import date, datetime
import numpy as np


def clean(v):
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items()}
    if isinstance(v, (tuple, list)):
        return [clean(x) for x in v]
    if isinstance(v, np.generic):
        return clean(v.item())
    if isinstance(v, float) and not np.isfinite(v):
        return None
    return v


def dumps(v):
    return json.dumps(clean(v), sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(v):
    return hashlib.sha256(dumps(v).encode()).hexdigest()
