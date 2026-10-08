# Candlestick Trade Inspector

Open a completed run → Inspect trades → click a row. A large Inspector panel opens.
Back to Trades preserves filters; Previous/Next and left/right arrows navigate the run's
chronological trade order (not the filtered subset). Input fields do not intercept arrows.

Choose 30 minutes before, one hour before, or Full session. All windows include the
trade through exit plus available context. Full session means the NY **calendar date**,
not a newly invented CME session label. Only existing five-minute candles are returned;
UTC timestamps remain original, while chart labels use America/New_York, including DST.
Incomplete source candles remain visible for inspection; they do not become signal events.

Lightweight Charts 5.2.0 renders OHLC. A generic SVG annotation layer tracks chart coordinates
on pan/zoom/resize. Fractional-minute event locations interpolate between integer candle
coordinates, so stop activation is not shifted to the preceding candle start. Annotations
are clipped to the price pane. Autoscaling includes annotated stop/target/FVG levels.
Attribution is retained. Library API reference:
https://tradingview.github.io/lightweight-charts/docs/5.0

`GET /api/backtests/{run_id}/trades/{trade_id}/chart?window=30|60|session`
returns trade/run identity, required candles, annotations, management events, session/data
bounds and previous/next trade IDs. The old `/candles/{trade_id}` endpoint remains compatible.
Parquet time predicates restrict reads; the browser never receives the minute dataset.

Annotations: box, horizontal_line, vertical_marker, point_marker, label. Common fields:
start_time/end_time (timezone-aware), price or price_low/price_high, label, category and
metadata. FVG is an optional box category. Entry metadata may contain an `annotations` list.
No renderer depends on CONT-A. Price strings become numbers only for visualization.

Original entry/stop/target, exit price/reason and optional FVG are drawn. Managed segments
start at recorded **activation** timestamps. The detail panel retains original risk, MFE,
MAE, duration and metadata. Original stop remains a labeled reference; amber segments show
active managed stops. Extrema remain the same OHLC bounds used by the engine; the chart does
not infer an intraminute path. Exit markers use the saved minute-end confirmation label.
