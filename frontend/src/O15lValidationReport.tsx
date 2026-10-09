import { useEffect, useState } from "react";
import { api } from "./api";
export default function O15lValidationReport() {
  const [study, setStudy] = useState<any>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api("/research/o15l-validation")
      .then(setStudy)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section aria-label="O15L clearance hold" className="panel">
      <h2>O15L · 2024 Validation</h2>
      <p>
        Validation · 2024 · Frozen nearby levels · Root-break stop · Fixed 1R target · Actual fees
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
            href="/api/research/o15l-validation/files/study.html"
            target="_blank"
            rel="noreferrer"
          >
            Open 2024 Validation results and trades
          </a>
          <p>
            <a href="/api/research/o15l-validation/files/VALIDATION_REPORT.md">
              Download complete report
            </a>{" "}
            ·{" "}
            <a href="/api/research/o15l-validation/files/trades_1tick.csv">
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
