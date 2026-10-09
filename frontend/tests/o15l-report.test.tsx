import { expect, test, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import O15lReport from "../src/O15lReport";
import { api } from "../src/api";
vi.mock("../src/api", () => ({ api: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
test("verified study offers results and every primary trade", async () => {
  vi.mocked(api).mockResolvedValue({ ready: true, events: 3745 });
  render(<O15lReport />);
  expect(
    await screen.findByText(/3,745 causal confirmations/),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("link", { name: /Open clearance-and-hold results/ }),
  ).toHaveAttribute(
    "href",
    "/api/research/o15l-clear-hold/files/study.html",
  );
  expect(
    screen.getByRole("link", { name: /every primary trade/ }),
  ).toBeInTheDocument();
});
test("unfinished study never offers a result link", async () => {
  vi.mocked(api).mockResolvedValue({ ready: false });
  render(<O15lReport />);
  expect(
    await screen.findByText(/not completed verification/),
  ).toBeInTheDocument();
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
});
