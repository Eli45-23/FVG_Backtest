import { useEffect, useState } from "react";
import { api } from "./api";
export default function StructureReport() {
  const [study, setStudy] = useState<any>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api("/research/structure-continuation")
      .then(setStudy)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section aria-label="Market-structure continuation" className="panel">
      <h2>Market-structure continuation · 2R</h2>
      <p>
        Development · 2020–2023 · Confirmed swings · Pullback stop · Fixed 2R target · Actual fees
      </p>
      {error ? (
        <p role="alert">{error}</p>
      ) : !study ? (
        <p>Checking study availability…</p>
      ) : study.ready ? (
        <>
          <p>
            {Number(study.events).toLocaleString()} causal breakouts.
            Repeated entries with one position at a time.
          </p>
          <a
            href="/api/research/structure-continuation/files/study.html"
            target="_blank"
            rel="noreferrer"
          >
            Open breakout results, times and trades
          </a>
          <p>
            <a href="/api/research/structure-continuation/files/STRUCTURE_CONTINUATION_REPORT.md">
              Download complete report
            </a>{" "}
            ·{" "}
            <a href="/api/research/structure-continuation/files/trades_1tick.csv">
              Download every primary trade
            </a>
          </p>
        </>
      ) : (
        <p>The local study has not completed verification yet.</p>
      )}
    </section>
  );
}
