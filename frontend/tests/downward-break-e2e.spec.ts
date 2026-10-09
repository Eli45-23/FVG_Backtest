import { test, expect } from "@playwright/test";

test("downward-break Development diagnostics, yearly stability and exports", async ({
  page,
  context,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await context.route("**/api/**", async (route) => {
    const url = route.request().url();
    if (
      url.includes("/api/research/downward-break-feasibility") ||
      url.includes("/api/research/eight-level-study")
    )
      await route.continue();
    else
      await route.fulfill({
        json: url.endsWith("/data") ? { datasets: [] } : [],
      });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Research", exact: true }).click();
  await expect(page.getByText(/11,364 causal break signals/)).toBeVisible();
  const popup = context.waitForEvent("page");
  await page
    .getByRole("link", { name: "Open execution feasibility and cost results" })
    .click();
  const result = await popup;
  result.on("pageerror", (e) => errors.push(e.message));
  await expect(result.locator("#all tbody tr")).toHaveCount(32);
  await expect(result.locator("#years tbody tr")).toHaveCount(4);
  await expect(result.locator("#costs tbody tr")).toHaveCount(3);
  await result.locator("#level").selectOption("PMH");
  await result.locator("#stop").selectOption("BREAK_CANDLE_HIGH");
  await result.locator("#target").selectOption("2");
  await expect(result.locator("#primary")).toContainText("Average net R");
  await expect(result.locator("#primary")).toContainText("-0.078");
  await result.getByRole("button", { name: "Reset view" }).click();
  await expect(result.locator("#level")).toHaveValue("PDH");
  await expect(result.locator("#stop")).toHaveValue("LEVEL_RECLAIM");
  for (const name of [
    "Primary diagnostics CSV",
    "Summary JSON",
    "Report bundle",
  ]) {
    const download = result.waitForEvent("download");
    await result.getByRole("link", { name, exact: true }).click();
    expect(await (await download).failure()).toBeNull();
  }
  await result.evaluate(() => window.scrollTo(0, 0));
  await result.screenshot({
    path: "../work/downward-break-viewer.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
