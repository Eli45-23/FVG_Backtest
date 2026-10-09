import { expect, test, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import DownwardBreakReport from "../src/DownwardBreakReport";
import { api } from "../src/api";
vi.mock("../src/api", () => ({ api: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
test("verified study offers results and primary diagnostics", async () => {
  vi.mocked(api).mockResolvedValue({ ready: true, events: 11364 });
  render(<DownwardBreakReport />);
  expect(
    await screen.findByText(/11,364 causal break signals/),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("link", { name: /Open execution feasibility/ }),
  ).toHaveAttribute(
    "href",
    "/api/research/downward-break-feasibility/files/study.html",
  );
  expect(
    screen.getByRole("link", { name: /primary diagnostics/ }),
  ).toBeInTheDocument();
});
test("unfinished study never offers a result link", async () => {
  vi.mocked(api).mockResolvedValue({ ready: false });
  render(<DownwardBreakReport />);
  expect(
    await screen.findByText(/not completed verification/),
  ).toBeInTheDocument();
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
});
