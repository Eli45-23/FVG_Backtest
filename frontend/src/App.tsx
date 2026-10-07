import TradeInspector from "./TradeInspector";
import { useState, useEffect, useRef } from "react";
import Editor, { loader } from "@monaco-editor/react";
import * as monaco from "monaco-editor";
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
import {
  Activity,
  Code2,
  Play,
  History,
  Columns3,
  SlidersHorizontal,
  Table2,
  Search,
  Database,
  Settings,
  FlaskConical,
} from "lucide-react";
import { api, type Strategy, type Run, type InputMeta } from "./api";
import { Inputs, Table, KPIs, Curve, Bars, money } from "./components";
(self as any).MonacoEnvironment = { getWorker: () => new EditorWorker() };
loader.config({ monaco });
const nav = [
  ["Dashboard", Activity],
  ["Strategies", Code2],
  ["Backtest", Play],
  ["Runs", History],
  ["Compare", Columns3],
  ["Sweeps", SlidersHorizontal],
  ["Trades", Table2],
  ["Research", Search],
  ["Data", Database],
  ["Settings", Settings],
] as const;
const initialSettings = {
  start: "2024-01-01",
  end: "2026-10-06",
  quantity: 1,
  commission: "0",
  slippage: 0,
  instrument: "MNQ",
  timeframe: "5m",
};
export default function App() {
  const [inspectedTrade, setInspectedTrade] = useState("");
  const [page, setPage] = useState("Dashboard"),
    [strategies, setStrategies] = useState<Strategy[]>([]),
    [selected, setSelected] = useState<Strategy | null>(null),
    [source, setSource] = useState(""),
    [name, setName] = useState(""),
    [inputs, setInputs] = useState<InputMeta[]>([]),
    [params, setParams] = useState<any>({}),
    [settings, setSettings] = useState(initialSettings),
    [runs, setRuns] = useState<Run[]>([]),
    [active, setActive] = useState(""),
    [variants, setVariants] = useState<any[]>([]),
    [variantId, setVariantId] = useState(""),
    [notes, setNotes] = useState(""),
    [segment, setSegment] = useState("development"),
    [log, setLog] = useState("Ready. Only run strategy code you trust."),
    [error, setError] = useState(""),
    [query, setQuery] = useState(""),
    [compareIds, setCompareIds] = useState<string[]>([]),
    [comparison, setComparison] = useState<any>(null),
    [compareMode, setCompareMode] = useState("Equity"),
    [workerLog, setWorkerLog] = useState(""),
    [data, setData] = useState<any>(null),
    [sweeps, setSweeps] = useState<any[]>([]),
    [sweepKey, setSweepKey] = useState("max_risk"),
    [sweepValues, setSweepValues] = useState("75,100"),
    [resultTab, setResultTab] = useState("Equity"),
    [equity, setEquity] = useState<any[]>([]),
    [trades, setTrades] = useState<any[]>([]),
    [filters, setFilters] = useState<any>({}),
    [research, setResearch] = useState<any>(null),
    [researchFilters, setResearchFilters] = useState<any>({});
  const editor = useRef<any>(null);
  const dirty =
    !!selected && (source !== selected.source || name !== selected.name);
  const current = runs.find((r) => r.id === active);
  const guard = async (fn: () => Promise<any>) => {
    setError("");
    try {
      return await fn();
    } catch (e) {
      setError((e as Error).message);
      return null;
    }
  };
  async function refresh() {
    const [s, r, v, sw] = await Promise.all([
      api("/strategies"),
      api("/backtests"),
      api("/variants"),
      api("/sweeps"),
    ]);
    setStrategies(s);
    setRuns(r);
    setVariants(v);
    setSweeps(sw);
    return s as Strategy[];
  }
  useEffect(() => {
    void guard(async () => {
      await refresh();
      setData(await api("/data"));
    });
  }, []);
  useEffect(() => {
    const timer = setInterval(() => {
      void guard(async () => {
        setRuns(await api("/backtests"));
        if (page === "Sweeps") setSweeps(await api("/sweeps"));
      });
    }, 2500);
    return () => clearInterval(timer);
  }, [page]);
  useEffect(() => {
    if (current?.status === "completed")
      void guard(async () => {
        setEquity(await api(`/backtests/${active}/equity`));
        setTrades(await api(`/backtests/${active}/trades`));
      });
    else {
      setEquity([]);
      setTrades([]);
    }
  }, [active, current?.status]);
  async function check(code = source) {
    setLog("Validating in isolated worker…");
    const result = await api("/strategies/validate", { source: code });
    if (result.valid) {
      setInputs(result.inputs);
      setLog("Validation passed. " + result.warnings.join(" "));
    } else setLog("Validation failed: " + result.error);
    if (editor.current) {
      monaco.editor.setModelMarkers(
        editor.current.getModel(),
        "strategy",
        result.valid
          ? []
          : [
              {
                severity: monaco.MarkerSeverity.Error,
                message: result.error,
                startLineNumber: result.line || 1,
                endLineNumber: result.line || 1,
                startColumn: 1,
                endColumn: 80,
              },
            ],
      );
    }
    return result;
  }
  async function open(s: Strategy) {
    if (dirty && !confirm("Discard unsaved edits?")) return;
    setSelected(s);
    setSource(s.source);
    setName(s.name);
    setParams({});
    setVariantId("");
    setPage("Strategies");
    await check(s.source);
  }
  async function save() {
    if (!selected) return null;
    const s = await api(
      "/strategies/" + selected.id,
      { name, source, description: selected.description, tags: selected.tags },
      "PUT",
    );
    setSelected(s);
    await refresh();
    setLog("Saved immutable version " + s.current_version);
    return s;
  }
  async function create(clone = false) {
    const nextName = prompt(
      clone ? "Clone name" : "Strategy name",
      clone ? name + " copy" : "My Strategy",
    );
    if (!nextName) return;
    const code = clone ? source : (await api("/template")).source;
    const s = await api("/strategies", { name: nextName, source: code });
    setSelected(null);
    await open(s);
    await refresh();
  }
  async function runNow() {
    const s = dirty ? await save() : selected;
    if (!s) return;
    const result = await api("/backtests", {
      strategy_version_id: s.version_id,
      name: name + " run",
      parameters: params,
      settings,
      notes,
      segment,
      variant_id: dirty ? null : variantId || null,
    });
    setActive(result.id);
    await refresh();
    setPage("Backtest");
  }
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        void guard(save);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selected, source, name]);
  async function useVariant(id: string) {
    setVariantId(id);
    const v = variants.find((x) => x.id === id);
    if (!v || !selected) return;
    const versions = await api(`/strategies/${selected.id}/versions`);
    const version = versions.find((x: any) => x.id === v.strategy_version_id);
    if (!version) return;
    setSelected({
      ...selected,
      source: version.source,
      version_id: version.id,
      current_version: version.number,
    });
    setSource(version.source);
    setParams(v.parameters);
    setSettings({ ...initialSettings, ...v.config });
    await check(version.source);
  }
  const submitBody = () => ({
    strategy_version_id: selected?.version_id,
    name: name + " sweep",
    parameters: params,
    settings,
    notes,
    segment,
  });
  async function startSweep() {
    const s = dirty ? await save() : selected;
    if (!s) return;
    const meta = inputs.find((i) => i.id === sweepKey);
    const values = sweepValues
      .split(",")
      .map((v) => (meta?.type === "choice" ? v.trim() : Number(v.trim())));
    await api("/sweeps", {
      name: name + " · " + sweepKey,
      parameter: sweepKey,
      values,
      run: { ...submitBody(), strategy_version_id: s.version_id },
    });
    await refresh();
  }
  async function compare() {
    setComparison(await api("/compare", { ids: compareIds }));
    setPage("Compare");
  }
  const grouped = (key: string) =>
    Object.entries(current?.metrics?.[key] || {}).map(([group, value]) => ({
      group,
      ...(value as object),
    }));
  const metricsKeys = [
    "trades",
    "win_rate_percent",
    "net_pnl_usd",
    "profit_factor",
    "average_r",
    "max_closed_trade_drawdown_usd",
  ];
  const tradeRows = trades
    .filter((t) =>
      Object.entries(filters).every(
        ([k, v]) =>
          !v ||
          (k === "outcome"
            ? v === "winner"
              ? Number(t.net_pnl_usd) > 0
              : Number(t.net_pnl_usd) < 0
            : k === "risk_min"
              ? Number(t.risk_points) >= Number(v)
              : k === "risk_max"
                ? Number(t.risk_points) < Number(v)
                : k === "start"
                  ? t.entry_time_ny.slice(0, 10) >= v
                  : k === "end"
                    ? t.entry_time_ny.slice(0, 10) < v
                    : k === "time_from"
                      ? t.entry_time_ny.slice(11, 16) >= v
                      : k === "time_to"
                        ? t.entry_time_ny.slice(11, 16) < v
                        : String(t[k]) === String(v)),
      ),
    )
    .map((t) => ({
      ...t,
      Date: t.entry_time_ny.slice(0, 10),
      Time: t.entry_time_ny.slice(11, 16),
      risk_points: Number(t.risk_points),
      net_pnl_usd: Number(t.net_pnl_usd),
    }));
  const compareCurve = () => {
    if (!comparison) return [];
    const times = [
      ...new Set<string>(
        Object.values(comparison.equity).flatMap((a: any) =>
          a.map((p: any) => p.exit_time_utc),
        ),
      ),
    ].sort();
    const values: any = {};
    return times.map((time) => {
      for (const r of comparison.runs) {
        const point = comparison.equity[r.id].find(
          (p: any) => p.exit_time_utc === time,
        );
        if (point)
          values[r.id] =
            compareMode === "Drawdown"
              ? point.drawdown_usd
              : point.cumulative_net_pnl_usd;
      }
      return {
        exit_time_utc: time,
        ...Object.fromEntries(
          comparison.runs.map((r: any) => [r.id, values[r.id] || 0]),
        ),
      };
    });
  };
  return (
    <div className="app">
      <aside className="nav">
        <div className="brand">
          <FlaskConical size={25} />
          <div>
            STRATEGY<span>RESEARCH LAB</span>
          </div>
        </div>
        <div className="local">
          <i /> LOCAL WORKSPACE
        </div>
        {nav.map(([label, Icon]) => (
          <button
            className={page === label ? "active" : ""}
            key={label}
            onClick={() => setPage(label)}
          >
            <Icon size={17} />
            {label}
          </button>
        ))}
        <footer>
          MNQ · 5 MINUTE
          <br />
          Validated minute execution
          <br />
          <span>Research, not live trading</span>
        </footer>
      </aside>
      <main>
        <header>
          <div>
            <small>WORKSPACE / {page.toUpperCase()}</small>
            <h1>{page}</h1>
          </div>
          <div className="header-info">
            MNQ.v.0 <span>LOCAL PARQUET</span>
            <span className="status">● ENGINE READY</span>
          </div>
        </header>
        {error && (
          <div role="alert" className="error">
            {error}
            <button onClick={() => setError("")}>Dismiss</button>
          </div>
        )}
        {page === "Dashboard" && (
          <>
            <div className="hero">
              <h2>
                Controlled experiments.
                <br />
                <span>Traceable results.</span>
              </h2>
              <p>
                Write a strategy, preserve its source, and test one idea at a
                time.
              </p>
              <button
                className="primary"
                onClick={() => void guard(() => create())}
              >
                New strategy
              </button>
              <button onClick={() => setPage("Strategies")}>
                Open library
              </button>
              <button onClick={() => setPage("Compare")}>Compare runs</button>
            </div>
            <KPIs
              m={runs.find((r) => r.status === "completed")?.metrics?.overall}
            />
            <div className="panel">
              <h2>
                Recent runs{" "}
                <small>Latest completed metrics above · no ranking</small>
              </h2>
              <Table
                rows={runs.slice(0, 8).map((r) => ({
                  id: r.id,
                  name: r.name,
                  status: r.status,
                  created_at: r.created_at,
                  net_pnl_usd: r.metrics?.overall.net_pnl_usd,
                }))}
                columns={["name", "status", "created_at", "net_pnl_usd"]}
                onRow={(r) => {
                  setActive(r.id);
                  setPage("Backtest");
                }}
              />
            </div>
            <div className="panel">
              <h2>Strategy library</h2>
              <div className="cards">
                {strategies.slice(0, 6).map((s) => (
                  <button key={s.id} onClick={() => void guard(() => open(s))}>
                    <Code2 size={18} />
                    {s.name}
                    <small>Version {s.current_version}</small>
                  </button>
                ))}
              </div>
              <p>
                Data range: {data?.start || "Loading"} →{" "}
                {data?.end || "Loading"} · end exclusive
              </p>
            </div>
          </>
        )}
        {page === "Strategies" && (
          <div className="editor-layout">
            <section className="library">
              <h3>LIBRARY</h3>
              <input
                placeholder="Search strategies"
                aria-label="Search strategies"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button onClick={() => void guard(() => create())}>
                + New Strategy
              </button>
              {strategies
                .filter((s) =>
                  s.name.toLowerCase().includes(query.toLowerCase()),
                )
                .map((s) => (
                  <button
                    className={selected?.id === s.id ? "selected" : ""}
                    key={s.id}
                    onClick={() => void guard(() => open(s))}
                  >
                    {s.name}
                    <small>v{s.current_version}</small>
                  </button>
                ))}
            </section>
            <section className="editor">
              <div className="toolbar">
                <input
                  aria-label="Strategy name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
                <span>{dirty ? "● Unsaved" : "Saved"}</span>
                <button disabled={!selected} onClick={() => void guard(save)}>
                  Save
                </button>
                <button
                  disabled={!selected}
                  onClick={() => void guard(() => create(true))}
                >
                  Clone
                </button>
                <button
                  disabled={!selected}
                  onClick={() => void guard(() => check())}
                >
                  Validate
                </button>
                <button
                  disabled={!selected}
                  className="primary"
                  onClick={() => void guard(runNow)}
                >
                  Run Backtest
                </button>
              </div>
              <Editor
                height="570px"
                language="python"
                theme="vs-dark"
                value={source}
                onChange={(v) => setSource(v || "")}
                onMount={(e) => (editor.current = e)}
                options={{
                  fontSize: 13,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  padding: { top: 16 },
                  wordWrap: "on",
                }}
              />
              <div className="console" role="status">
                <strong>VALIDATION / LOG</strong>
                <pre>{log}</pre>
              </div>
              <div className="toolbar">
                <button
                  disabled={!selected}
                  onClick={() =>
                    void guard(async () => {
                      if (
                        confirm(
                          "Archive this strategy? Historical runs remain available.",
                        )
                      ) {
                        await api(
                          "/strategies/" + selected?.id,
                          undefined,
                          "DELETE",
                        );
                        setSelected(null);
                        setSource("");
                        await refresh();
                      }
                    })
                  }
                >
                  Archive strategy
                </button>
                <button
                  disabled={!selected}
                  onClick={() =>
                    void guard(async () => {
                      const n = prompt("Saved variant name", "New variant");
                      if (n) {
                        const s = dirty ? await save() : selected;
                        await api("/variants", {
                          strategy_version_id: s.version_id,
                          name: n,
                          parameters: params,
                          config: settings,
                          notes,
                        });
                        await refresh();
                      }
                    })
                  }
                >
                  Save / Clone Variant
                </button>
              </div>
            </section>
            <section className="inputs">
              <h3>STRATEGY INPUTS</h3>
              <label>
                Saved variant
                <select
                  aria-label="Saved variant"
                  value={variantId}
                  onChange={(e) => void guard(() => useVariant(e.target.value))}
                >
                  <option value="">Custom configuration</option>
                  {variants
                    .filter(
                      (v) => v.strategy_version_id === selected?.version_id,
                    )
                    .map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name}
                      </option>
                    ))}
                </select>
              </label>
              <Inputs inputs={inputs} values={params} onChange={setParams} />
              <h3>BACKTEST SETTINGS</h3>
              {(["start", "end"] as const).map((k) => (
                <label key={k}>
                  {k === "start" ? "Start date" : "End date (exclusive)"}
                  <input
                    aria-label={k + " date"}
                    type="date"
                    min={data?.start}
                    max={data?.end}
                    value={settings[k]}
                    onChange={(e) =>
                      setSettings({ ...settings, [k]: e.target.value })
                    }
                  />
                </label>
              ))}
              <p className="muted">
                MNQ · 5m · Full XNYS sessions
                <br />
                One actual trade per NY date
              </p>
              {(["quantity", "commission", "slippage"] as const).map((k) => (
                <label key={k}>
                  {k}
                  <input
                    aria-label={k}
                    type="number"
                    min={k === "quantity" ? 1 : 0}
                    step={k === "commission" ? ".01" : 1}
                    value={settings[k]}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        [k]:
                          k === "commission"
                            ? e.target.value
                            : Number(e.target.value),
                      })
                    }
                  />
                </label>
              ))}
              <label>
                Research segment
                <select
                  value={segment}
                  onChange={(e) => setSegment(e.target.value)}
                >
                  <option>development</option>
                  <option>validation</option>
                  <option>out-of-sample</option>
                </select>
              </label>
              <label>
                Run notes
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Hypothesis and the one change being tested"
                />
              </label>
              <small>
                Inputs create run configurations; they do not rewrite source.
              </small>
            </section>
          </div>
        )}
        {page === "Backtest" && (
          <>
            <div className="toolbar">
              <select
                aria-label="Selected run"
                value={active}
                onChange={(e) => setActive(e.target.value)}
              >
                <option value="">Select a run</option>
                {runs.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} · {r.status}
                  </option>
                ))}
              </select>
              {current && (
                <>
                  <span className="badge">{current.status}</span>
                  <span>{current.progress}</span>
                  {["queued", "running"].includes(current.status) && (
                    <button
                      onClick={() =>
                        void guard(async () => {
                          await api(`/backtests/${active}/cancel`, {});
                          await refresh();
                        })
                      }
                    >
                      Cancel Run
                    </button>
                  )}
                  <button onClick={() => setPage("Trades")}>
                    Inspect trades
                  </button>
                </>
              )}
            </div>
            {current?.error && <div className="error">{current.error}</div>}
            {current && (
              <details>
                <summary
                  onClick={() =>
                    void guard(async () =>
                      setWorkerLog(
                        (await api(`/backtests/${active}/logs`)).text,
                      ),
                    )
                  }
                >
                  Local worker log
                </summary>
                <pre>{workerLog || "No strategy output."}</pre>
              </details>
            )}
            <KPIs m={current?.metrics?.overall} />
            {current?.status === "completed" ? (
              <>
                <div className="tabs">
                  {[
                    "Equity",
                    "Drawdown",
                    "Monthly",
                    "Yearly",
                    "Direction",
                    "Time of day",
                    "Weekday",
                    "Risk",
                    "R distribution",
                    "MFE / MAE",
                    "Duration",
                    "All metrics",
                    "Configuration",
                  ].map((t) => (
                    <button
                      className={resultTab === t ? "active" : ""}
                      key={t}
                      onClick={() => setResultTab(t)}
                    >
                      {t}
                    </button>
                  ))}
                </div>
                <section className="panel">
                  {resultTab === "Equity" ? (
                    <Curve rows={equity} />
                  ) : resultTab === "Drawdown" ? (
                    <Curve rows={equity} series={["drawdown_usd"]} />
                  ) : resultTab === "Configuration" ? (
                    <pre>{JSON.stringify(current.config, null, 2)}</pre>
                  ) : resultTab === "All metrics" ? (
                    <Table
                      rows={Object.entries(current.metrics.overall).map(
                        ([metric, value]) => ({ metric, value }),
                      )}
                    />
                  ) : resultTab === "MFE / MAE" ? (
                    <Table
                      rows={Object.entries(current.metrics.excursions).map(
                        ([metric, value]) => ({ metric, value }),
                      )}
                    />
                  ) : ["R distribution", "Duration"].includes(resultTab) ? (
                    <>
                      <Bars
                        rows={Object.entries(
                          trades.reduce((acc: any, t: any) => {
                            const key =
                              resultTab === "Duration"
                                ? Math.floor(t.duration_minutes / 30) * 30
                                : Math.floor(t.result_r * 2) / 2;
                            acc[key] = (acc[key] || 0) + 1;
                            return acc;
                          }, {}),
                        ).map(([group, count]) => ({ group, count }))}
                        y="count"
                      />
                    </>
                  ) : (
                    <>
                      <Bars
                        rows={grouped(
                          (
                            {
                              Monthly: "monthly",
                              Yearly: "yearly",
                              Direction: "direction",
                              "Time of day": "trigger_time_bins",
                              Weekday: "weekday",
                              Risk: "risk_buckets_left_inclusive",
                            } as any
                          )[resultTab],
                        )}
                      />
                      <Table
                        rows={grouped(
                          (
                            {
                              Monthly: "monthly",
                              Yearly: "yearly",
                              Direction: "direction",
                              "Time of day": "trigger_time_bins",
                              Weekday: "weekday",
                              Risk: "risk_buckets_left_inclusive",
                            } as any
                          )[resultTab],
                        )}
                        columns={["group", ...metricsKeys]}
                      />
                    </>
                  )}
                </section>
              </>
            ) : (
              <div className="empty panel">
                {current
                  ? current.status === "failed"
                    ? "Run failed. Review the error and local worker log, then fix or clone the configuration."
                    : current.status === "cancelled"
                      ? "Run cancelled. Its configuration remains in history."
                      : "Worker is processing this run. Results appear here automatically."
                  : "Open a strategy, configure inputs and run a backtest."}
              </div>
            )}
          </>
        )}
        {page === "Runs" && (
          <section className="panel">
            <h2>Immutable run history</h2>
            <Table
              rows={runs.map((r) => ({
                ...r,
                net_pnl_usd: r.metrics?.overall.net_pnl_usd,
                trades: r.metrics?.overall.trades,
              }))}
              columns={[
                "name",
                "status",
                "created_at",
                "trades",
                "net_pnl_usd",
                "notes",
              ]}
              onRow={(r) => {
                setActive(r.id);
                setPage("Backtest");
              }}
            />
            {current && (
              <button
                onClick={() =>
                  void guard(async () => {
                    const r = await api(`/backtests/${active}/clone`, {});
                    setActive(r.id);
                    await refresh();
                    setPage("Backtest");
                  })
                }
              >
                Clone selected run configuration
              </button>
            )}
          </section>
        )}
        {page === "Compare" && (
          <>
            <div className="panel">
              <h2>Select completed runs</h2>
              <div className="choices">
                {runs
                  .filter((r) => r.status === "completed")
                  .map((r) => (
                    <label key={r.id}>
                      <input
                        type="checkbox"
                        checked={compareIds.includes(r.id)}
                        onChange={(e) =>
                          setCompareIds(
                            e.target.checked
                              ? [...compareIds, r.id]
                              : compareIds.filter((x) => x !== r.id),
                          )
                        }
                      />
                      {r.name} · {r.created_at.slice(0, 16)}
                    </label>
                  ))}
              </div>
              <button
                className="primary"
                disabled={!compareIds.length}
                onClick={() => void guard(compare)}
              >
                Compare selected
              </button>
            </div>
            {comparison && (
              <>
                <div className="warning">
                  {comparison.warnings.join(" ") ||
                    "Matching date, data and engine settings. Inspect parameter differences below."}
                </div>
                <div className="panel">
                  <div className="tabs">
                    {["Equity", "Drawdown"].map((mode) => (
                      <button
                        key={mode}
                        className={compareMode === mode ? "active" : ""}
                        onClick={() => setCompareMode(mode)}
                      >
                        {mode}
                      </button>
                    ))}
                  </div>
                  <Curve
                    rows={compareCurve()}
                    series={comparison.runs.map((r: any) => r.id)}
                    labels={Object.fromEntries(
                      comparison.runs.map((r: any) => [
                        r.id,
                        r.name + " · " + r.id.slice(0, 6),
                      ]),
                    )}
                  />
                  <Table
                    rows={comparison.runs.map((r: any) => ({
                      name: r.name,
                      ...r.metrics.overall,
                      long_pnl: r.metrics.direction.LONG.net_pnl_usd,
                      short_pnl: r.metrics.direction.SHORT.net_pnl_usd,
                    }))}
                    columns={[
                      "name",
                      ...metricsKeys,
                      "total_r",
                      "average_winner_usd",
                      "average_loser_usd",
                      "long_pnl",
                      "short_pnl",
                    ]}
                  />
                  {[
                    "yearly",
                    "monthly",
                    "direction",
                    "trigger_time_bins",
                    "weekday",
                    "risk_buckets_left_inclusive",
                    "excursions",
                  ].map((key) => (
                    <details key={key}>
                      <summary>{key.replaceAll("_", " ")}</summary>
                      <Table
                        rows={comparison.runs.flatMap((r: any) =>
                          Object.entries(r.metrics[key]).map(([group, v]) => ({
                            run: r.name,
                            group,
                            ...(typeof v === "object" && v !== null
                              ? (v as object)
                              : { value: v }),
                          })),
                        )}
                      />
                    </details>
                  ))}
                  <details>
                    <summary>Exact configuration differences</summary>
                    <pre>
                      {JSON.stringify(comparison.configurations, null, 2)}
                    </pre>
                  </details>
                </div>
              </>
            )}
          </>
        )}
        {page === "Sweeps" && (
          <>
            <div className="panel">
              <h2>Single-parameter experiment</h2>
              <p>
                Current strategy: {selected?.name || "Open a strategy first"}.
                Uses the editor’s dates and base inputs.
              </p>
              <div className="warning">
                Exploratory sweeps are in-sample research. No automatic ranking
                or best-strategy selection.
              </div>
              <label>
                Parameter
                <select
                  value={sweepKey}
                  onChange={(e) => setSweepKey(e.target.value)}
                >
                  {inputs
                    .filter((i) => ["float", "int", "choice"].includes(i.type))
                    .map((i) => (
                      <option key={i.id} value={i.id}>
                        {i.label}
                      </option>
                    ))}
                </select>
              </label>
              <label>
                Values (comma separated)
                <input
                  aria-label="Sweep values"
                  value={sweepValues}
                  onChange={(e) => setSweepValues(e.target.value)}
                />
              </label>
              <button
                className="primary"
                disabled={!selected}
                onClick={() => void guard(startSweep)}
              >
                Run sweep
              </button>
            </div>
            {sweeps.map((s) => (
              <div className="panel" key={s.id}>
                <h2>{s.name}</h2>
                <Table
                  rows={s.children.map((r: any) => ({
                    id: r.id,
                    value: r.value,
                    status: r.status,
                    ...r.metrics?.overall,
                  }))}
                  columns={["value", "status", ...metricsKeys]}
                  onRow={(r) => {
                    setActive(r.id);
                    setPage("Backtest");
                  }}
                />
              </div>
            ))}
          </>
        )}
        {page === "Inspector" && <TradeInspector runId={active} tradeId={inspectedTrade} onNavigate={setInspectedTrade} onBack={()=>setPage("Trades")} />}
        {page === "Trades" && (
          <>
            <div className="toolbar">
              <select
                aria-label="Trade run"
                value={active}
                onChange={(e) => setActive(e.target.value)}
              >
                <option value="">Select run</option>
                {runs
                  .filter((r) => r.status === "completed")
                  .map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
              </select>
              {active && (
                <a
                  className="button"
                  href={`/api/backtests/${active}/export.csv`}
                >
                  Export all run trades CSV
                </a>
              )}
            </div>
            <div className="filters">
              {[
                "direction",
                "outcome",
                "year",
                "month",
                "weekday",
                "exit_reason",
              ].map((k) => (
                <label key={k}>
                  {k}
                  <select
                    value={filters[k] || ""}
                    onChange={(e) =>
                      setFilters({ ...filters, [k]: e.target.value })
                    }
                  >
                    <option value="">All</option>
                    {(k === "direction"
                      ? ["LONG", "SHORT"]
                      : k === "outcome"
                        ? ["winner", "loser"]
                        : k === "exit_reason"
                          ? ["STOP", "TARGET", "SESSION_CLOSE"]
                          : k === "weekday"
                            ? [
                                "Monday",
                                "Tuesday",
                                "Wednesday",
                                "Thursday",
                                "Friday",
                              ]
                            : k === "year"
                              ? ["2024", "2025", "2026"]
                              : Array.from({ length: 12 }, (_, i) =>
                                  String(i + 1),
                                )
                    ).map((x) => (
                      <option key={x}>{x}</option>
                    ))}
                  </select>
                </label>
              ))}
              {[
                "start",
                "end",
                "risk_min",
                "risk_max",
                "time_from",
                "time_to",
              ].map((k) => (
                <label key={k}>
                  {k}
                  <input
                    type={
                      k.includes("risk")
                        ? "number"
                        : k.includes("time")
                          ? "time"
                          : "date"
                    }
                    value={filters[k] || ""}
                    onChange={(e) =>
                      setFilters({ ...filters, [k]: e.target.value })
                    }
                  />
                </label>
              ))}
            </div>
            <section className="panel">
              <p>{tradeRows.length} matching trades</p>
              <Table
                rows={tradeRows}
                onRow={(t)=>{setInspectedTrade(t.trade_id);setPage("Inspector")}}
                columns={[
                  "Date",
                  "Time",
                  "direction",
                  "entry_price",
                  "stop_price",
                  "target_price",
                  "exit_price",
                  "risk_points",
                  "net_pnl_usd",
                  "result_r",
                  "mfe_points",
                  "mae_points",
                  "duration_minutes",
                  "exit_reason",
                ]}
              />
            </section>
          </>
        )}
        {page === "Data" && (
          <div className="panel">
            <h2>Local historical sources</h2>
            <p>
              No data is downloaded on startup. UTC timestamps and source files
              remain unchanged.
            </p>
            <Table rows={data?.datasets || []} />
            <p>{data?.date_semantics}</p>
          </div>
        )}
        {page === "Research" && (
          <div className="panel">
            <h2>FVG lifecycle explorer</h2>
            <div className="filters">
              {[
                "direction",
                "touched",
                "fully_filled",
                "close_invalidated",
                "wick_invalidated",
                "opening_exception",
              ].map((k) => (
                <label key={k}>
                  {k}
                  <select
                    value={researchFilters[k] || ""}
                    onChange={(e) =>
                      setResearchFilters({
                        ...researchFilters,
                        [k]: e.target.value,
                      })
                    }
                  >
                    <option value="">All</option>
                    {(k === "direction"
                      ? ["bullish", "bearish"]
                      : ["true", "false"]
                    ).map((x) => (
                      <option key={x}>{x}</option>
                    ))}
                  </select>
                </label>
              ))}
              {[
                "start",
                "end",
                "size_min",
                "size_max",
                "time_from",
                "time_to",
              ].map((k) => (
                <label key={k}>
                  {k}
                  <input
                    type={
                      k.includes("size")
                        ? "number"
                        : k.includes("time")
                          ? "time"
                          : "date"
                    }
                    value={researchFilters[k] || ""}
                    onChange={(e) =>
                      setResearchFilters({
                        ...researchFilters,
                        [k]: e.target.value,
                      })
                    }
                  />
                </label>
              ))}
            </div>
            <button
              onClick={() =>
                void guard(async () =>
                  setResearch(
                    await api(
                      "/research/fvgs?" +
                        new URLSearchParams(
                          Object.fromEntries(
                            Object.entries(researchFilters)
                              .filter(([, v]) => v)
                              .map(([k, v]) => [k, String(v)]),
                          ),
                        ).toString(),
                    ),
                  ),
                )
              }
            >
              Query research
            </button>
            {research && (
              <>
                <p>{research.denominator}</p>
                <Table rows={[research.stats]} />
                <Table rows={research.rows} />
                <small>
                  First 100 matching records. API supports pagination.
                </small>
              </>
            )}
          </div>
        )}
        {page === "Settings" && (
          <div className="panel">
            <h2>Local research environment</h2>
            <p>Backend: 127.0.0.1:8000 · Frontend: 127.0.0.1:5173</p>
            <p>
              Only run strategy code you trust. Workers isolate crashes and
              enforce timeouts, but Python is not securely sandboxed.
            </p>
            <p>
              Engine v1: MNQ / 5m, full XNYS sessions, one trade per NY date,
              fixed brackets, no position management. Other instruments and
              management hooks require separately validated engine extensions.
            </p>
            <p>
              Immutable strategy versions and run snapshots are stored in
              SQLite. Market data and run artifacts remain local and ignored by
              Git.
            </p>
            <a
              href="http://127.0.0.1:8000/docs"
              target="_blank"
              rel="noreferrer"
            >
              Open API reference
            </a>
          </div>
        )}
      </main>
    </div>
  );
}
