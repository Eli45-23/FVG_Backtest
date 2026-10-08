export const numericFields = [
  "atr14",
  "atr_percentile",
  "event_candle_range",
  "body_ratio",
  "break_distance_points",
  "break_distance_atr",
  "penetration_points",
  "penetration_atr",
  "room_points",
  "room_atr",
  "opening_range_size",
  "opening_range_atr",
  "premarket_range_size",
  "premarket_range_atr",
  "prior_day_range",
  "prior_day_range_atr",
  "overnight_gap",
  "overnight_gap_atr",
  "distance_open_to_level",
  "distance_open_to_level_atr",
  "distance_to_pdh",
  "distance_to_pdl",
  "distance_to_next_level",
  "ema_separation",
  "ema_absolute_separation",
  "ema_separation_atr",
  "ema9_slope",
  "ema20_slope",
  "vwap_distance",
  "vwap_distance_atr",
  "swing_displacement",
  "swing_displacement_atr",
  "zone_distance",
  "zone_distance_atr",
  "directional_efficiency",
  "rolling_range_atr",
];
export default function NumericResearch({
  value,
  onChange,
}: {
  value: Record<string, any>;
  onChange: (v: Record<string, any>) => void;
}) {
  return (
    <details>
      <summary>Numeric ranges and saved buckets</summary>
      <p>
        Inclusive bounds; buckets include their lower edge. Missing measurements
        fail bounded filters. These settings are frozen when the study is
        created.
      </p>
      <label>
        Add measurement
        <select
          aria-label="Add numeric measurement"
          value=""
          onChange={(e) =>
            e.target.value && onChange({ ...value, [e.target.value]: {} })
          }
        >
          <option value="">Select…</option>
          {numericFields
            .filter((k) => !(k in value))
            .map((k) => (
              <option key={k}>{k}</option>
            ))}
        </select>
      </label>
      {Object.entries(value).map(([key, rule]) => (
        <div className="toolbar" key={key}>
          <strong>{key}</strong>
          {["min", "max"].map((b) => (
            <label key={b}>
              {b}
              <input
                aria-label={`${key} ${b}`}
                type="number"
                value={rule[b] ?? ""}
                onChange={(e) =>
                  onChange({
                    ...value,
                    [key]: {
                      ...rule,
                      [b]:
                        e.target.value === "" ? null : Number(e.target.value),
                    },
                  })
                }
              />
            </label>
          ))}
          <label>
            Bucket edges
            <input
              aria-label={`${key} edges`}
              placeholder="10, 25, 50"
              defaultValue={(rule.edges ?? []).join(", ")}
              onBlur={(e) =>
                onChange({
                  ...value,
                  [key]: {
                    ...rule,
                    edges: e.target.value.trim()
                      ? e.target.value.split(",").map(Number)
                      : [],
                  },
                })
              }
            />
          </label>
          <button
            onClick={() => {
              const copy = { ...value };
              delete copy[key];
              onChange(copy);
            }}
          >
            Remove {key}
          </button>
        </div>
      ))}
    </details>
  );
}
