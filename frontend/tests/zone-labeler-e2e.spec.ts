import { test, expect } from "@playwright/test";
test("isolated Development label, freeze, provider comparison and export", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Zone Labeler", exact: true }).click();
  await expect(page.locator("canvas").first()).toBeVisible();
  await expect(
    page.getByText(/PROVISIONAL_PENDING_HUMAN_GROUND_TRUTH/),
  ).toBeVisible();
  await page.getByLabel("Saved seed").fill("42");
  const loaded = page.waitForResponse(
    (r) =>
      r.url().includes("/zone-labels/candidate?mode=random") &&
      r.status() === 200,
  );
  await page
    .getByRole("button", { name: "Random Development candidate" })
    .click();
  await loaded;
  await expect(
    page.getByRole("button", { name: "Random Development candidate" }),
  ).toBeEnabled();
  await expect(page.locator("canvas").first()).toBeVisible();
  await page
    .getByLabel(
      "I confirm departure candles are excluded from the selected base",
    )
    .check();
  await page
    .getByLabel("Annotation notes")
    .fill("SYNTHETIC BROWSER WORKFLOW — not human ground truth");
  await page.getByRole("button", { name: "Save immutable annotation" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Annotation saved immutably",
  );
  await page
    .getByRole("button", { name: "Freeze labels and compare provider" })
    .click();
  await expect(
    page.getByText("Reviewed-opportunity agreement — not trading evidence"),
  ).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export comparison JSON" }).click();
  expect((await download).suggestedFilename()).toBe("zone-ground-truth.json");
  await page.screenshot({
    path: "../work/zone-ground-truth-v1/labeler-browser.png",
    fullPage: true,
  });
});
