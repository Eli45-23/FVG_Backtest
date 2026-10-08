import { render, screen, fireEvent } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import ExecutionSettings from "../src/ExecutionSettings";
import NumericResearch from "../src/NumericResearch";

test("execution controls preserve default and opt into sequential execution", () => {
  const change = vi.fn();
  render(
    <ExecutionSettings
      value={{ timeframe: "5m", max_trades_per_day: 1 }}
      onChange={change}
    />,
  );
  expect(screen.getByLabelText("Execution mode")).toHaveValue("legacy_v1");
  fireEvent.change(screen.getByLabelText("Maximum trades per day"), {
    target: { value: "unlimited" },
  });
  expect(change).toHaveBeenLastCalledWith(
    expect.objectContaining({
      max_trades_per_day: null,
      execution_mode: "extended_v1",
    }),
  );
  fireEvent.change(screen.getByLabelText("Primary timeframe"), {
    target: { value: "4h" },
  });
  expect(change).toHaveBeenLastCalledWith(
    expect.objectContaining({ timeframe: "4h", execution_mode: "extended_v1" }),
  );
});
test("numeric controls expose range and bucket configuration", () => {
  const change = vi.fn();
  render(
    <NumericResearch
      value={{ atr14: { min: 5, edges: [10, 25] } }}
      onChange={change}
    />,
  );
  fireEvent.change(screen.getByLabelText("atr14 max"), {
    target: { value: "100" },
  });
  expect(change).toHaveBeenLastCalledWith({
    atr14: { min: 5, max: 100, edges: [10, 25] },
  });
  fireEvent.blur(screen.getByLabelText("atr14 edges"), {
    target: { value: "10, 20, 30" },
  });
  expect(change).toHaveBeenLastCalledWith({
    atr14: { min: 5, edges: [10, 20, 30] },
  });
});
