import { useEffect, useState } from "react";
import { api } from "./api";
export default function LevelStudyReport() {
  const [study, setStudy] = useState<any>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api("/research/eight-level-study")
      .then(setStudy)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section aria-label="Eight-level research" className="panel">
      <h2>Eight-level reaction and entry study</h2>
      <p>
        Development · 2020–2023 · Fixed daily levels · Four reaction families ·
        Ten entry definitions
      </p>
      {error ? (
        <p role="alert">{error}</p>
      ) : !study ? (
        <p>Checking study availability…</p>
      ) : study.ready ? (
        <>
          <p>
            {Number(study.events).toLocaleString()} entry observations. Research
            measurements, not a trading strategy.
          </p>
          <a
            href="/api/research/eight-level-study/files/study.html"
            target="_blank"
            rel="noreferrer"
          >
            Open results, entry comparisons and chart audits
          </a>
          <p>
            <a href="/api/research/eight-level-study/files/EIGHT_LEVEL_RESEARCH_REPORT.md">
              Download complete report
            </a>{" "}
            ·{" "}
            <a href="/api/research/eight-level-study/files/primary_evidence.csv">
              Download corrected evidence
            </a>
          </p>
        </>
      ) : (
        <p>The local study has not completed verification yet.</p>
      )}
    </section>
  );
}
