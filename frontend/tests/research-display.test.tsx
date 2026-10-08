import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import { newYorkTime, eventStages } from "../src/researchDisplay";
import { Table } from "../src/components";
test("research dates explicitly show NY date, year and DST", () => {
  expect(newYorkTime("2020-01-07T14:45:00Z")).toBe("Jan 07, 2020, 09:45 EST");
  expect(newYorkTime("2020-07-07T13:45:00Z")).toBe("Jul 07, 2020, 09:45 EDT");
});
test("stage audit uses the bar ending at confirmation, not the future bar", () => {
  const chart = {
    event: {
      break_confirmation_timestamp: "2020-01-07T14:40:00Z",
      timestamp_utc: "2020-01-07T14:45:00Z",
    },
    candles: [
      { timestamp_utc: "2020-01-07T14:35:00Z", close: 10 },
      { timestamp_utc: "2020-01-07T14:40:00Z", close: 11 },
      { timestamp_utc: "2020-01-07T14:45:00Z", close: 99 },
    ],
  };
  expect(eventStages(chart).map((r) => r.close)).toEqual([10, 11]);
});
test("full evidence region is keyboard accessible and retains inference columns", () => {
  render(
    <Table
      label="Date-clustered evidence"
      rows={[
        {
          baseline_probability: 0.2,
          effect: 0.1,
          ci95: [0.01, 0.2],
          p_value: 0.03,
          q_value: 0.04,
        },
      ]}
    />,
  );
  expect(
    screen.getByRole("region", { name: "Date-clustered evidence" }),
  ).toHaveAttribute("tabindex", "0");
  for (const name of [
    "baseline probability",
    "effect",
    "ci95",
    "p value",
    "q value",
  ])
    expect(screen.getByRole("button", { name })).toBeInTheDocument();
});
