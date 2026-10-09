import { useEffect, useRef, useState } from "react";
import {
  createChart,
  CandlestickSeries,
  ColorType,
  type UTCTimestamp,
} from "lightweight-charts";
import { api } from "./api";
import { Table, money, number } from "./components";
const ny = (t: string | number) =>
  new Date(typeof t === "number" ? t * 1000 : t).toLocaleString("en-US", {
    timeZone: "America/New_York",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
export function annotationX(
  time: string,
  candles: { time: number }[],
  coordinate: (n: number) => number | null,
  finalStep = 300,
) {
  const at = Date.parse(time) / 1000;
  let right = candles.findIndex((c) => c.time > at);
  if (right < 0) right = candles.length;
  const left = Math.max(0, right - 1),
    x1 = coordinate(left) ?? 0,
    x2 = coordinate(left + 1) ?? x1;
  const step = candles[left + 1]
    ? candles[left + 1].time - candles[left].time
    : finalStep;
  return x1 + ((x2 - x1) * (at - candles[left].time)) / step;
}
export function CandleChart({ data }: { data: any }) {
  const host = useRef<HTMLDivElement>(null),
    overlay = useRef<SVGSVGElement>(null);
  useEffect(() => {
    if (!host.current || !data.candles.length) return;
    const chart = createChart(host.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#101a25" },
        textColor: "#aabbd0",
      },
      grid: {
        vertLines: { color: "#202e3e" },
        horzLines: { color: "#202e3e" },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        rightOffset: data.right_offset ?? 0,
        tickMarkFormatter: (t: any) => ny(Number(t)),
      },
      localization: { timeFormatter: (t: any) => ny(Number(t)) },
      rightPriceScale: { scaleMargins: { top: 0.12, bottom: 0.12 } },
    });
    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#4ad6b5",
      downColor: "#ed7186",
      borderVisible: false,
      wickUpColor: "#4ad6b5",
      wickDownColor: "#ed7186",
      autoscaleInfoProvider: (base: any) => {
        const info = base();
        const levels = data.annotations.flatMap((a: any) =>
          [a.price, a.price_low, a.price_high]
            .filter((v) => v != null)
            .map(Number),
        );
        return info
          ? {
              ...info,
              priceRange: {
                minValue: Math.min(info.priceRange.minValue, ...levels),
                maxValue: Math.max(info.priceRange.maxValue, ...levels),
              },
            }
          : null;
      },
    });
    const candles = data.candles.map((c: any) => ({
      time: (Date.parse(c.timestamp_utc) / 1000) as UTCTimestamp,
      open: Number(c.open),
      high: Number(c.high),
      low: Number(c.low),
      close: Number(c.close),
    }));
    series.setData(candles);
    chart.timeScale().fitContent();
    let frame = 0;
    function draw() {
      const svg = overlay.current;
      if (!svg) return;
      svg.replaceChildren();
      const x = (time: string) =>
        annotationX(
          time,
          candles,
          (n) => chart.timeScale().logicalToCoordinate(n as any),
          data.bar_seconds ?? 300,
        );
      const y = (price: any) => series.priceToCoordinate(Number(price)) ?? 0;
      const node = (type: string, attrs: any, label?: string) => {
        const e = document.createElementNS("http://www.w3.org/2000/svg", type);
        Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, String(v)));
        if (label) e.textContent = label;
        svg.appendChild(e);
      };
      let markerRow = 0;
      for (const a of data.annotations) {
        const color =
          a.category === "stop"
            ? "#ed7186"
            : a.category === "management"
              ? "#edb76b"
              : a.category === "target"
                ? "#789bff"
                : "#4ad6b5";
        const x1 = x(a.start_time),
          x2 = a.end_time ? x(a.end_time) : x1,
          py = y(a.price);
        if (a.type === "box")
          node("rect", {
            x: x1,
            y: y(a.price_high),
            width: Math.max(0, x2 - x1),
            height: Math.max(0, y(a.price_low) - y(a.price_high)),
            fill: "#4ad6b51f",
            stroke: "#4ad6b566",
          });
        else if (a.type === "horizontal_line")
          node("line", {
            x1,
            y1: py,
            x2,
            y2: py,
            stroke: color,
            "stroke-width": a.category === "management" ? 3 : 1.5,
            "stroke-dasharray": a.category === "management" ? "" : "5 4",
          });
        else if (a.type === "vertical_marker")
          node("line", {
            x1,
            y1: 0,
            x2: x1,
            y2: host.current!.clientHeight,
            stroke: color,
            "stroke-dasharray": "4 4",
          });
        else if (a.type === "point_marker")
          node("circle", { cx: x1, cy: py, r: 5, fill: color });
        node(
          "text",
          {
            x: x1 + 5,
            y:
              a.type === "vertical_marker"
                ? 18 + markerRow++ * 16
                : a.type === "box"
                  ? y(a.price_high) - 5
                  : a.type === "point_marker"
                    ? py + 16
                    : py - 7,
            fill: color,
            "font-size": 11,
          },
          a.label,
        );
      }
      frame = requestAnimationFrame(draw);
    }
    draw();
    return () => {
      cancelAnimationFrame(frame);
      chart.remove();
    };
  }, [data]);
  return (
    <div className="candle-shell">
      <div ref={host} className="candle-chart" />
      <svg ref={overlay} className="candle-overlay" aria-hidden="true" />
    </div>
  );
}
export default function TradeInspector({
  runId,
  tradeId,
  onNavigate,
  onBack,
}: {
  runId: string;
  tradeId: string;
  onNavigate: (id: string) => void;
  onBack: () => void;
}) {
  const [window, setWindow] = useState("30"),
    [data, setData] = useState<any>(null),
    [error, setError] = useState("");
  useEffect(() => {
    let alive = true;
    setError("");
    setData(null);
    api(`/backtests/${runId}/trades/${tradeId}/chart?window=${window}`)
      .then((d) => {
        if (alive) setData(d);
      })
      .catch((e) => {
        if (alive) setError(e.message);
      });
    return () => {
      alive = false;
    };
  }, [runId, tradeId, window]);
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (
        e.target instanceof HTMLElement &&
        e.target.matches("input,textarea,select")
      )
        return;
      if (e.key === "ArrowLeft" && data?.previous_trade_id)
        onNavigate(data.previous_trade_id);
      if (e.key === "ArrowRight" && data?.next_trade_id)
        onNavigate(data.next_trade_id);
    };
    globalThis.addEventListener("keydown", handler);
    return () => globalThis.removeEventListener("keydown", handler);
  }, [data, onNavigate]);
  const t = data?.trade;
  return (
    <section className="inspector">
      <div className="toolbar">
        <button onClick={onBack}>Back to Trades</button>
        <button
          disabled={!data?.previous_trade_id}
          onClick={() => onNavigate(data.previous_trade_id)}
        >
          Previous Trade
        </button>
        <button
          disabled={!data?.next_trade_id}
          onClick={() => onNavigate(data.next_trade_id)}
        >
          Next Trade
        </button>
        {[
          ["30", "30 min before"],
          ["60", "1 hour before"],
          ["session", "Full session"],
        ].map(([v, label]) => (
          <button
            key={v}
            className={window === v ? "active" : ""}
            onClick={() => setWindow(v)}
          >
            {label}
          </button>
        ))}
      </div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {t ? (
        <>
          <h2>
            {data.run.strategy_name} · {data.run.variant || data.run.name}
          </h2>
          <p>
            {data.run.name} · Trade {data.trade_number}/{data.trade_count} ·{" "}
            {t.direction} · {ny(t.entry_time_utc)} → {ny(t.exit_time_utc)} ET ·{" "}
            {money(t.net_pnl_usd)} · {number(t.result_r)}R
          </p>
          <CandleChart data={data} />
          <small>
            Candles: actual 5m bar starts. Labels: America/New_York. Exit
            markers use recorded minute-end confirmation; extrema order within a
            minute is unknown. Charting by{" "}
            <a
              href="https://www.tradingview.com/"
              target="_blank"
              rel="noreferrer"
            >
              TradingView Lightweight Charts
            </a>
            .
          </small>
          <div className="inspection-details">
            <Table
              rows={[
                "entry_price",
                "stop_price",
                "target_price",
                "exit_price",
                "risk_points",
                "mfe_points",
                "mae_points",
                "mfe_r",
                "mae_r",
                "duration_minutes",
                "exit_reason",
              ].map((k) => ({ field: k, value: t[k] }))}
            />
            <div>
              <h3>Management events</h3>
              <Table rows={data.management_events} />
              {t.partial_execution_history && (
                <>
                  <h3>Partial execution history</h3>
                  <Table rows={t.partial_execution_history} />
                </>
              )}
              <h3>Strategy metadata</h3>
              <pre>{JSON.stringify(t.metadata || {}, null, 2)}</pre>
            </div>
          </div>
        </>
      ) : (
        !error && <p>Loading source candles…</p>
      )}
    </section>
  );
}
