/** Display only: persisted UTC timestamps and event records stay unchanged. */
export function newYorkTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
    timeZoneName: "short",
  }).format(date);
}
export function eventStages(chart: any) {
  const e = chart.event;
  const stages = [
    ["Break candle", e.break_confirmation_timestamp],
    ["Hold / event candle", e.timestamp_utc],
  ].filter(([, time]) => time);
  return stages.map(([stage, time]) => {
    const candle = chart.candles.find(
      (c: any) => Date.parse(c.timestamp_utc) + 300000 === Date.parse(time),
    );
    return {
      stage,
      bar_start_ny: candle ? newYorkTime(candle.timestamp_utc) : "Unavailable",
      confirmed_ny: newYorkTime(time),
      open: candle?.open,
      high: candle?.high,
      low: candle?.low,
      close: candle?.close,
    };
  });
}
