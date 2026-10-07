import { useMemo, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
} from "recharts";
import type { InputMeta } from "./api";
export const number = (n: unknown) =>
  n == null
    ? "—"
    : typeof n === "number"
      ? n.toLocaleString("en-US", { maximumFractionDigits: 3 })
      : String(n);
export const money = (n: unknown) =>
  n == null
    ? "—"
    : Number(n).toLocaleString("en-US", { style: "currency", currency: "USD" });
export function Inputs({
  inputs,
  values,
  onChange,
}: {
  inputs: InputMeta[];
  values: any;
  onChange: (v: any) => void;
}) {
  return (
    <>
      {inputs.map((i) => (
        <label key={i.id}>
          {i.label}
          {i.type === "bool" ? (
            <input
              aria-label={i.label}
              type="checkbox"
              checked={Boolean(values[i.id] ?? i.default)}
              onChange={(e) =>
                onChange({ ...values, [i.id]: e.target.checked })
              }
            />
          ) : i.type === "choice" ? (
            <select
              aria-label={i.label}
              value={String(values[i.id] ?? i.default)}
              onChange={(e) => onChange({ ...values, [i.id]: e.target.value })}
            >
              {i.choices?.map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          ) : (
            <input
              aria-label={i.label}
              type={
                ["float", "int"].includes(i.type)
                  ? "number"
                  : i.type === "time"
                    ? "time"
                    : "text"
              }
              value={String(values[i.id] ?? i.default)}
              min={i.min}
              max={i.max}
              step={i.step || "any"}
              onChange={(e) =>
                onChange({
                  ...values,
                  [i.id]: ["float", "int"].includes(i.type)
                    ? Number(e.target.value)
                    : e.target.value,
                })
              }
            />
          )}
          <small>{i.description}</small>
        </label>
      ))}
    </>
  );
}
export function Table({
  rows,
  columns,
  onRow,
}: {
  rows: any[];
  columns?: string[];
  onRow?: (r: any) => void;
}) {
  const [sort, setSort] = useState("");
  const [desc, setDesc] = useState(false);
  const keys = columns || Object.keys(rows[0] || {});
  const sorted = useMemo(
    () =>
      [...rows].sort((a, b) => {
        if (!sort) return 0;
        const x = a[sort],
          y = b[sort];
        return (
          (typeof x === "number"
            ? x - y
            : String(x ?? "").localeCompare(String(y ?? ""), undefined, {
                numeric: true,
              })) * (desc ? -1 : 1)
        );
      }),
    [rows, sort, desc],
  );
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {keys.map((k) => (
              <th key={k}>
                <button
                  onClick={() => {
                    setSort(k);
                    setDesc(sort === k ? !desc : false);
                  }}
                >
                  {k.replaceAll("_", " ")}{" "}
                  {sort === k ? (desc ? "↓" : "↑") : ""}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr
              key={row.id || row.trade_id || i}
              onClick={() => onRow?.(row)}
              className={onRow ? "clickable" : ""}
            >
              {keys.map((k) => (
                <td
                  key={k}
                  className={
                    /pnl|usd|average_r|result_r/.test(k)
                      ? Number(row[k]) < 0
                        ? "negative"
                        : "positive"
                      : ""
                  }
                >
                  {typeof row[k] === "object" && row[k] !== null
                    ? JSON.stringify(row[k])
                    : number(row[k])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {!rows.length && <p className="empty">No records for this selection.</p>}
    </div>
  );
}
export function KPIs({ m }: { m: any }) {
  return (
    <div className="kpis">
      {[
        ["Net P&L", money(m?.net_pnl_usd)],
        ["Profit factor", number(m?.profit_factor)],
        ["Average R", number(m?.average_r)],
        [
          "Win rate",
          m?.win_rate_percent != null ? number(m.win_rate_percent) + "%" : "—",
        ],
        ["Trades", number(m?.trades)],
        ["Max drawdown", money(m?.max_closed_trade_drawdown_usd)],
      ].map(([k, v]) => (
        <div key={k}>
          <span>{k}</span>
          <strong>{v}</strong>
        </div>
      ))}
    </div>
  );
}
const colors = ["#4ad6b5", "#789bff", "#edb76b", "#c98bf4", "#ee7e89"];
export function Curve({
  rows,
  series = ["cumulative_net_pnl_usd"],
  x = "exit_time_utc",
  labels = {},
}: {
  rows: any[];
  series?: string[];
  x?: string;
  labels?: Record<string,string>;
}) {
  if (!rows.length)
    return <p className="empty">No closed trades to chart for this run.</p>;
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows}>
          <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
          <XAxis
            dataKey={x}
            tickFormatter={(x) => String(x).slice(0, 10)}
            minTickGap={60}
          />
          <YAxis width={65} />
          <Tooltip
            contentStyle={{
              background: "#182230",
              border: "1px solid #334155",
            }}
          />
          <Legend />
          {series.map((s, i) => (
            <Line
              key={s}
              name={labels[s] || s.replaceAll("_", " ")}
              type="stepAfter"
              dataKey={s}
              stroke={colors[i % colors.length]}
              dot={false}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
export function Bars({
  rows,
  x = "group",
  y = "net_pnl_usd",
}: {
  rows: any[];
  x?: string;
  y?: string;
}) {
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows}>
          <CartesianGrid stroke="#263241" />
          <XAxis dataKey={x} />
          <YAxis />
          <Tooltip contentStyle={{ background: "#182230" }} />
          <Bar dataKey={y} fill="#4ad6b5" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
