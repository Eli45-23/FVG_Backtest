import { useEffect, useState } from "react";
import { api } from "./api";
export default function O15lReport() {
  const [study, setStudy] = useState<any>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api("/research/o15l-clear-hold")
      .then(setStudy)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section aria-label="O15L clearance hold" className="panel">
      <h2>O15L upward clearance-and-hold · 1R</h2>
      <p>
        Development · 2020–2023 · Frozen nearby levels · Root-break stop · Fixed 1R target · Actual fees
      </p>
      {error ? (
        <p role="alert">{error}</p>
      ) : !study ? (
        <p>Checking study availability…</p>
      ) : study.ready ? (
        <>
          <p>
            {Number(study.events).toLocaleString()} causal confirmations.
            Repeated entries with one position at a time.
          </p>
          <a
            href="/api/research/o15l-clear-hold/files/study.html"
            target="_blank"
            rel="noreferrer"
          >
            Open clearance-and-hold results and trades
          </a>
          <p>
            <a href="/api/research/o15l-clear-hold/files/O15L_CLEAR_HOLD_REPORT.md">
              Download complete report
            </a>{" "}
            ·{" "}
            <a href="/api/research/o15l-clear-hold/files/trades_1tick.csv">
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
