import { test, expect } from "@playwright/test";

// Only the verified Development artifact endpoint reaches the live API.
// Unrelated app lists are mocked so this smoke test never loads reserved outcomes.
test("eight-level Development report, filters, chart audits and exports", async ({ page, context }) => {
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  await context.route("**/api/**", async route => {
    if (route.request().url().includes("/api/research/eight-level-study")) {
      await route.continue();
    } else {
      await route.fulfill({ json: route.request().url().endsWith("/data") ? { datasets: [] } : [] });
    }
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Research", exact: true }).click();
  await expect(page.getByText(/88,911 entry observations/)).toBeVisible();
  const popup = context.waitForEvent("page");
  await page.getByRole("link", { name: /Open results, entry comparisons/ }).click();
  const result = await popup;
  result.on("pageerror", e => errors.push(e.message));
  await expect(result.locator("#evidence tbody tr")).toHaveCount(1);
  await result.locator("#level").selectOption("O15L");
  await result.locator("#direction").selectOption("DOWN");
  await result.locator("#entry").selectOption("BREAK_NEXT_FULL_HOLD");
  await result.locator("#horizon").selectOption("60");
  await expect(result.locator("#outcomes tbody tr")).toHaveCount(7);
  await expect(result.locator("#years tbody tr")).toHaveCount(4);
  await expect(result.locator("#evidence")).toContainText("95% CI low");
  await expect(result.locator("#evidence")).toContainText("BH q-value");
  await expect(result.locator("#evidence")).toContainText("Baseline %");
  await result.getByRole("button", { name: "Reset view" }).click();
  await expect(result.locator("#level")).toHaveValue("PDH");
  await expect(result.locator("#horizon")).toHaveValue("30");
  const charts = await result.locator("#chart option").evaluateAll(options => options.map(o => (o as HTMLOptionElement).value));
  expect(charts).toHaveLength(32);
  for (const chart of charts) {
    await result.locator("#chart").selectOption(chart);
    await expect(result.locator("#chartimg")).toHaveAttribute("src", chart);
    await expect.poll(() => result.locator("#chartimg").evaluate((i: HTMLImageElement) => i.complete && i.naturalWidth > 0)).toBeTruthy();
  }
  await result.locator("#chart").selectOption(charts[0]);
  for (const name of ["All primary evidence CSV", "Summary JSON", "Report bundle"]) {
    const download = result.waitForEvent("download");
    await result.getByRole("link", { name, exact: true }).click();
    expect(await (await download).failure()).toBeNull();
  }
  await result.screenshot({ path: "../work/eight-level-viewer.png", fullPage: true });
  expect(errors).toEqual([]);
});
