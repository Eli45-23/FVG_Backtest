import { useEffect, useState } from "react";
import { api } from "./api";
export default function CombinationReport() {
  const [study, setStudy] = useState<any>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api("/research/level-combinations")
      .then(setStudy)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section aria-label="Level combinations" className="panel">
      <h2>Do nearby levels improve entries?</h2>
      <p>
        Development · 2020–2023 · Immediate versus clearance-and-hold ·
        Clustered versus isolated rejection
      </p>
      {error ? (
        <p role="alert">{error}</p>
      ) : !study ? (
        <p>Checking study availability…</p>
      ) : study.ready ? (
        <>
          <p>
            {Number(study.events).toLocaleString()} entry records. Independent
            diagnostics; not a portfolio backtest.
          </p>
          <a
            href="/api/research/level-combinations/files/study.html"
            target="_blank"
            rel="noreferrer"
          >
            Open level-combination evidence
          </a>
          <p>
            <a href="/api/research/level-combinations/files/LEVEL_COMBINATION_REPORT.md">
              Download full combination report
            </a>
            {" · "}
            <a href="/api/research/level-combinations/files/study_bundle.zip">
              Download complete study bundle
            </a>
          </p>
        </>
      ) : (
        <p>The local study has not completed verification yet.</p>
      )}
    </section>
  );
}
