import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { test, expect, vi, afterEach } from "vitest";
import ZoneLabeler from "../src/ZoneLabeler";
import { api } from "../src/api";
vi.mock("../src/api", () => ({ api: vi.fn() }));
vi.mock("../src/TradeInspector", () => ({
  CandleChart: () => <div>Outcome-hidden chart</div>,
}));
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});
const value = {
  candidate: 3,
  total: 10,
  selection: {
    candidate: 3,
    first: 2,
    last: 2,
    zone_type: "SUPPLY",
    seed: 2020,
  },
  choices: [{ index: 2, time: "2020-01-02 02:00", complete: true, full: true }],
  chart: { candles: [], annotations: [] },
  base_count: 1,
  base_timestamps: ["2020-01-02T07:00Z"],
  base_body_ratios: [0.2],
  departure_timestamps: ["2020-01-02T11:00Z"],
  departure_body_ratios: [0.8],
  availability: "2020-01-02T15:00Z",
  preview_hash: "hash",
  top: 104,
  bottom: 100,
};
test("labeler shows Development-only chart and requires explicit departure confirmation", async () => {
  vi.mocked(api).mockResolvedValue(value);
  render(<ZoneLabeler />);
  await screen.findByText("Outcome-hidden chart");
  const save = screen.getByText("Save immutable annotation");
  expect(save).toBeDisabled();
  fireEvent.click(
    screen.getByLabelText(
      "I confirm departure candles are excluded from the selected base",
    ),
  );
  expect(save).not.toBeDisabled();
  fireEvent.click(save);
  await screen.findByRole("status");
  expect(
    vi
      .mocked(api)
      .mock.calls.some(
        ([p, b]: any) =>
          p === "/zone-labels/annotations" &&
          b.preview_hash === "hash" &&
          b.decision === "NOT_A_ZONE",
      ),
  ).toBe(true);
});
test("changing selection invalidates approval and requires recalculation", async () => {
  vi.mocked(api).mockResolvedValue(value);
  render(<ZoneLabeler />);
  await screen.findByText("Outcome-hidden chart");
  fireEvent.change(screen.getByLabelText("Zone type"), {
    target: { value: "DEMAND" },
  });
  expect(screen.queryByText("Outcome-hidden chart")).toBeNull();
  fireEvent.click(screen.getByText("Calculate rectangle"));
  await screen.findByText("Outcome-hidden chart");
  expect(
    vi
      .mocked(api)
      .mock.calls.some(
        ([p, b]: any) =>
          p === "/zone-labels/preview" && b.zone_type === "DEMAND",
      ),
  ).toBe(true);
});
test("server errors displayed without research fallback", async () => {
  vi.mocked(api).mockRejectedValue(new Error("Development only"));
  render(<ZoneLabeler />);
  expect((await screen.findByRole("alert")).textContent).toContain(
    "Development only",
  );
  expect(screen.queryByText("Save immutable annotation")).toBeNull();
});
