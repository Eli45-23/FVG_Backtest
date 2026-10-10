import { expect, test, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import StructureReport from "../src/StructureReport";
import { api } from "../src/api";
vi.mock("../src/api", () => ({ api: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
test("verified study offers results and every primary trade", async () => {
  vi.mocked(api).mockResolvedValue({ ready: true, events: 1584 });
  render(<StructureReport />);
  expect(
    await screen.findByText(/1,584 causal breakouts/),
  ).toBeInTheDocument();
  expect(
    screen.getByRole("link", { name: /Open breakout results/ }),
  ).toHaveAttribute(
    "href",
    "/api/research/structure-continuation/files/study.html",
  );
  expect(
    screen.getByRole("link", { name: /every primary trade/ }),
  ).toBeInTheDocument();
});
test("unfinished study never offers a result link", async () => {
  vi.mocked(api).mockResolvedValue({ ready: false });
  render(<StructureReport />);
  expect(
    await screen.findByText(/not completed verification/),
  ).toBeInTheDocument();
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
});
