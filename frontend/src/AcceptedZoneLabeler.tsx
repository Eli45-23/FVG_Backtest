import { useEffect, useState } from "react";
import { api } from "./api";
import { CandleChart } from "./TradeInspector";
import { Table } from "./components";
const root = "/zone-ground-truth-v2";
export default function AcceptedZoneLabeler() {
  const [collection, setCollection] = useState<any>(null),
    [win, setWin] = useState<any>(null),
    [idx, setIdx] = useState(0),
    [mode, setMode] = useState("BLIND"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState("");
  const [selection, setSelection] = useState<any>({
      first: 0,
      last: 0,
      side: "SUPPLY",
    }),
    [preview, setPreview] = useState<any>(null),
    [decision, setDecision] = useState(""),
    [approved, setApproved] = useState(false),
    [excluded, setExcluded] = useState(false),
    [done, setDone] = useState(true),
    [notes, setNotes] = useState(""),
    [supersedes, setSupersedes] = useState(""),
    [metrics, setMetrics] = useState<any>(null);
  async function action(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function load() {
    setCollection(await api(root + "/collection"));
  }
  useEffect(() => {
    action(load);
  }, []);
  const samples = collection?.samples.filter((s: any) => s.kind === mode) || [];
  async function open(i: number, m = mode) {
    await action(async () => {
      const list = collection.samples.filter((s: any) => s.kind === m);
      const n = Math.max(0, Math.min(i, list.length - 1));
      const x = await api(root + "/window/" + list[n].sample_id);
      setWin(x);
      setIdx(n);
      setMode(m);
      setPreview(null);
      setApproved(false);
      setExcluded(false);
      setNotes("");
      setSupersedes("");
      setMessage("");
      setDecision("");
      setDone(true);
      setSelection({
        sample_id: x.sample_id,
        first: x.choices.at(-1)?.index,
        last: x.choices.at(-1)?.index,
        side: x.proposal?.zone_type || "SUPPLY",
      });
    });
  }
  function change(k: string, v: any) {
    setSelection({ ...selection, [k]: v });
    setPreview(null);
    setApproved(false);
    setExcluded(false);
  }
  function download(x: any, name: string) {
    const u = URL.createObjectURL(
      new Blob([JSON.stringify(x, null, 2)], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = u;
    a.download = name;
    a.click();
    URL.revokeObjectURL(u);
  }
  const positive = !["NOT_A_ZONE", "REJECT_NOT_A_ZONE"].includes(decision);
  const chart = win
    ? {
        ...win.chart,
        annotations: [
          ...win.chart.annotations,
          ...(preview
            ? [
                {
                  type: "box",
                  category: "zone",
                  start_time: preview.base_timestamps[0],
                  end_time: preview.availability,
                  price_low: preview.bottom,
                  price_high: preview.top,
                  label: "Human selected base",
                },
              ]
            : []),
        ],
      }
    : null;
  return (
    <section className="accepted-zone-labeler">
      <h2>Accepted-calendar Ground Truth</h2>
      <p>
        Development only · PROVISIONAL_PENDING_HUMAN_GROUND_TRUTH · Outcomes
        hidden
      </p>
      <p>
        Label every zone confirming at the displayed cutoff. Earlier candles are
        context, not additional labeling opportunities. Blind windows are
        independent of provider detections. Near-miss reasons are hidden. Finish
        blind collection before opening provider review.
      </p>
      {error && <p role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}
      {collection && (
        <>
          <details>
            <summary>
              Frozen historical identities and acceptance criteria
            </summary>
            <pre>
              {JSON.stringify(
                {
                  identity: collection.identity,
                  protocol_sha256: collection.protocol_sha256,
                  minimum: collection.minimum,
                  acceptance: collection.acceptance,
                  matching: collection.matching,
                },
                null,
                2,
              )}
            </pre>
          </details>
          <p>
            {collection.completed.length} windows completed. All 104 unresolved
            dates excluded.
          </p>
          <div className="toolbar">
            <label>
              Collection mode{" "}
              <select
                aria-label="Collection mode"
                value={mode}
                onChange={(e) => {
                  setMode(e.target.value);
                  setWin(null);
                  setIdx(0);
                }}
              >
                <option value="BLIND">A — Blind ground truth (80)</option>
                <option value="NEAR_MISS">Blind near-miss review</option>
                <option
                  value="PROVIDER_REVIEW"
                  disabled={!collection.provider_review_unlocked}
                >
                  B — Provider candidate review (50)
                </option>
              </select>
            </label>
            <button disabled={busy} onClick={() => open(idx)}>
              Open frozen window
            </button>
            <button
              disabled={busy || !win || idx === 0}
              onClick={() => open(idx - 1)}
            >
              Previous
            </button>
            <button
              disabled={busy || !win || idx >= samples.length - 1}
              onClick={() => open(idx + 1)}
            >
              Next
            </button>
            <label>
              Window{" "}
              <select
                aria-label="Frozen window"
                value={idx}
                onChange={(e) => open(Number(e.target.value))}
              >
                {samples.map((s: any, i: number) => (
                  <option value={i} key={s.sample_id}>
                    {i + 1} · {s.ny_date}
                    {collection.completed.includes(s.sample_id)
                      ? " · complete"
                      : ""}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </>
      )}
      {win && (
        <>
          <p>
            Confirmation:{" "}
            {new Date(win.confirmation).toLocaleString("en-US", {
              timeZone: "America/New_York",
            })}{" "}
            New York. No later candles are supplied.
          </p>
          <CandleChart data={chart} />
          {win.proposal && (
            <>
              <h3>Provider proposal</h3>
              <details>
                <summary>Provider configuration identity</summary>
                <pre>
                  {JSON.stringify(
                    {
                      configuration: win.identity.provider_configuration,
                      configuration_sha256:
                        win.identity.provider_configuration_sha256,
                      source_sha256: win.identity.provider_source_sha256,
                    },
                    null,
                    2,
                  )}
                </pre>
              </details>
              <Table
                rows={[
                  {
                    zone_id: win.proposal.zone_id,
                    side: win.proposal.zone_type,
                    top: win.proposal.top,
                    bottom: win.proposal.bottom,
                    base: win.proposal.base_timestamps.join(", "),
                    availability: win.proposal.availability_timestamp,
                  },
                ]}
              />
            </>
          )}
          <label>
            Human decision{" "}
            <select
              aria-label="Accepted human decision"
              value={decision}
              onChange={(e) => setDecision(e.target.value)}
            >
              <option value="" disabled>
                Choose a human decision
              </option>
              {(mode === "PROVIDER_REVIEW"
                ? [
                    "ACCEPT_EXACT",
                    "ACCEPT_ZONE_WRONG_BASE",
                    "ACCEPT_ZONE_WRONG_BOUNDARIES",
                    "REJECT_NOT_A_ZONE",
                  ]
                : ["NOT_A_ZONE", "VALID_SUPPLY", "VALID_DEMAND"]
              ).map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          <div className="toolbar">
            {["first", "last"].map((k) => (
              <label key={k}>
                {k} base candle{" "}
                <select
                  aria-label={k + " accepted base candle"}
                  value={selection[k]}
                  onChange={(e) => change(k, Number(e.target.value))}
                >
                  {win.choices.map((x: any) => (
                    <option key={x.bar_id} value={x.index}>
                      {x.time}
                    </option>
                  ))}
                </select>
              </label>
            ))}
            <label>
              Human side{" "}
              <select
                aria-label="Human side"
                value={selection.side}
                onChange={(e) => change("side", e.target.value)}
              >
                <option>SUPPLY</option>
                <option>DEMAND</option>
              </select>
            </label>
            <button
              disabled={busy}
              onClick={() =>
                action(async () =>
                  setPreview(await api(root + "/preview", selection)),
                )
              }
            >
              Calculate human rectangle
            </button>
          </div>
          {preview && (
            <>
              <Table
                rows={[
                  {
                    base_count: preview.base_count,
                    proximal: preview.proximal,
                    distal: preview.distal,
                    width: preview.width,
                    availability: preview.availability,
                  },
                ]}
              />
              <p>
                Base body ratios: {preview.base_body_ratios.join(", ")}.
                Departure body ratios:{" "}
                {preview.departure_body_ratios.join(", ")}
              </p>
            </>
          )}
          <label>
            <input
              type="checkbox"
              checked={approved}
              onChange={(e) => setApproved(e.target.checked)}
            />
            Approve human rectangle
          </label>
          <label>
            <input
              type="checkbox"
              checked={excluded}
              onChange={(e) => setExcluded(e.target.checked)}
            />
            Departure excluded from base
          </label>
          <label>
            <input
              type="checkbox"
              checked={done}
              onChange={(e) => setDone(e.target.checked)}
            />
            This is the last zone in this window (or no zone exists)
          </label>
          <p>
            Uncheck to add multiple zones at this cutoff, then finish the
            window.
          </p>
          <textarea
            aria-label="Accepted annotation notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Definition/disagreement only; no outcomes"
          />
          <label>
            Correction of prior annotation{" "}
            <select
              aria-label="Correction version"
              value={supersedes}
              onChange={(e) => setSupersedes(e.target.value)}
            >
              <option value="">New annotation</option>
              {win.annotations_saved.map((x: any) => (
                <option key={x.annotation_id} value={x.annotation_id}>
                  {x.annotation_id} · {x.label}
                </option>
              ))}
            </select>
          </label>
          <button
            disabled={
              !decision ||
              busy ||
              (positive && (!preview || !approved || !excluded))
            }
            onClick={() =>
              action(async () => {
                const x = await api(root + "/annotations", {
                  sample_id: win.sample_id,
                  label: decision,
                  selection: positive ? selection : null,
                  preview_hash: positive ? preview?.preview_hash : null,
                  rectangle_approved: approved,
                  departure_excluded: excluded,
                  window_complete: done,
                  notes,
                  supersedes: supersedes || null,
                });
                setMessage("Human annotation saved: " + x.annotation_id);
                await load();
                setWin(await api(root + "/window/" + win.sample_id));
              })
            }
          >
            Save human annotation
          </button>
          <button
            disabled={busy || !win.annotations_saved.length}
            onClick={() =>
              action(async () => {
                await api(root + "/complete/" + win.sample_id, {});
                await load();
                setMessage("Window completed immutably");
              })
            }
          >
            Finish window
          </button>
        </>
      )}
      <hr />
      <button
        disabled={busy}
        onClick={() =>
          action(async () =>
            download(
              await api(root + "/export", {}),
              "accepted-zone-human-labels.json",
            ),
          )
        }
      >
        Export immutable snapshot
      </button>
      <button
        disabled={busy}
        onClick={() =>
          action(async () => setMetrics(await api(root + "/comparison")))
        }
      >
        Collection status / comparison
      </button>
      {metrics && (
        <>
          <p>{metrics.status}</p>
          <p>{metrics.scope}</p>
          <Table rows={[{ ...metrics, rows: undefined, groups: undefined }]} />
        </>
      )}
    </section>
  );
}
