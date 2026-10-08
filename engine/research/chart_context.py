"""Persisted causal feature overlays. No recomputation from future chart bars."""


def annotations(event, start, end):
    import pandas as pd

    result = []
    at = event["timestamp_utc"]
    context = event.get("chart_context", {})
    for level in context.get("levels", []):
        category = (
            "4h levels"
            if level["type"].startswith("4h")
            else "swings" if "SWING" in level["type"] else "session levels"
        )
        result.append(
            dict(
                type="horizontal_line",
                price=float(level["price"]),
                start_time=str(max(start, pd.Timestamp(level["available_at"]))),
                end_time=str(end),
                label=level["type"],
                category=category,
            )
        )
    for zone in context.get("zones", []):
        result.append(
            dict(
                type="box",
                price_low=zone["bottom"],
                price_high=zone["top"],
                start_time=str(
                    max(start, pd.Timestamp(zone["availability_timestamp"]))
                ),
                end_time=str(end),
                label=zone["zone_type"],
                category="zones",
            )
        )
    for key, value in context.get("indicators", {}).items():
        if value is not None:
            result.append(
                dict(
                    type="horizontal_line",
                    price=value,
                    start_time=at,
                    end_time=str(end),
                    label=key + " at confirmation",
                    category="indicators",
                )
            )
    for key in ("break_confirmation_timestamp", "confirmation_timestamp"):
        if event.get(key):
            result.append(
                dict(
                    type="vertical_marker",
                    start_time=event[key],
                    label=key.replace("_", " "),
                    category="sequence",
                )
            )
    return result
