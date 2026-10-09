import { useEffect, useState } from "react";
import { api } from "./api";
import { CandleChart } from "./TradeInspector";
import { Table } from "./components";
export default function ZoneLabeler() {
  const [candidate, setCandidate] = useState<any>(null),
    [preview, setPreview] = useState<any>(null),
    [selection, setSelection] = useState<any>(null);
  const [seed, setSeed] = useState(2020),
    [jump, setJump] = useState("2020-01-07T10:00"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [decision, setDecision] = useState("NOT_A_ZONE"),
    [approved, setApproved] = useState(false),
    [excluded, setExcluded] = useState(false),
    [notes, setNotes] = useState(""),
    [message, setMessage] = useState(""),
    [report, setReport] = useState<any>(null);
  async function action(fn: () => Promise<void>) {
    setError("");
    setBusy(true);
    try {
      await fn();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function navigate(mode = "index") {
    await action(async () => {
      const x = await api(
        `/zone-labels/candidate?mode=${mode}&index=${candidate?.candidate || 0}&seed=${seed}&jump=${encodeURIComponent(jump)}`,
      );
      setCandidate(x);
      setPreview(x);
      setSelection(x.selection);
      setApproved(false);
      setExcluded(false);
      setMessage("");
      setNotes("");
      setDecision("NOT_A_ZONE");
    });
  }
  useEffect(() => {
    navigate();
  }, []);
  function change(k: string, v: any) {
    setSelection({ ...selection, [k]: v });
    setPreview(null);
    setApproved(false);
    setExcluded(false);
  }
  async function refresh() {
    await action(async () =>
      setPreview(await api("/zone-labels/preview", selection)),
    );
  }
  function download(value: any) {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "zone-ground-truth.json";
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <section className="zone-labeler">
      <h2>Zone Ground Truth Labeler</h2>
      <p>
        Development only · 2020–2023 · PROVISIONAL_PENDING_HUMAN_GROUND_TRUTH
      </p>
      <p>
        Calendar discrepancies remain unresolved. Label the original
        base/departure definition only. Post-confirmation outcomes and provider
        predictions are hidden. Ordinary complete-bar opportunities are
        included.
      </p>
      {error && <p role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}
      <div className="toolbar">
        <button disabled={busy} onClick={() => navigate("previous")}>
          Previous candidate
        </button>
        <button disabled={busy} onClick={() => navigate("next")}>
          Next candidate
        </button>
        <label>
          Saved seed
          <input
            aria-label="Saved seed"
            type="number"
            value={seed}
            onChange={(e) => setSeed(Number(e.target.value))}
          />
        </label>
        <button disabled={busy} onClick={() => navigate("random")}>
          Random Development candidate
        </button>
        <input
          aria-label="Jump to New York time"
          type="datetime-local"
          min="2020-01-01T00:00"
          max="2023-12-31T23:59"
          value={jump}
          onChange={(e) => setJump(e.target.value)}
        />
        <button disabled={busy} onClick={() => navigate("jump")}>
          Jump
        </button>
      </div>
      {candidate && selection && (
        <>
          <p>
            Opportunity {candidate.candidate} · {candidate.total} available ·
            all times New York
          </p>
          <div className="toolbar">
            {(["first", "last"] as const).map((k) => (
              <label key={k}>
                {k === "first" ? "First base candle" : "Last base candle"}
                <select
                  aria-label={
                    k === "first" ? "First base candle" : "Last base candle"
                  }
                  value={selection[k]}
                  onChange={(e) => change(k, Number(e.target.value))}
                >
                  {candidate.choices
                    .filter((x: any) => x.index < candidate.candidate)
                    .map((x: any) => (
                      <option
                        key={x.index}
                        value={x.index}
                        disabled={!x.complete || !x.full}
                      >
                        {x.time}
                        {!x.complete || !x.full ? " · unavailable" : ""}
                      </option>
                    ))}
                </select>
              </label>
            ))}
            <label>
              Zone type
              <select
                aria-label="Zone type"
                value={selection.zone_type}
                onChange={(e) => change("zone_type", e.target.value)}
              >
                <option>SUPPLY</option>
                <option>DEMAND</option>
              </select>
            </label>
            <button disabled={busy} onClick={refresh}>
              Calculate rectangle
            </button>
          </div>
          {preview && (
            <>
              <CandleChart data={preview.chart} />
              <p>{preview.warning}</p>
              <Table
                rows={[
                  {
                    base_count: preview.base_count,
                    top: preview.top,
                    bottom: preview.bottom,
                    width: preview.width,
                    width_ATR: preview.width_atr,
                    ATR: preview.atr14,
                    displacement: preview.departure_displacement,
                    displacement_ATR: preview.displacement_atr,
                    BOS: preview.bos ?? "unavailable",
                    CHoCH: preview.choch ?? "unavailable",
                    FVG: preview.fvg ?? "unavailable",
                    availability: new Date(preview.availability).toLocaleString(
                      "en-US",
                      { timeZone: "America/New_York" },
                    ),
                  },
                ]}
              />
              <p>
                Base timestamps: {preview.base_timestamps.join(", ")} (UTC).
                Body ratios: {preview.base_body_ratios.join(", ")}
              </p>
              <p>
                Departure timestamps: {preview.departure_timestamps.join(", ")}{" "}
                (UTC). Body ratios: {preview.departure_body_ratios.join(", ")}
              </p>
              <label>
                Human decision
                <select
                  aria-label="Human decision"
                  value={decision}
                  onChange={(e) => setDecision(e.target.value)}
                >
                  <option>NOT_A_ZONE</option>
                  <option>VALID_SUPPLY</option>
                  <option>VALID_DEMAND</option>
                </select>
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={approved}
                  onChange={(e) => setApproved(e.target.checked)}
                />
                Approve calculated rectangle
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={excluded}
                  onChange={(e) => setExcluded(e.target.checked)}
                />
                I confirm departure candles are excluded from the selected base
              </label>
              <textarea
                aria-label="Annotation notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Definition notes only; no subsequent outcomes"
              />
              <button
                disabled={busy || !excluded}
                onClick={() =>
                  action(async () => {
                    const x = await api("/zone-labels/annotations", {
                      ...selection,
                      decision,
                      rectangle_approved: approved,
                      departure_excluded_confirmed: excluded,
                      notes,
                      preview_hash: preview.preview_hash,
                    });
                    setMessage("Annotation saved immutably: " + x.id);
                  })
                }
              >
                Save immutable annotation
              </button>
            </>
          )}
        </>
      )}
      <hr />
      <button
        disabled={busy}
        onClick={() =>
          action(async () => download(await api("/zone-labels/annotations")))
        }
      >
        Export annotations JSON
      </button>
      <button
        disabled={busy}
        onClick={() =>
          action(async () => {
            const snap = await api("/zone-labels/freeze", {});
            const x = await api("/zone-labels/compare/" + snap.id, {});
            setReport(x);
            setMessage("Frozen human-label snapshot: " + snap.id);
          })
        }
      >
        Freeze labels and compare provider
      </button>
      {report && (
        <>
          <h3>Reviewed-opportunity agreement — not trading evidence</h3>
          <p>{report.report.scope}</p>
          <Table
            rows={[report.report].map(
              ({ rows, scope, by_direction, by_base_count, ...r }: any) => r,
            )}
          />
          <h4>Supply / demand agreement</h4>
          <Table
            rows={Object.entries(report.report.by_direction).map(
              ([side, r]: any) => ({
                side,
                TP: r.true_positives,
                FP: r.false_positives,
                FN: r.false_negatives,
                precision: r.precision,
                recall: r.recall,
                boundary_agreement: r.exact_boundary_agreement,
                availability_agreement: r.availability_time_agreement,
              }),
            )}
          />
          <h4>Base-count agreement</h4>
          <Table
            rows={Object.entries(report.report.by_base_count).map(
              ([count, r]: any) => ({
                count,
                TP: r.true_positives,
                FP: r.false_positives,
                FN: r.false_negatives,
                precision: r.precision,
                recall: r.recall,
              }),
            )}
          />
          <Table rows={report.report.rows} />
          <button onClick={() => download(report)}>
            Export comparison JSON
          </button>
        </>
      )}
    </section>
  );
}
