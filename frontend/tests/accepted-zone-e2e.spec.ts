import { test, expect } from "@playwright/test";
test("isolated accepted-calendar blind collection and immutable export", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Zone Labeler", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Accepted-calendar Ground Truth" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Open frozen window", exact: true })
    .click();
  await expect(page.locator("canvas").first()).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Provider proposal" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("option", { name: /B — Provider/ }),
  ).toHaveAttribute("disabled", "");
  await page.getByLabel("Accepted human decision").selectOption("NOT_A_ZONE");
  await page
    .getByLabel("Accepted annotation notes")
    .fill("AUTOMATED ISOLATED WORKFLOW TEST — NOT HUMAN GROUND TRUTH");
  await page
    .getByRole("button", { name: "Save human annotation", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "Human annotation saved",
  );
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export immutable snapshot" }).click();
  expect((await download).suggestedFilename()).toBe(
    "accepted-zone-human-labels.json",
  );
  await page
    .getByRole("button", { name: "Collection status / comparison" })
    .click();
  await expect(
    page.getByText("INSUFFICIENT_HUMAN_LABELS", { exact: true }).first(),
  ).toBeVisible();
  await page.screenshot({
    path: "../work/zone-ground-truth-v2-calendar-accepted/isolated-browser.png",
    fullPage: true,
  });
});
