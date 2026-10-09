import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { test, expect, vi, afterEach } from "vitest";
import AcceptedZoneLabeler from "../src/AcceptedZoneLabeler";
import { api } from "../src/api";
vi.mock("../src/api", () => ({ api: vi.fn() }));
vi.mock("../src/TradeInspector", () => ({
  CandleChart: ({ data }: any) => (
    <div data-testid="accepted-chart">{JSON.stringify(data.annotations)}</div>
  ),
}));
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});
const coll = {
  identity: { calendar: "MNQ_GLOBEX_HISTORICAL_SESSION_CALENDAR_V1" },
  completed: [],
  provider_review_unlocked: false,
  samples: [{ sample_id: "s", kind: "BLIND", ny_date: "2020-02-03" }],
};
const win = {
  sample_id: "s",
  kind: "BLIND",
  confirmation: "2020-02-04T15:00Z",
  choices: [{ index: 4, bar_id: "b", time: "2020-02-04 02:00 NY" }],
  chart: { candles: [], annotations: [] },
  annotations_saved: [],
  proposal: null,
};
function setup() {
  vi.mocked(api).mockImplementation(async (p: any) =>
    p.endsWith("/collection")
      ? coll
      : p.includes("/window/")
        ? win
        : { annotation_id: "human" },
  );
  render(<AcceptedZoneLabeler />);
}
test("blind chart has no provider rectangle and provider review is gated", async () => {
  setup();
  await screen.findByText("Open frozen window");
  fireEvent.click(screen.getByText("Open frozen window"));
  expect(await screen.findByTestId("accepted-chart")).toHaveTextContent("[]");
  expect(screen.queryByText("Provider proposal")).toBeNull();
  expect(screen.getByRole("option", { name: /B — Provider/ })).toBeDisabled();
});
test("explicit no-zone can be saved without selecting an invented base", async () => {
  setup();
  await screen.findByText("Open frozen window");
  fireEvent.click(screen.getByText("Open frozen window"));
  await screen.findByTestId("accepted-chart");
  fireEvent.change(screen.getByLabelText("Accepted human decision"), {
    target: { value: "NOT_A_ZONE" },
  });
  fireEvent.click(screen.getByText("Save human annotation"));
  await screen.findByRole("status");
  expect(
    vi
      .mocked(api)
      .mock.calls.some(
        ([p, b]: any) =>
          p.endsWith("/annotations") &&
          b.label === "NOT_A_ZONE" &&
          b.selection === null,
      ),
  ).toBe(true);
});
test("positive human labels require approved fresh rectangle", async () => {
  setup();
  await screen.findByText("Open frozen window");
  fireEvent.click(screen.getByText("Open frozen window"));
  await screen.findByTestId("accepted-chart");
  fireEvent.change(screen.getByLabelText("Accepted human decision"), {
    target: { value: "VALID_SUPPLY" },
  });
  expect(screen.getByText("Save human annotation")).toBeDisabled();
});

test("provider review has separate decisions after blind gate unlocks", async () => {
  vi.mocked(api).mockImplementation(async (p: any) =>
    p.endsWith("/collection")
      ? {
          ...coll,
          provider_review_unlocked: true,
          samples: [
            ...coll.samples,
            { sample_id: "r", kind: "PROVIDER_REVIEW", ny_date: "2020-02-03" },
          ],
        }
      : {
          ...win,
          sample_id: "r",
          kind: "PROVIDER_REVIEW",
          identity: { provider_configuration: { base_max: 3 } },
          proposal: {
            zone_id: "z",
            zone_type: "SUPPLY",
            base_timestamps: ["2020-02-04T07:00Z"],
            availability_timestamp: "2020-02-04T15:00Z",
            top: 105,
            bottom: 100,
          },
        },
  );
  render(<AcceptedZoneLabeler />);
  await screen.findByText("Open frozen window");
  fireEvent.change(screen.getByLabelText("Collection mode"), {
    target: { value: "PROVIDER_REVIEW" },
  });
  fireEvent.click(screen.getByText("Open frozen window"));
  await screen.findByText("Provider proposal");
  expect(
    screen.getByRole("option", { name: "ACCEPT_ZONE_WRONG_BASE" }),
  ).toBeInTheDocument();
  expect(
    screen.getByText("Provider configuration identity"),
  ).toBeInTheDocument();
});
