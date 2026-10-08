import { test, expect } from "@playwright/test";

test("columnar development study: numeric buckets, compound filters, statistics and overlays", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page
    .getByRole("button", { name: "Event Studies", exact: true })
    .click();
  await page.getByLabel("Study name").fill("Upgrade columnar development");
  await page.getByLabel("Study start").fill("2020-01-06");
  await page.getByLabel("Study end").fill("2020-01-08");
  await page
    .getByText("Numeric ranges and saved buckets", { exact: true })
    .click();
  await page.getByLabel("Add numeric measurement").selectOption("atr14");
  await page.getByLabel("atr14 min").fill("0");
  await page.getByLabel("atr14 edges").fill("10, 25, 50");
  await page.getByLabel("Study name").click();
  await page
    .getByRole("button", { name: "Create Event Study", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Date-clustered matched evidence" }),
  ).toBeVisible({ timeout: 90000 });
  await page.getByLabel("Research grouping").selectOption("atr14");
  await page.getByLabel("Outcome threshold").selectOption("atr:0.5");
  await expect(page.getByText(/Threshold: 0.5 ATR/)).toBeVisible();
  await page
    .getByLabel("compound_interaction", { exact: true })
    .selectOption("BREAK_NEXT_CANDLE_CLOSE_HOLD");
  await expect(page.locator("tr.clickable").first()).toBeVisible();
  await page.locator("tr.clickable").first().click();
  await expect(page.getByText("Event metadata", { exact: true })).toBeVisible();
  await page.getByRole("checkbox", { name: "indicators", exact: true }).check();
  await expect(page.locator("canvas").first()).toBeVisible();
  await page.screenshot({
    path: "../work/upgrade-research-ui.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});

test("2020 ordinary strategy: multiple entries, MTF and partial execution inspection", async ({
  page,
}) => {
  const source = `from engine.strategy import PositionPlan, TargetLeg
from decimal import Decimal as D
class Strategy:
    def on_bar(self,ctx,p):
        if ctx.bar.time in ('09:35','10:00'):
            assert ctx.frames['1m'].timestamp < ctx.timestamp
            return PositionPlan('LONG',ctx.bar.close-D('2'),legs=(TargetLeg(1,D('1'),'TP1'),TargetLeg(1,None,'runner')),break_even_after_tp1=True)
`;
  const created = await page.request.post("/api/strategies", {
    data: { name: "Browser partial capability", source },
  });
  expect(created.ok()).toBeTruthy();
  await page.goto("/");
  await page.getByRole("button", { name: "Strategies", exact: true }).click();
  await page
    .getByRole("button", { name: /Browser partial capability/ })
    .first()
    .click();
  await expect(page.getByRole("status")).toContainText("Validation passed");
  await page
    .getByLabel("Dataset profile", { exact: true })
    .selectOption("research_2020_2026");
  await page.getByLabel("Execution mode").selectOption("extended_v1");
  await page.getByLabel("Maximum trades per day").selectOption("3");
  await page.getByLabel("quantity", { exact: true }).fill("2");
  await page.getByLabel("start date", { exact: true }).fill("2020-01-06");
  await page.getByLabel("end date", { exact: true }).fill("2020-01-07");
  await page.getByRole("button", { name: "Run Backtest", exact: true }).click();
  await expect(page.locator(".badge")).toHaveText("completed", {
    timeout: 90000,
  });
  await page
    .getByRole("button", { name: "Inspect trades", exact: true })
    .click();
  await page.locator("tr.clickable").first().click();
  await expect(
    page.getByRole("heading", { name: "Partial execution history" }),
  ).toBeVisible();
  await page.screenshot({
    path: "../work/upgrade-partial-ui.png",
    fullPage: true,
  });
});
