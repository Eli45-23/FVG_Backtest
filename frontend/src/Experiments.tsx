import { useEffect, useState } from "react";
import { api } from "./api";
import { Table, KPIs } from "./components";
const segments = ["development", "validation", "out-of-sample"];
const defaults: any = {
  development: { start: "2024-01-01", end: "2026-01-01" },
  validation: { start: "2026-01-01", end: "2026-07-01" },
  "out-of-sample": { start: "2026-07-01", end: "2026-10-06" },
};
export default function Experiments({
  selected,
  params,
  settings,
  variantId,
  dirty,
  onRun,
}: {
  selected: any;
  params: any;
  settings: any;
  variantId: string;
  dirty: boolean;
  onRun: (id: string) => void;
}) {
  const [splits, setSplits] = useState<any[]>([]),
    [experiments, setExperiments] = useState<any[]>([]),
    [split, setSplit] = useState(""),
    [id, setId] = useState(""),
    [ranges, setRanges] = useState(defaults),
    [name, setName] = useState("MNQ Research Split 1"),
    [experimentName, setExperimentName] = useState("Controlled experiment"),
    [error, setError] = useState(""),
    [combined, setCombined] = useState<any>(null);
  const [profile, setProfile] = useState("legacy_2024_2026");
  const current = experiments.find((e) => e.id === id);
  const guard = async (fn: () => Promise<void>) => {
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    }
  };
  async function refresh() {
    const [sp, ex] = await Promise.all([
      api("/research-splits"),
      api("/experiments"),
    ]);
    setSplits(sp);
    setExperiments(ex);
  }
  useEffect(() => {
    void guard(refresh);
    const t = setInterval(() => void guard(refresh), 2500);
    return () => clearInterval(t);
  }, []);
  const run = async (segment: string) => {
    if (
      segment === "out-of-sample" &&
      !confirm(
        "Run and reveal the official OOS result for this frozen configuration? This exposure is recorded.",
      )
    )
      return;
    await api(`/experiments/${id}/run`, { segment });
    await refresh();
  };
  return (
    <>
      <h2>Controlled research experiments</h2>
      <p>
        New York dates · start inclusive / end exclusive. A snapshot fixes
        source and inputs; freeze locks the official OOS evaluation. Raw files
        remain locally accessible.
      </p>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <details className="panel">
        <summary>Create Research Split</summary>
        <label>
          Split dataset profile
          <select
            aria-label="Split dataset profile"
            value={profile}
            onChange={(e) => {
              setProfile(e.target.value);
              if (e.target.value === "research_2020_2026")
                setRanges({
                  development: { start: "2020-01-01", end: "2024-01-01" },
                  validation: { start: "2024-01-01", end: "2025-01-01" },
                  "out-of-sample": { start: "2025-01-01", end: "2026-10-06" },
                });
            }}
          >
            <option>legacy_2024_2026</option>
            <option>research_2020_2026</option>
          </select>
        </label>
        <label>
          Split name
          <input
            aria-label="Split name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </label>
        <div className="split-grid">
          {segments.map((segment) => (
            <section key={segment}>
              <h3>{segment.toUpperCase()}</h3>
              {["start", "end"].map((k) => (
                <label key={k}>
                  {k}
                  {k === "end" ? " (exclusive)" : ""}
                  <input
                    aria-label={`${segment} ${k}`}
                    type="date"
                    value={ranges[segment][k]}
                    onChange={(e) =>
                      setRanges({
                        ...ranges,
                        [segment]: { ...ranges[segment], [k]: e.target.value },
                      })
                    }
                  />
                </label>
              ))}
            </section>
          ))}
        </div>
        <button
          onClick={() =>
            void guard(async () => {
              const r = await api("/research-splits", {
                name,
                ranges,
                dataset_profile: profile,
              });
              setSplit(r.id);
              await refresh();
            })
          }
        >
          Create split
        </button>
      </details>
      <section className="panel">
        <h3>Create experiment from saved strategy</h3>
        <p>
          {selected
            ? `${selected.name} · v${selected.current_version}`
            : "Open a strategy first, then return here."}{" "}
          {dirty ? "Save source changes before creating an experiment." : ""}
        </p>
        <div className="toolbar">
          <label>
            Research split
            <select
              aria-label="Research split"
              value={split}
              onChange={(e) => setSplit(e.target.value)}
            >
              <option value="">Select split</option>
              {splits.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Experiment name
            <input
              aria-label="Experiment name"
              value={experimentName}
              onChange={(e) => setExperimentName(e.target.value)}
            />
          </label>
          <button
            disabled={!selected || !split || dirty}
            onClick={() =>
              void guard(async () => {
                const e = await api("/experiments", {
                  name: experimentName,
                  research_split_id: split,
                  strategy_version_id: selected.version_id,
                  variant_id: variantId || null,
                  parameters: params,
                  settings,
                });
                setId(e.id);
                setCombined(null);
                await refresh();
              })
            }
          >
            Create experiment snapshot
          </button>
        </div>
        {splits
          .find((s) => s.id === split)
          ?.warnings.map((w: string) => (
            <p className="warning" key={w}>
              {w}
            </p>
          ))}
        <details>
          <summary>Inputs to snapshot</summary>
          <pre>{JSON.stringify({ parameters: params, settings }, null, 2)}</pre>
        </details>
      </section>
      <section className="panel">
        <h3>Experiment history</h3>
        <Table
          rows={experiments.map((e) => ({
            ...e,
            source_version: e.config.strategy_version_id,
          }))}
          columns={["name", "created_at", "frozen_at", "oos_status"]}
          onRow={(e) => {
            setId(e.id);
            setCombined(null);
          }}
        />
      </section>
      {current && (
        <section className="panel">
          <h2>{current.name}</h2>
          <div className="toolbar">
            <strong data-testid="oos-status">{current.oos_status}</strong>
            <button onClick={() => void guard(() => run("development"))}>
              Run Development
            </button>
            <button onClick={() => void guard(() => run("validation"))}>
              Run Validation
            </button>
            <button
              disabled={!!current.frozen_at}
              onClick={() =>
                void guard(async () => {
                  await api(`/experiments/${id}/freeze`, {});
                  await refresh();
                })
              }
            >
              Freeze for Out-of-Sample
            </button>
            <button
              disabled={!current.frozen_at}
              onClick={() => void guard(() => run("out-of-sample"))}
            >
              Run / Reveal OOS
            </button>
          </div>
          <p>
            Frozen: {current.frozen_at || "Not frozen"} · OOS run:{" "}
            {current.oos_run_at || "Not run"} · Revealed:{" "}
            {current.oos_revealed_at || "Not revealed"}
          </p>
          <Table
            rows={segments.map((segment) => {
              const r = current.runs[segment];
              return {
                segment,
                status:
                  r?.status ||
                  (segment === "out-of-sample" ? "SEALED" : "Not run"),
                id: r?.id,
                ...r?.metrics?.overall,
                long_pnl: r?.metrics?.direction.LONG.net_pnl_usd,
                short_pnl: r?.metrics?.direction.SHORT.net_pnl_usd,
              };
            })}
            columns={[
              "segment",
              "status",
              "trades",
              "net_pnl_usd",
              "profit_factor",
              "win_rate_percent",
              "average_r",
              "total_r",
              "max_closed_trade_drawdown_usd",
              "long_pnl",
              "short_pnl",
            ]}
            onRow={(r) => {
              if (r.id) onRun(r.id);
            }}
          />
          <button
            onClick={() =>
              void guard(async () =>
                setCombined(await api(`/experiments/${id}/combined`)),
              )
            }
          >
            Combined revealed segments
          </button>
          {combined && (
            <>
              <p>{combined.label}</p>
              <KPIs m={combined.metrics} />
            </>
          )}
          <details>
            <summary>Exact immutable snapshot</summary>
            <p>{current.snapshot_hash}</p>
            <pre>{JSON.stringify(current.config, null, 2)}</pre>
          </details>
        </section>
      )}
    </>
  );
}
