import { useEffect, useState } from "react";
import { DiffEditor } from "@monaco-editor/react";
import { api } from "./api";
import { Table } from "./components";
export default function VersionBrowser({
  strategyId,
  tab,
  initialVersion,
  onOpen,
  onRun,
}: {
  strategyId: string;
  tab: string;
  initialVersion?: string;
  onOpen: (id: string) => void;
  onRun: (id: string) => void;
}) {
  const [versions, setVersions] = useState<any[]>([]),
    [left, setLeft] = useState(""),
    [right, setRight] = useState(""),
    [detail, setDetail] = useState<any>(null),
    [diff, setDiff] = useState<any>(null),
    [error, setError] = useState("");
  const guard = async (fn: () => Promise<void>) => {
    try {
      setError("");
      await fn();
    } catch (e) {
      setError((e as Error).message);
    }
  };
  useEffect(() => {
    void guard(async () => {
      const vs = await api(`/strategies/${strategyId}/versions`);
      setVersions(vs);
      setLeft(initialVersion || vs.at(-1)?.id || "");
      setRight(vs[0]?.id || "");
    });
  }, [strategyId, initialVersion]);
  useEffect(() => {
    if (left) void guard(async () => setDetail(await api(`/versions/${left}`)));
  }, [left]);
  useEffect(() => {
    if (left && right)
      void guard(async () =>
        setDiff(await api(`/versions/${left}/diff/${right}`)),
      );
  }, [left, right]);
  return (
    <section className="panel">
      <h2>Immutable source history</h2>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <div className="toolbar">
        <label>
          Historical version
          <select
            aria-label="Historical version"
            value={left}
            onChange={(e) => setLeft(e.target.value)}
          >
            {versions.map((v) => (
              <option value={v.id} key={v.id}>
                v{v.number} · {v.created_at.slice(0, 16)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Compare with
          <select
            aria-label="Compare version"
            value={right}
            onChange={(e) => setRight(e.target.value)}
          >
            {versions.map((v) => (
              <option value={v.id} key={v.id}>
                v{v.number}
              </option>
            ))}
          </select>
        </label>
        <button
          onClick={() =>
            void guard(async () => {
              const name = prompt("Clone historical version name");
              if (name) {
                const r = await api(`/versions/${left}/clone`, { name });
                onOpen(r.strategy_id);
              }
            })
          }
        >
          Clone this version
        </button>
        <button
          onClick={() =>
            void guard(async () => {
              if (
                confirm(
                  "Restore creates a NEW version. Existing history remains unchanged.",
                )
              ) {
                const r = await api(`/versions/${left}/restore`, {});
                onOpen(r.strategy_id);
              }
            })
          }
        >
          Restore as NEW version
        </button>
      </div>
      {detail && (
        <p>
          v{detail.number} · {detail.created_at} · {detail.runs.length} runs ·{" "}
          {detail.variants.length} variants
          <br />
          <code>{detail.source_hash}</code>
        </p>
      )}
      {tab === "Versions" && (
        <>
          <Table
            rows={versions}
            columns={[
              "number",
              "created_at",
              "source_hash",
              "run_count",
              "variant_count",
            ]}
            onRow={(v) => setLeft(v.id)}
          />
          {diff && (
            <DiffEditor
              height="520px"
              language="python"
              theme="vs-dark"
              original={diff.original.source}
              modified={diff.modified.source}
              options={{
                readOnly: true,
                originalEditable: false,
                automaticLayout: true,
              }}
            />
          )}
        </>
      )}
      {(tab === "Runs" || tab === "Versions") && (
        <>
          <h3>Runs from selected source version</h3>
          <Table
            rows={detail?.runs || []}
            columns={["name", "status", "created_at"]}
            onRow={(r) => onRun(r.id)}
          />
        </>
      )}
      {(tab === "Variants" || tab === "Versions") && (
        <>
          <h3>Variants of selected source version</h3>
          <Table
            rows={detail?.variants || []}
            columns={["name", "parameters", "created_at"]}
          />
        </>
      )}
    </section>
  );
}
