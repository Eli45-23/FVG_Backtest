import { useEffect, useState } from "react";
import { api } from "./api";
import { Table } from "./components";
import { CandleChart } from "./TradeInspector";

export default function EventStudies() {
  const [profiles, setProfiles] = useState<any[]>([]),
    [studies, setStudies] = useState<any[]>([]);
  const [active, setActive] = useState(""),
    [error, setError] = useState(""),
    [summary, setSummary] = useState<any>(null);
  const [rows, setRows] = useState<any[]>([]),
    [count, setCount] = useState(0),
    [offset, setOffset] = useState(0);
  const [chart, setChart] = useState<any>(null),
    [filters, setFilters] = useState<Record<string, string>>({});
  const [horizon, setHorizon] = useState("30"),
    [interpretation, setInterpretation] = useState("continuation");
  const [form, setForm] = useState({
    name: "Level development study",
    dataset: "research_2020_2026",
    segment: "development",
    start: "2020-01-02",
    end: "2020-01-11",
  });
  const [pm, setPm] = useState(false),
    [pmStart, setPmStart] = useState(""),
    [pmEnd, setPmEnd] = useState("");
  const [penetration, setPenetration] = useState("0"),
    [clearance, setClearance] = useState("0.25");
  const current = studies.find((s) => s.id === active);
  async function guard(fn: () => Promise<void>) {
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function refresh() {
    setStudies(await api("/level-research/studies"));
  }
  useEffect(() => {
    guard(async () => {
      setProfiles(await api("/level-research/profiles"));
      await refresh();
    });
  }, []);
  useEffect(() => {
    const timer = setInterval(() => refresh().catch(() => {}), 2000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    setSummary(null);
    setRows([]);
    setChart(null);
    if (!current || !["completed", "sealed"].includes(current.status)) return;
    let disposed = false;
    const query = new URLSearchParams(filters).toString();
    guard(async () => {
      const e = await api(
        `/level-research/studies/${active}/events?${query}&offset=${offset}`,
      );
      if (disposed) return;
      setRows(e.events);
      setCount(e.count);
      if (current.outcomes_available) {
        const s = await api(
          `/level-research/studies/${active}/summary?${query}&horizon=${horizon}&interpretation=${interpretation}`,
        );
        if (!disposed) setSummary(s);
      }
    });
    return () => {
      disposed = true;
    };
  }, [
    active,
    current?.status,
    current?.outcomes_available,
    filters,
    offset,
    horizon,
    interpretation,
  ]);
  async function submit() {
    await guard(async () => {
      const session: any = {
        rejection_penetration: Number(penetration),
        rejection_clearance: Number(clearance),
      };
      if (pm) {
        if (!pmStart || !pmEnd)
          throw new Error("Choose both explicit premarket endpoints");
        session.premarket_start = pmStart;
        session.premarket_end = pmEnd;
      }
      const r = await api("/level-research/studies", { ...form, session });
      await refresh();
      setActive(r.id);
      setOffset(0);
    });
  }
  return (
    <section className="event-studies">
      <h2>Level Event Studies</h2>
      <p>
        Measurement only · confirmed 5-minute events · subsequent 1-minute
        outcomes · no daily trade limit.
      </p>
      {error && (
        <div role="alert" className="error">
          {error}
        </div>
      )}
      <div className="panel">
        <h3>Create immutable study</h3>
        <div className="level-form">
          <label>
            Name
            <input
              aria-label="Study name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </label>
          <label>
            Dataset
            <select
              aria-label="Research dataset"
              value={form.dataset}
              onChange={(e) => setForm({ ...form, dataset: e.target.value })}
            >
              {profiles.map((p) => (
                <option key={p.profile}>{p.profile}</option>
              ))}
            </select>
          </label>
          <label>
            Segment
            <select
              aria-label="Research segment"
              value={form.segment}
              onChange={(e) => {
                const segment = e.target.value;
                const ranges: any = {
                  development: ["2020-01-01", "2024-01-01"],
                  validation: ["2024-01-01", "2025-01-01"],
                  "out-of-sample": ["2025-01-01", "2026-10-06"],
                };
                setForm({
                  ...form,
                  segment,
                  start: ranges[segment][0],
                  end: ranges[segment][1],
                });
              }}
            >
              {["development", "validation", "out-of-sample"].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </label>
          <label>
            Start inclusive
            <input
              aria-label="Study start"
              type="date"
              value={form.start}
              onChange={(e) => setForm({ ...form, start: e.target.value })}
            />
          </label>
          <label>
            End exclusive
            <input
              aria-label="Study end"
              type="date"
              value={form.end}
              onChange={(e) => setForm({ ...form, end: e.target.value })}
            />
          </label>
          <label>
            Rejection minimum penetration
            <input
              type="number"
              min="0"
              step="0.25"
              value={penetration}
              onChange={(e) => setPenetration(e.target.value)}
            />
          </label>
          <label>
            Rejection close-back clearance
            <input
              type="number"
              min="0"
              step="0.25"
              value={clearance}
              onChange={(e) => setClearance(e.target.value)}
            />
          </label>
        </div>
        <label>
          <input
            type="checkbox"
            checked={pm}
            onChange={(e) => setPm(e.target.checked)}
          />{" "}
          Enable PMH/PML with explicit New York window
        </label>
        {pm && (
          <div className="toolbar">
            <input
              aria-label="Premarket start"
              type="time"
              step="300"
              value={pmStart}
              onChange={(e) => setPmStart(e.target.value)}
            />
            <input
              aria-label="Premarket end"
              type="time"
              step="300"
              value={pmEnd}
              onChange={(e) => setPmEnd(e.target.value)}
            />
          </div>
        )}
        <p>
          PDH/PDL use the prior complete XNYS session, including half-days. O5
          levels become available at 09:35. PMH/PML are disabled unless
          explicitly configured. OOS outcomes remain sealed.
        </p>
        <button onClick={submit}>Create Event Study</button>
      </div>
      <div className="toolbar">
        <label>
          Saved study
          <select
            aria-label="Saved event study"
            value={active}
            onChange={(e) => {
              setActive(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">Select…</option>
            {studies.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} · {s.config.segment} · {s.status}
              </option>
            ))}
          </select>
        </label>
      </div>
      {current && (
        <>
          <p>
            <strong>{current.status.toUpperCase()}</strong> ·{" "}
            {current.config.dataset} · {current.config.start} →{" "}
            {current.config.end} · {current.config.segment.toUpperCase()}
          </p>
          {current.error && <p role="alert">{current.error}</p>}
          {["queued", "running"].includes(current.status) && (
            <button
              onClick={() =>
                guard(async () => {
                  await api(`/level-research/studies/${active}/cancel`, {});
                  await refresh();
                })
              }
            >
              Cancel study
            </button>
          )}
          {current.status === "sealed" && (
            <div className="panel">
              <strong>OOS outcomes are sealed</strong>
              <p>
                Only event detections and candles through confirmation are
                available.
              </p>
              <button
                onClick={() => {
                  if (
                    window.confirm(
                      "Reveal OOS outcomes? This action is permanently recorded and cannot be undone.",
                    )
                  )
                    guard(async () => {
                      await api(`/level-research/studies/${active}/reveal`, {});
                      await refresh();
                    });
                }}
              >
                Explicitly reveal OOS outcomes
              </button>
            </div>
          )}
          <details>
            <summary>Immutable configuration and dataset hashes</summary>
            <pre>{JSON.stringify(current.config, null, 2)}</pre>
          </details>
          <div className="level-form">
            {Object.entries({
              level_type: ["PDH", "PDL", "PMH", "PML", "O5H", "O5L"],
              interaction_type: [
                "TOUCH",
                "SWEEP_RECLAIM",
                "BREAK_ACCEPTANCE",
                "RETEST",
                "REJECTION",
              ],
              direction: ["UP", "DOWN", "UNKNOWN"],
              touch_number: ["1", "2", "3", "3+"],
              time_bucket: [
                "09:30",
                "10:00",
                "10:30",
                "11:00",
                "11:30",
                "12:00",
                "12:30",
                "13:00",
                "13:30",
                "14:00",
                "14:30",
                "15:00",
                "15:30",
                "16:00",
              ],
              year: ["2020", "2021", "2022", "2023", "2024", "2025", "2026"],
              weekday: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            }).map(([key, options]) => (
              <label key={key}>
                {key.replaceAll("_", " ")}
                <select
                  aria-label={key}
                  value={filters[key] || ""}
                  onChange={(e) => {
                    setFilters({ ...filters, [key]: e.target.value });
                    setOffset(0);
                  }}
                >
                  <option value="">All</option>
                  {options.map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
              </label>
            ))}
          </div>
          {current.outcomes_available && (
            <div className="toolbar">
              <label>
                Horizon
                <select
                  value={horizon}
                  onChange={(e) => setHorizon(e.target.value)}
                >
                  {["5", "10", "15", "30", "60", "session_close"].map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
              </label>
              <label>
                Directional view
                <select
                  value={interpretation}
                  onChange={(e) => setInterpretation(e.target.value)}
                >
                  <option>continuation</option>
                  <option>rejection</option>
                </select>
              </label>
              <a
                href={`/api/level-research/studies/${active}/export?format=json`}
              >
                Export full JSON
              </a>
              <a
                href={`/api/level-research/studies/${active}/export?format=csv`}
              >
                Export events CSV
              </a>
            </div>
          )}
          {summary && (
            <>
              <h3>
                Forward outcomes · {summary.overall.complete_outcomes} complete
                / {summary.overall.censored_outcomes} censored
              </h3>
              <Table
                rows={[
                  {
                    events: summary.overall.events,
                    mean_mfe: summary.overall.mean_mfe,
                    median_mfe: summary.overall.median_mfe,
                    mean_mae: summary.overall.mean_mae,
                    matched_mean_mfe: summary.overall.matched_mean_mfe,
                    baseline_mean_mfe: summary.overall.baseline_mean_mfe,
                    matched_mean_mae: summary.overall.matched_mean_mae,
                    baseline_mean_mae: summary.overall.baseline_mean_mae,
                    median_mae: summary.overall.median_mae,
                  },
                ]}
              />
              <p>
                Probabilities are fractions (0–1). Difference is matched event
                minus baseline. Baseline: ordinary observations matched by year
                and half-hour confirmation time. Overlapping classes and
                repeated baseline observations are not independent trials.
              </p>
              <Table rows={summary.overall.probabilities} />
              <details>
                <summary>Excursion distributions</summary>
                <pre>
                  {JSON.stringify(
                    {
                      mfe: summary.overall.mfe_distribution,
                      mae: summary.overall.mae_distribution,
                    },
                    null,
                    2,
                  )}
                </pre>
              </details>
              {Object.entries(summary.groups).map(([key, value]) => (
                <details key={key}>
                  <summary>By {key.replaceAll("_", " ")}</summary>
                  <Table
                    rows={(value as any[]).map((v) => ({
                      [key]: v[key],
                      events: v.events,
                      complete: v.complete_outcomes,
                      mean_mfe: v.mean_mfe,
                      median_mfe: v.median_mfe,
                      mean_mae: v.mean_mae,
                    }))}
                  />
                </details>
              ))}
            </>
          )}
          <h3>Event audit · {count} records</h3>
          <p>
            Click a row to inspect classification. Multiple classes may describe
            the same level/candle observation.
          </p>
          <Table
            rows={rows}
            columns={[
              "timestamp_ny",
              "level_type",
              "level_price",
              "interaction_type",
              "direction",
              "touch_number",
              "price_at_event",
              "distance_through_level",
            ]}
            onRow={(e) =>
              guard(async () =>
                setChart(
                  await api(
                    `/level-research/studies/${active}/events/${e.event_id}/chart`,
                  ),
                ),
              )
            }
          />
          <div className="toolbar">
            <button
              disabled={!offset}
              onClick={() => setOffset(Math.max(0, offset - 100))}
            >
              Previous events
            </button>
            <span>
              {offset + 1}–{Math.min(offset + 100, count)}
            </span>
            <button
              disabled={offset + 100 >= count}
              onClick={() => setOffset(offset + 100)}
            >
              Next events
            </button>
          </div>
          {chart && (
            <div className="panel">
              <h3>
                {chart.event.level_type} · {chart.event.interaction_type}
              </h3>
              {chart.future_hidden && <p>Future candles hidden</p>}
              <CandleChart data={chart} />
              <details>
                <summary>Event metadata</summary>
                <pre>{JSON.stringify(chart.event, null, 2)}</pre>
              </details>
            </div>
          )}
        </>
      )}
    </section>
  );
}
