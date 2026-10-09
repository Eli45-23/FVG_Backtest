import { expect, test, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import FullHoldReport from "../src/FullHoldReport";
import { api } from "../src/api";
vi.mock("../src/api", () => ({ api: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
test("verified study offers results and primary diagnostics", async () => {
  vi.mocked(api).mockResolvedValue({ ready: true, events: 4784 });
  render(<FullHoldReport />);
  expect(
    await screen.findByText(/4,784 causal full-hold signals/),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("link", { name: /Open full-hold comparison/ }),
  ).toHaveAttribute(
    "href",
    "/api/research/full-hold-feasibility/files/study.html",
  );
  expect(
    screen.getByRole("link", { name: /primary diagnostics/ }),
  ).toBeInTheDocument();
});
test("unfinished study never offers a result link", async () => {
  vi.mocked(api).mockResolvedValue({ ready: false });
  render(<FullHoldReport />);
  expect(
    await screen.findByText(/not completed verification/),
  ).toBeInTheDocument();
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
});
