import { expect, test, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import LevelStudyReport from "../src/LevelStudyReport";
import { api } from "../src/api";
vi.mock("../src/api", () => ({ api: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
test("verified study offers results and corrected evidence", async () => {
  vi.mocked(api).mockResolvedValue({ ready: true, events: 88911 });
  render(<LevelStudyReport />);
  expect(
    await screen.findByText(/88,911 entry observations/),
  ).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Open results/ })).toHaveAttribute(
    "href",
    "/api/research/eight-level-study/files/study.html",
  );
  expect(
    screen.getByRole("link", { name: /corrected evidence/ }),
  ).toBeInTheDocument();
});
test("unfinished study never offers a result link", async () => {
  vi.mocked(api).mockResolvedValue({ ready: false });
  render(<LevelStudyReport />);
  expect(
    await screen.findByText(/not completed verification/),
  ).toBeInTheDocument();
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
});
