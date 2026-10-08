"""Bounded columnar queries and date-cluster matched comparisons for v2 studies."""

import json
from engine.research.columnar import query, predicate
from engine.research.numeric import NUMERIC, CATEGORIES, validate
from engine.research.statistics import clustered, StatisticsConfig, benjamini_hochberg


def where(filters, numeric):
    clause, args = predicate(filters)
    validate(numeric)
    for key, rule in numeric.items():
        for bound, op in [("min", ">="), ("max", "<=")]:
            if rule.get(bound) is not None:
                clause += f' AND e."{key}" {op} ?'
                args.append(float(rule[bound]))
    return clause, args


def page(
    root,
    filters=None,
    numeric=None,
    offset=0,
    limit=100,
    sort="timestamp_utc",
    descending=False,
):
    if sort not in (*NUMERIC, *CATEGORIES, "timestamp_utc", "event_id"):
        raise ValueError("Unsupported sort field")
    clause, args = where(filters or {}, numeric or {})
    count = query(root, f"SELECT count(*) n FROM events e WHERE {clause}", args)[0]["n"]
    rows = query(
        root,
        f'SELECT payload FROM events e WHERE {clause} ORDER BY "{sort}" {"DESC" if descending else "ASC"} NULLS LAST,event_id LIMIT ? OFFSET ?',
        [*args, limit, offset],
    )
    return dict(count=count, events=[json.loads(r["payload"]) for r in rows])


def group_expression(group, numeric):
    if group in CATEGORIES:
        return f"coalesce(e.\"{group}\",'unavailable')"
    if group not in NUMERIC:
        raise ValueError("Unsupported group field")
    edges = numeric.get(group, {}).get("edges", [])
    if not edges:
        raise ValueError("Numeric grouping requires saved or supplied bucket edges")
    validate({group: {"edges": edges}})
    # Only finite float literals enter SQL; field names are allow-listed above.
    parts = [f"WHEN e.\"{group}\" IS NULL THEN 'unavailable'"]
    for i, edge in enumerate(edges):
        lo = float(edges[i - 1]) if i else "-inf"
        parts.append(f"WHEN e.\"{group}\" < {float(edge)} THEN '[{lo}, {float(edge)})'")
    return "CASE " + " ".join(parts) + f" ELSE '[{float(edges[-1])}, inf)' END"


def summary(
    root,
    config,
    filters=None,
    numeric=None,
    group="year",
    horizon="30",
    threshold=50,
    interpretation="continuation",
    threshold_atr=None,
):
    if horizon not in (
        "5",
        "10",
        "15",
        "30",
        "60",
        "session_close",
    ) or threshold not in (10, 25, 50, 75, 100):
        raise ValueError("Unsupported outcome measurement")
    if interpretation not in ("continuation", "rejection"):
        raise ValueError("Unsupported directional interpretation")
    numeric = {**config["research_settings"]["numeric_filters"], **(numeric or {})}
    clause, args = where(filters or {}, numeric)
    expression = group_expression(group, numeric)
    positive = "UP" if interpretation == "continuation" else "DOWN"
    if threshold_atr is not None:
        allowed = config["research_settings"]["atr_thresholds"]
        if threshold_atr not in allowed:
            raise ValueError("ATR threshold must be in immutable study configuration")
        token = str(next(x for x in allowed if x == threshold_atr))
        # Validated finite config numbers only; quoted JSON path preserves the decimal point.
        up = f"CAST(json_extract(o.payload, '$.atr_thresholds.\"up_{token}\".reached') AS DOUBLE)"
        down = f"CAST(json_extract(o.payload, '$.atr_thresholds.\"down_{token}\".reached') AS DOUBLE)"
    else:
        up = f"CAST(o.up_{threshold} AS DOUBLE)"
        down = f"CAST(o.down_{threshold} AS DOUBLE)"
    # Match ordinary observations by year, confirmation half-hour, and fixed ATR bucket.
    # Each event inherits its matching stratum mean; inference then collapses to NY dates.
    cte = f"""WITH base AS (
      SELECT b.year,b.time_bucket,b.volatility_bucket,avg({up}) up,
      avg({down}) down
      FROM observations b JOIN outcomes o USING(event_id)
      WHERE o.kind='baseline' AND o.horizon=? AND o.complete
      GROUP BY b.year,b.time_bucket,b.volatility_bucket),
      selected AS (
      SELECT e.event_id,e.date,{expression} grp,o.complete,
      CASE WHEN e.direction='{positive}' THEN {up}
           WHEN e.direction IN ('UP','DOWN') THEN {down} END hit,
      CASE WHEN e.direction='{positive}' THEN b.up
           WHEN e.direction IN ('UP','DOWN') THEN b.down END baseline,
      CASE WHEN e.direction='{positive}' THEN o.maximum_high_excursion ELSE o.maximum_low_excursion END mfe,
      CASE WHEN e.direction='{positive}' THEN o.maximum_low_excursion ELSE o.maximum_high_excursion END mae,
      o.forward_close_change change
      FROM events e LEFT JOIN outcomes o ON e.event_id=o.event_id AND o.kind='event' AND o.horizon=?
      LEFT JOIN base b ON e.year=b.year AND e.time_bucket=b.time_bucket AND e.volatility_bucket=b.volatility_bucket
      WHERE {clause})"""
    parameters = [horizon, horizon, *args]
    aggregates = query(
        root,
        cte + """ SELECT grp,count(*) events,count(DISTINCT date) unique_dates,
      count(*) FILTER(WHERE complete) complete,count(*) FILTER(WHERE NOT coalesce(complete,false)) censored,
      avg(change) mean,median(change) median,stddev_samp(change) standard_deviation,
      avg(mfe) mfe,median(mfe) median_mfe,avg(mae) mae,median(mae) median_mae,
      count(*) FILTER(WHERE complete AND baseline IS NOT NULL AND hit IS NOT NULL) matched_events
      FROM selected GROUP BY grp ORDER BY grp""",
        parameters,
    )
    daily = query(
        root,
        cte + """ SELECT grp,date,avg(hit) event_value,avg(baseline) baseline_value
      FROM selected WHERE complete AND baseline IS NOT NULL AND hit IS NOT NULL
      GROUP BY grp,date ORDER BY grp,date""",
        parameters,
    )
    by_group = {}
    for d in daily:
        by_group.setdefault(d["grp"], []).append(d)
    statcfg = StatisticsConfig(**config["research_settings"]["statistics"])
    for row in aggregates:
        ds = by_group.get(row["grp"], [])
        inference = clustered(
            [d["date"] for d in ds],
            [d["event_value"] for d in ds],
            [d["baseline_value"] for d in ds],
            statcfg,
        )
        row["matched_dates"] = inference["unique_dates"]
        for k in (
            "event_probability",
            "baseline_probability",
            "effect",
            "relative_effect",
            "ci95",
            "p_value",
            "small_sample",
        ):
            row[k] = inference[k]
    for row, q in zip(
        aggregates, benjamini_hochberg([r["p_value"] for r in aggregates])
    ):
        row["q_value"] = q
    return dict(
        groups=aggregates,
        group=group,
        horizon=horizon,
        threshold_points=threshold if threshold_atr is None else None,
        threshold_atr=threshold_atr,
        interpretation=interpretation,
        methodology="Equal-weight NY-date matched probability difference; date-cluster percentile bootstrap; BH across displayed groups",
        statistics=config["research_settings"]["statistics"],
    )
