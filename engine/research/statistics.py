"""Date-cluster bootstrap of matched differences; no event-independence assumption."""

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class StatisticsConfig:
    seed: int = 1729
    iterations: int = 2000
    minimum_dates: int = 10

    def __post_init__(self):
        if not 100 <= self.iterations <= 10000 or self.minimum_dates < 2:
            raise ValueError("Invalid inference settings")


def clustered(dates, event_values, baseline_values, config=StatisticsConfig()):
    dates = np.asarray(dates)
    y = np.asarray(event_values, dtype=float)
    b = np.asarray(baseline_values, dtype=float)
    good = np.isfinite(y) & np.isfinite(b)
    dates, y, b = dates[good], y[good], b[good]
    unique = np.unique(dates)
    groups = [np.flatnonzero(dates == d) for d in unique]
    n = len(groups)
    if not n:
        return dict(
            events=0,
            unique_dates=0,
            mean=None,
            median=None,
            event_probability=None,
            baseline_probability=None,
            effect=None,
            relative_effect=None,
            ci95=None,
            p_value=None,
            small_sample=True,
        )
    # Equal-weight daily means: repeated events cannot increase the independent unit count.
    dy = np.array([y[g].mean() for g in groups])
    db = np.array([b[g].mean() for g in groups])
    delta = dy - db
    effect = float(delta.mean())
    rng = np.random.default_rng(config.seed)
    sampled = rng.integers(0, n, size=(config.iterations, n))
    draws = delta[sampled].mean(axis=1)
    # Centered cluster bootstrap null distribution, two-sided +1 correction.
    null = draws - effect
    p = (
        float((1 + np.sum(np.abs(null) >= abs(effect))) / (config.iterations + 1))
        if n >= 2
        else None
    )
    baseline = float(db.mean())
    return dict(
        events=len(y),
        unique_dates=n,
        mean=float(y.mean()),
        median=float(np.median(y)),
        standard_deviation=float(np.std(y, ddof=1)) if len(y) > 1 else None,
        event_probability=float(dy.mean()),
        baseline_probability=baseline,
        effect=effect,
        relative_effect=effect / baseline if baseline else None,
        ci95=[float(x) for x in np.quantile(draws, [0.025, 0.975])] if n >= 2 else None,
        p_value=p,
        small_sample=n < config.minimum_dates,
        estimand="Equal-weight NY-date mean matched difference",
        seed=config.seed,
        iterations=config.iterations,
    )


def benjamini_hochberg(values):
    valid = [(i, p) for i, p in enumerate(values) if p is not None]
    valid.sort(key=lambda x: x[1])
    out = [None] * len(values)
    previous = 1.0
    for rank in range(len(valid), 0, -1):
        i, p = valid[rank - 1]
        previous = min(previous, p * len(valid) / rank)
        out[i] = previous
    return out
