import { test, expect } from "@playwright/test";

test("development event study creation, summaries, chart and export", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Event Studies", exact: true })
    .click();
  await page.getByLabel("Study name").fill("Browser level foundation");
  await page.getByLabel("Study start").fill("2020-01-06");
  await page.getByLabel("Study end").fill("2020-01-08");
  await page
    .getByRole("button", { name: "Create Event Study", exact: true })
    .click();
  await expect(page.getByText(/Forward outcomes ·/)).toBeVisible({
    timeout: 60000,
  });
  await expect(
    page.getByRole("link", { name: "Export full JSON" }),
  ).toBeVisible();
  await page.getByLabel("level_type", { exact: true }).selectOption("O5H");
  await page.locator("tr.clickable").first().click();
  await expect(page.getByText("Event metadata", { exact: true })).toBeVisible();
  await expect(page.locator("canvas").first()).toBeVisible();
  await page.screenshot({
    path: "../work/levels-development-ui.png",
    fullPage: true,
  });
});
