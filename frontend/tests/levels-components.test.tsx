import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { vi, test, expect, afterEach } from "vitest";
import EventStudies from "../src/EventStudies";
import { api } from "../src/api";
vi.mock("../src/api", () => ({ api: vi.fn() }));
vi.mock("../src/TradeInspector", () => ({
  CandleChart: () => <div>Event candle chart</div>,
}));
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
function mock(studies: any[] = []) {
  vi.mocked(api).mockImplementation(async (path) => {
    if (path.endsWith("/profiles")) return [{ profile: "research_2020_2026" }];
    if (path.endsWith("/studies")) return studies;
    if (path.includes("/events?")) return { count: 0, events: [] };
    return {};
  });
}
test("PM is disabled and must have explicit endpoints when enabled", async () => {
  mock();
  render(<EventStudies />);
  await screen.findByText("research_2020_2026");
  expect(screen.queryByLabelText("Premarket start")).toBeNull();
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByText("Create Event Study"));
  await screen.findByRole("alert");
  expect(screen.getByRole("alert").textContent).toContain("both explicit");
});
test("segment selection uses exclusive planned boundaries", async () => {
  mock();
  render(<EventStudies />);
  fireEvent.change(screen.getByLabelText("Research segment"), {
    target: { value: "validation" },
  });
  expect((screen.getByLabelText("Study start") as HTMLInputElement).value).toBe(
    "2024-01-01",
  );
  expect((screen.getByLabelText("Study end") as HTMLInputElement).value).toBe(
    "2025-01-01",
  );
});
test("sealed OOS does not request summary or offer exports", async () => {
  mock([
    {
      id: "s",
      name: "Sealed",
      status: "sealed",
      config: {
        dataset: "research_2020_2026",
        segment: "out-of-sample",
        start: "2025-01-01",
        end: "2025-02-01",
      },
      outcomes_available: false,
    },
  ]);
  render(<EventStudies />);
  await screen.findByText(/Sealed ·/);
  fireEvent.change(screen.getByLabelText("Saved event study"), {
    target: { value: "s" },
  });
  await screen.findByText("OOS outcomes are sealed");
  expect(screen.queryByText("Export full JSON")).toBeNull();
  expect(vi.mocked(api).mock.calls.some(([p]) => p.includes("/summary"))).toBe(
    false,
  );
  const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
  fireEvent.click(screen.getByText("Explicitly reveal OOS outcomes"));
  expect(confirm).toHaveBeenCalled();
  expect(vi.mocked(api).mock.calls.some(([p]) => p.endsWith("/reveal"))).toBe(
    false,
  );
});
