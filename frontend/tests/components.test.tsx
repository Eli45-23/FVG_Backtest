import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { Inputs, Table, KPIs } from "../src/components";
afterEach(cleanup);
describe("research components", () => {
  it("renders discovered input and changes configuration", () => {
    const change = vi.fn();
    render(
      <Inputs
        inputs={[
          {
            id: "risk",
            label: "Maximum Risk",
            type: "float",
            default: 100,
            min: 0,
            step: 0.25,
          },
        ]}
        values={{}}
        onChange={change}
      />,
    );
    fireEvent.change(screen.getByLabelText("Maximum Risk"), {
      target: { value: "75" },
    });
    expect(change).toHaveBeenCalledWith({ risk: 75 });
  });
  it("renders boolean and choice controls", () => {
    const change = vi.fn();
    render(
      <Inputs
        inputs={[
          { id: "flag", label: "Exclude", type: "bool", default: false },
          {
            id: "mode",
            label: "Mode",
            type: "choice",
            default: "a",
            choices: ["a", "b"],
          },
        ]}
        values={{}}
        onChange={change}
      />,
    );
    fireEvent.click(screen.getByLabelText("Exclude"));
    expect(change).toHaveBeenCalledWith({ flag: true });
    expect(screen.getByRole("option", { name: "b" })).toBeInTheDocument();
  });
  it("displays result metrics with null PF", () => {
    render(
      <KPIs
        m={{
          net_pnl_usd: 123,
          profit_factor: null,
          average_r: 0.5,
          win_rate_percent: 50,
          trades: 2,
          max_closed_trade_drawdown_usd: 10,
        }}
      />,
    );
    expect(screen.getByText("$123.00")).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument();
  });
  it("sorts result table and opens run", () => {
    const click = vi.fn();
    render(
      <Table
        rows={[
          { id: "a", name: "Z", trades: 5 },
          { id: "b", name: "A", trades: 2 },
        ]}
        columns={["name", "trades"]}
        onRow={click}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /name/ }));
    expect(screen.getAllByRole("row")[1]).toHaveTextContent("A");
    fireEvent.click(screen.getByText("Z"));
    expect(click).toHaveBeenCalledWith({ id: "a", name: "Z", trades: 5 });
  });
  it("shows empty result honestly", () => {
    render(<Table rows={[]} />);
    expect(
      screen.getByText("No records for this selection."),
    ).toBeInTheDocument();
  });
});
