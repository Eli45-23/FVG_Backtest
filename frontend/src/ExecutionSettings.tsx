export default function ExecutionSettings({
  value,
  onChange,
}: {
  value: any;
  onChange: (v: any) => void;
}) {
  const set = (key: string, v: any) => onChange({ ...value, [key]: v });
  return (
    <fieldset>
      <legend>Execution policy</legend>
      <label>
        Execution mode
        <select
          aria-label="Execution mode"
          value={value.execution_mode ?? "legacy_v1"}
          onChange={(e) => set("execution_mode", e.target.value)}
        >
          <option value="legacy_v1">Validated legacy</option>
          <option value="extended_v1">Extended · flat-only sequential</option>
        </select>
      </label>
      <label>
        Primary timeframe
        <select
          aria-label="Primary timeframe"
          value={value.timeframe}
          onChange={(e) =>
            onChange({
              ...value,
              timeframe: e.target.value,
              execution_mode:
                e.target.value === "5m" ? value.execution_mode : "extended_v1",
            })
          }
        >
          {["1m", "5m", "15m", "4h"].map((v) => (
            <option key={v}>{v}</option>
          ))}
        </select>
      </label>
      <label>
        Maximum trades per day
        <select
          aria-label="Maximum trades per day"
          value={
            value.max_trades_per_day === null
              ? "unlimited"
              : (value.max_trades_per_day ?? 1)
          }
          onChange={(e) =>
            onChange({
              ...value,
              max_trades_per_day:
                e.target.value === "unlimited" ? null : Number(e.target.value),
              execution_mode: "extended_v1",
            })
          }
        >
          {[1, 2, 3, 5, "unlimited"].map((v) => (
            <option key={v}>{v}</option>
          ))}
        </select>
      </label>
      <label>
        Position sizing
        <select
          aria-label="Position sizing"
          value={value.sizing_mode ?? "FIXED_QUANTITY"}
          onChange={(e) =>
            onChange({
              ...value,
              sizing_mode: e.target.value,
              execution_mode: "extended_v1",
            })
          }
        >
          <option>FIXED_QUANTITY</option>
          <option>FIXED_DOLLAR_RISK</option>
        </select>
      </label>
      {value.sizing_mode === "FIXED_DOLLAR_RISK" && (
        <label>
          Risk budget USD
          <input
            aria-label="Risk budget USD"
            type="number"
            min="0.01"
            step="0.01"
            value={value.risk_budget ?? "100"}
            onChange={(e) => set("risk_budget", e.target.value)}
          />
        </label>
      )}
      <label>
        Higher-timeframe anchor
        <select
          aria-label="Higher-timeframe anchor"
          value={value.frame_config?.session ?? "extended"}
          onChange={(e) =>
            set(
              "frame_config",
              e.target.value === "rth"
                ? {
                    anchor: "09:30",
                    timezone: "America/New_York",
                    session: "rth",
                  }
                : { anchor: "00:00", timezone: "UTC", session: "extended" },
            )
          }
        >
          <option value="extended">Extended · UTC 00:00</option>
          <option value="rth">RTH · New York 09:30</option>
        </select>
      </label>
      <p className="muted">
        MNQ · full XNYS entry sessions · 1-minute fills. Extended execution
        permits sequential positions only. Partial legs require extended mode.
      </p>
    </fieldset>
  );
}
