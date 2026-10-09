import { expect, test, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import CombinationReport from "../src/CombinationReport";
import { api } from "../src/api";
vi.mock("../src/api", () => ({ api: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
test("verified combination report links to inspectable evidence", async () => {
  vi.mocked(api).mockResolvedValue({ ready: true, events: 36400 });
  render(<CombinationReport />);
  expect(await screen.findByText(/36,400 entry records/)).toBeInTheDocument();
  expect(
    screen.getByRole("link", { name: "Open level-combination evidence" }),
  ).toHaveAttribute(
    "href",
    "/api/research/level-combinations/files/study.html",
  );
});
test("unverified study is not shown as completed", async () => {
  vi.mocked(api).mockResolvedValue({ ready: false });
  render(<CombinationReport />);
  expect(
    await screen.findByText(/not completed verification/),
  ).toBeInTheDocument();
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
});
