import { test, expect } from "@playwright/test";
test("combination evidence, filters and complete exports", async ({
  page,
  context,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await context.route("**/api/**", async (route) => {
    if (route.request().url().includes("/api/research/level-combinations"))
      await route.continue();
    else
      await route.fulfill({
        json: route.request().url().endsWith("/data") ? { datasets: [] } : [],
      });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Research", exact: true }).click();
  await expect(page.getByText(/36,400 entry records/)).toBeVisible();
  const popup = context.waitForEvent("page");
  await page
    .getByRole("link", { name: "Open level-combination evidence" })
    .click();
  const result = await popup;
  result.on("pageerror", (e) => errors.push(e.message));
  await expect(result.locator("#tab0 tbody tr")).toHaveCount(32);
  await result.locator("#level").selectOption("PDH");
  await result.locator("#direction").selectOption("DOWN");
  await expect(result.locator("#tab0 tbody tr:visible")).toHaveCount(2);
  await result
    .getByRole("button", { name: "Clear filters", exact: true })
    .click();
  await expect(result.locator("#tab0 tbody tr:visible")).toHaveCount(32);
  await result
    .getByRole("button", { name: "Waiting opportunities", exact: true })
    .click();
  await expect(result.locator("#tab1 tbody tr")).toHaveCount(16);
  await expect(result.locator("#tab1")).toContainText("Original opportunities");
  for (const name of [
    "study_summary.json",
    "statistical_evidence.csv",
    "study_bundle.zip",
  ]) {
    const p = result.waitForEvent("download");
    await result.getByRole("link", { name, exact: true }).click();
    expect(await (await p).failure()).toBeNull();
  }
  await result.evaluate(() => window.scrollTo(0, 0));
  await result.screenshot({
    path: "../work/level-combination-viewer.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
});
