import { useEffect, useState } from "react";
import { api } from "./api";
export default function Opening15Report() {
  const [study, setStudy] = useState<any>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api("/research/opening15-breakout")
      .then(setStudy)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section aria-label="Opening-range breakout" className="panel">
      <h2>Opening 15-minute breakout · 50 points</h2>
      <p>
        Development · 2020–2023 · Opening range · Preceding-candle stop · Fixed 50-point target · Actual fees
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
            href="/api/research/opening15-breakout/files/study.html"
            target="_blank"
            rel="noreferrer"
          >
            Open breakout results, times and trades
          </a>
          <p>
            <a href="/api/research/opening15-breakout/files/OPENING15_BREAKOUT_50PT_REPORT.md">
              Download complete report
            </a>{" "}
            ·{" "}
            <a href="/api/research/opening15-breakout/files/trades_1tick.csv">
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
