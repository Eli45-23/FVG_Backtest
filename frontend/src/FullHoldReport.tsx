import { useEffect, useState } from "react";
import { api } from "./api";
export default function FullHoldReport() {
  const [study, setStudy] = useState<any>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api("/research/full-hold-feasibility")
      .then(setStudy)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section aria-label="Full-hold feasibility" className="panel">
      <h2>Next-candle full-hold feasibility</h2>
      <p>
        Development · 2020–2023 · Eight levels · Two structural stops · Fixed 1R
        and 2R targets · Actual fees
      </p>
      {error ? (
        <p role="alert">{error}</p>
      ) : !study ? (
        <p>Checking study availability…</p>
      ) : study.ready ? (
        <>
          <p>
            {Number(study.events).toLocaleString()} causal full-hold signals.
            Independent overlapping diagnostics, not an investable portfolio.
          </p>
          <a
            href="/api/research/full-hold-feasibility/files/study.html"
            target="_blank"
            rel="noreferrer"
          >
            Open full-hold comparison and cost results
          </a>
          <p>
            <a href="/api/research/full-hold-feasibility/files/DOWNWARD_BREAK_FULL_HOLD_FEASIBILITY.md">
              Download complete report
            </a>{" "}
            ·{" "}
            <a href="/api/research/full-hold-feasibility/files/fixed_target_diagnostics.csv">
              Download primary diagnostics
            </a>
          </p>
        </>
      ) : (
        <p>The local study has not completed verification yet.</p>
      )}
    </section>
  );
}
