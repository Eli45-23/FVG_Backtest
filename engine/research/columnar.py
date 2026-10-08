"""Append-only Parquet artifacts; parameterized DuckDB filtering/aggregation."""

import json
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb
from engine.canonical import dumps
from engine.research.numeric import NUMERIC, CATEGORIES

EVENT_SCHEMA = pa.schema(
    [
        (k, pa.string())
        for k in [
            "event_id",
            "timestamp_utc",
            "date",
            "session_close",
            "volatility_bucket",
            "payload",
        ]
    ]
    + [(k, pa.string()) for k in CATEGORIES if k != "volatility_bucket"]
    + [(k, pa.float64()) for k in ["price_at_event", *NUMERIC]]
)


class Writer:
    def __init__(self, path, schema=EVENT_SCHEMA):
        if path.exists():
            raise ValueError("Immutable artifact already exists")
        self.writer = pq.ParquetWriter(path, schema, compression="zstd")
        self.schema = schema
        self.buffer = []

    def add(self, event):
        if self.schema == EVENT_SCHEMA:
            row = {
                k: (None if event.get(k) is None else str(event[k]))
                for k in self.schema.names
                if k not in NUMERIC and k != "price_at_event"
            }
            row.update(
                {
                    k: float(event[k]) if event.get(k) is not None else None
                    for k in ["price_at_event", *NUMERIC]
                }
            )
            row["payload"] = dumps(event)
        else:
            row = event
        self.buffer.append(row)
        if len(self.buffer) >= 2048:
            self.flush()

    def flush(self):
        if self.buffer:
            self.writer.write_table(
                pa.Table.from_pylist(self.buffer, schema=self.schema)
            )
            self.buffer = []

    def close(self):
        self.flush()
        self.writer.close()


OUTCOME_SCHEMA = pa.schema(
    [
        ("event_id", pa.string()),
        ("kind", pa.string()),
        ("horizon", pa.string()),
        ("complete", pa.bool_()),
        ("censor_reason", pa.string()),
    ]
    + [
        (k, pa.float64())
        for k in [
            "forward_close_change",
            "maximum_high_excursion",
            "maximum_low_excursion",
            "mfe",
            "mae",
            "forward_close_change_atr",
            "mfe_atr",
            "mae_atr",
        ]
    ]
    + [
        (f"{side}_{n}", pa.bool_())
        for side in ["up", "down"]
        for n in [10, 25, 50, 75, 100]
    ]
    + [("payload", pa.string())]
)


def query(root, sql, parameters=()):
    with duckdb.connect() as con:
        con.execute("SET memory_limit='512MB'")
        con.execute("SET threads=2")
        # Paths originate from server-created immutable study IDs, never query text input.
        for table, file in [
            ("events", "v2_events.parquet"),
            ("observations", "v2_observations.parquet"),
            ("outcomes", "v2_outcomes.parquet"),
        ]:
            p = root / file
            if p.exists():
                con.read_parquet(str(p)).create_view(table)
        cursor = con.execute(sql, parameters)
        names = [x[0] for x in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]


def predicate(filters, alias="e"):
    clauses = []
    args = []
    for key, value in filters.items():
        if value in ("", None):
            continue
        if key not in CATEGORIES:
            raise ValueError("Unsupported event filter")
        if key == "touch_number" and value == "3+":
            clauses.append(f'TRY_CAST({alias}."touch_number" AS DOUBLE)>=3')
        else:
            clauses.append(f'{alias}."{key}"=?')
            args.append(str(value))
    return (" AND ".join(clauses) or "TRUE"), args


def export_rows(root, kind):
    """Stream stable artifact-order batches without materializing the result set."""
    file = {
        "events": "v2_events.parquet",
        "outcomes": "v2_outcomes.parquet",
        "observations": "v2_observations.parquet",
    }[kind]
    for batch in pq.ParquetFile(root / file).iter_batches(
        batch_size=1024, columns=["payload"]
    ):
        yield from batch.column(0).to_pylist()
