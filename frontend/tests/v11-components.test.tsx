import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { vi, test, expect, afterEach } from "vitest";
import TradeInspector, { annotationX } from "../src/TradeInspector";
import VersionBrowser from "../src/VersionBrowser";
import Experiments from "../src/Experiments";
import { api } from "../src/api";
vi.mock("../src/api", () => ({ api: vi.fn() }));
vi.mock("@monaco-editor/react", () => ({
  DiffEditor: (p: any) => (
    <div data-testid="diff">
      {p.original}|{p.modified}|{String(p.options.readOnly)}
    </div>
  ),
}));
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});
const payload = {
  candles: [],
  annotations: [],
  management_events: [],
  run: { strategy_name: "Example", name: "Run" },
  trade: {
    direction: "LONG",
    entry_time_utc: "2024-02-05T15:00Z",
    exit_time_utc: "2024-02-05T15:10Z",
    net_pnl_usd: 20,
    result_r: 1,
  },
  previous_trade_id: "before",
  next_trade_id: "after",
  trade_number: 2,
  trade_count: 3,
};
test("inspector navigation and keyboard retain caller state", async () => {
  vi.mocked(api).mockResolvedValue(payload);
  const nav = vi.fn(),
    back = vi.fn();
  render(
    <TradeInspector runId="r" tradeId="t" onNavigate={nav} onBack={back} />,
  );
  await screen.findByText(/Example/);
  fireEvent.click(screen.getByText("Next Trade"));
  expect(nav).toHaveBeenCalledWith("after");
  fireEvent.keyDown(window, { key: "ArrowLeft" });
  expect(nav).toHaveBeenCalledWith("before");
  fireEvent.click(screen.getByText("Back to Trades"));
  expect(back).toHaveBeenCalled();
});
test("chart missing-data error is readable", async () => {
  vi.mocked(api).mockRejectedValue(new Error("No chart candles available"));
  render(
    <TradeInspector
      runId="r"
      tradeId="x"
      onNavigate={() => {}}
      onBack={() => {}}
    />,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "No chart candles",
  );
});
test("chart window selection changes server request", async () => {
  vi.mocked(api).mockResolvedValue(payload);
  render(
    <TradeInspector
      runId="r"
      tradeId="t"
      onNavigate={() => {}}
      onBack={() => {}}
    />,
  );
  await screen.findByText(/Example/);
  fireEvent.click(screen.getByText("Full session"));
  await waitFor(() =>
    expect(api).toHaveBeenLastCalledWith(
      "/backtests/r/trades/t/chart?window=session",
    ),
  );
});
test("version diff is read-only and linked history is visible", async () => {
  const v = {
    id: "v1",
    number: 1,
    source: "old",
    created_at: "2024-01-01",
    source_hash: "hash",
  };
  vi.mocked(api).mockImplementation(async (path: string) =>
    path.endsWith("/versions")
      ? [v]
      : path.includes("/diff/")
        ? { original: { source: "old" }, modified: { source: "new" } }
        : { ...v, runs: [], variants: [] },
  );
  render(
    <VersionBrowser
      strategyId="s"
      tab="Versions"
      onOpen={() => {}}
      onRun={() => {}}
    />,
  );
  expect(await screen.findByTestId("diff")).toHaveTextContent("old|new|true");
  expect(screen.getByText("Restore as NEW version")).toBeVisible();
});
test("sealed experiment cannot reveal before freeze", async () => {
  const ex = {
    id: "e",
    name: "Sealed example",
    config: {},
    runs: {},
    oos_status: "SEALED",
  };
  vi.mocked(api).mockImplementation(async (path: string) =>
    path === "/experiments" ? [ex] : [],
  );
  render(
    <Experiments
      selected={null}
      params={{}}
      settings={{}}
      variantId=""
      dirty={false}
      onRun={() => {}}
    />,
  );
  fireEvent.click(await screen.findByText("Sealed example"));
  expect(screen.getByText("Run / Reveal OOS")).toBeDisabled();
  expect(screen.getByTestId("oos-status")).toHaveTextContent("SEALED");
});

test("off-grid activation interpolates between integer candle coordinates", () => {
  const candles = [
    { time: Date.parse("2024-01-02T15:50Z") / 1000 },
    { time: Date.parse("2024-01-02T15:55Z") / 1000 },
  ];
  expect(annotationX("2024-01-02T15:51Z", candles, (n) => 100 + n * 50)).toBe(
    110,
  );
});
