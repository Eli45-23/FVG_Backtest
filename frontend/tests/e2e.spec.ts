import { test, expect } from "@playwright/test";
test("clone, edit inputs, validate, run, inspect, compare and sweep", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page.getByRole("button", { name: "Strategies", exact: true }).click();
  await page
    .getByRole("button", { name: /CONT-A Second Candle/ })
    .first()
    .click();
  await expect(page.getByRole("status")).toContainText("Validation passed", {
    timeout: 20000,
  });
  await expect(page.locator(".monaco-editor").first()).toBeVisible();
  page.once("dialog", (d) => d.accept("E2E CONT-A clone"));
  await page.getByRole("button", { name: "Clone", exact: true }).click();
  await expect(page.getByLabel("Strategy name")).toHaveValue(
    "E2E CONT-A clone",
  );
  await page.getByRole("button", { name: "Validate", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Validation passed");
  await page
    .getByLabel("Maximum structural risk (0 = disabled)", { exact: true })
    .fill("75");
  await page.getByLabel("start date", { exact: true }).fill("2024-02-05");
  await page.getByLabel("end date", { exact: true }).fill("2024-02-09");
  await page.getByRole("button", { name: "Run Backtest", exact: true }).click();
  await expect(page.locator(".badge")).toHaveText("completed", {
    timeout: 90000,
  });
  await expect(page.getByText("Net P&L", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Monthly", exact: true }).click();
  await expect(
    page.getByRole("cell", { name: "2024-02", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Inspect trades", exact: true })
    .click();
  await expect(page.getByText(/matching trades/)).toBeVisible();
  await page.getByRole("button", { name: "Runs", exact: true }).click();
  await page
    .getByRole("button", { name: "Clone selected run configuration" })
    .click();
  await expect(page.locator(".badge")).toHaveText("completed", {
    timeout: 90000,
  });
  await page.getByRole("button", { name: "Compare", exact: true }).click();
  const boxes = page.locator(".choices input");
  await boxes.nth(0).check();
  await boxes.nth(1).check();
  await page.getByRole("button", { name: "Compare selected" }).click();
  await expect(page.getByText("Exact configuration differences")).toBeVisible();
  await expect(page.locator(".chart").first()).toBeVisible();
  await page.screenshot({
    path: "../work/platform-compare.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Sweeps", exact: true }).click();
  await page.getByLabel("Sweep values").fill("75,100");
  await page.getByRole("button", { name: "Run sweep", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: /E2E CONT-A clone · max_risk/ }),
  ).toBeVisible({ timeout: 30000 });
  await page.getByRole("button", { name: "Strategies", exact: true }).click();
  await expect(page.locator(".view-lines")).toContainText("on_bar");
  await page.screenshot({
    path: "../work/platform-editor.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
test("new source validates and runs without changing backend", async ({
  page,
}) => {
  await page.goto("/");
  page.once("dialog", (d) => d.accept("E2E new concept"));
  await page.getByRole("button", { name: "New strategy", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Validation passed", {
    timeout: 20000,
  });
  const editor = page.locator(".monaco-editor textarea").first();
  await editor.focus();
  await page.keyboard.press(
    process.platform === "darwin" ? "Meta+A" : "Control+A",
  );
  await page.context().grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.evaluate(
    (text) => navigator.clipboard.writeText(text),
    "from engine.strategy import Entry\nclass Strategy:\n    name = 'New concept'\n    def on_bar(self, ctx, p):\n        if ctx.bar.time == '09:45':\n            return Entry('LONG', ctx.bar.low - ctx.tick_size)\n        return None\n",
  );
  await page.keyboard.press(
    process.platform === "darwin" ? "Meta+V" : "Control+V",
  );
  await page.getByRole("button", { name: "Save", exact: true }).click();
  await expect(page.getByRole("status")).toContainText(
    "Saved immutable version 2",
  );
  await page.getByRole("button", { name: "Validate", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Validation passed");
  await page.getByLabel("start date", { exact: true }).fill("2024-02-05");
  await page.getByLabel("end date", { exact: true }).fill("2024-02-07");
  await page.getByRole("button", { name: "Run Backtest", exact: true }).click();
  await expect(page.locator(".badge")).toHaveText("completed", {
    timeout: 90000,
  });
  await expect(page.locator(".kpis")).toContainText("2");
  await page.screenshot({
    path: "../work/platform-results.png",
    fullPage: true,
  });
});
