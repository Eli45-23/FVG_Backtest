import { test, expect } from "@playwright/test";
test("managed run, candle inspector and activation overlays", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await page.getByRole("button", { name: "Strategies", exact: true }).click();
  await page
    .getByRole("button", { name: /CONT-A Quality R-Step/ })
    .first()
    .click();
  await expect(page.getByRole("status")).toContainText("Validation passed", {
    timeout: 20000,
  });
  await page.getByRole("button", { name: "Run Backtest", exact: true }).click();
  await expect(page.locator(".badge").first()).toHaveText("completed", {
    timeout: 90000,
  });
  const rid = await page.getByLabel("Selected run").inputValue();
  const trades = await (
    await request.get(`/api/backtests/${rid}/trades`)
  ).json();
  const chosen = trades.find(
    (t: any) => t.direction === "LONG" && t.management_event_count > 0,
  );
  expect(chosen).toBeTruthy();
  await page.getByRole("button", { name: "Management", exact: true }).click();
  await expect(
    page.getByRole("cell", { name: "management_exit_count", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Inspect trades", exact: true })
    .click();
  await page.getByLabel("direction", { exact: true }).selectOption("LONG");
  await page
    .getByRole("row")
    .filter({ hasText: chosen.entry_time_ny.slice(0, 10) })
    .first()
    .click();
  await expect(page.locator(".candle-chart canvas").first()).toBeVisible();
  await expect(page.locator(".candle-overlay")).toContainText("+50 touch");
  await page.getByRole("button", { name: "Full session", exact: true }).click();
  await expect(page.locator(".candle-chart canvas").first()).toBeVisible();
  await page.screenshot({ path: "../work/v11-inspector.png", fullPage: true });
  await page.getByRole("button", { name: "Next Trade", exact: true }).click();
  await expect(page.locator(".candle-chart canvas").first()).toBeVisible();
  await page
    .getByRole("button", { name: "Previous Trade", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Back to Trades", exact: true })
    .click();
  await expect(page.getByLabel("direction", { exact: true })).toHaveValue(
    "LONG",
  );
  expect(errors).toEqual([]);
});

test("source versions diff, historical clone and append-only restore", async ({
  page,
  request,
}) => {
  const template = await (await request.get("/api/template")).json();
  const st = await (
    await request.post("/api/strategies", {
      data: { name: "Version browser smoke", source: template.source },
    })
  ).json();
  await request.put(`/api/strategies/${st.id}`, {
    data: {
      name: st.name,
      source: template.source + "\n# browser version two",
    },
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Strategies", exact: true }).click();
  await page
    .getByRole("button", { name: /Version browser smoke/ })
    .first()
    .click();
  await page.getByRole("button", { name: "Versions", exact: true }).click();
  await expect(page.locator(".monaco-diff-editor")).toBeVisible();
  await page.getByLabel("Historical version").selectOption(st.version_id);
  page.once("dialog", (d) => d.accept());
  await page.getByRole("button", { name: "Restore as NEW version" }).click();
  await expect(page.getByRole("status")).toContainText("Validation passed", {
    timeout: 20000,
  });
  const versions = await (
    await request.get(`/api/strategies/${st.id}/versions`)
  ).json();
  expect(versions.map((v: any) => v.number)).toEqual([3, 2, 1]);
  expect(versions[2].source).toBe(template.source);
  await page.getByRole("button", { name: "Versions", exact: true }).click();
  await page.getByLabel("Historical version").selectOption(st.version_id);
  page.once("dialog", (d) => d.accept("Historical clone smoke"));
  await page.getByRole("button", { name: "Clone this version" }).click();
  await expect(page.getByLabel("Strategy name")).toHaveValue(
    "Historical clone smoke",
  );
});

test("development validation freeze and explicit OOS reveal", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Strategies", exact: true }).click();
  await page
    .getByRole("button", { name: /CONT-A Second Candle/ })
    .first()
    .click();
  await expect(page.getByRole("status")).toContainText("Validation passed", {
    timeout: 20000,
  });
  await page.getByRole("button", { name: "Experiments", exact: true }).click();
  await page.getByText("Create Research Split", { exact: true }).click();
  await page.getByLabel("Split name", { exact: true }).fill("Browser split");
  for (const [segment, start, end] of [
    ["development", "2024-03-04", "2024-03-05"],
    ["validation", "2024-03-05", "2024-03-06"],
    ["out-of-sample", "2024-03-06", "2024-03-07"],
  ]) {
    await page.getByLabel(`${segment} start`, { exact: true }).fill(start);
    await page.getByLabel(`${segment} end`, { exact: true }).fill(end);
  }
  await page.getByRole("button", { name: "Create split", exact: true }).click();
  await page
    .getByRole("button", { name: "Create experiment snapshot", exact: true })
    .click();
  await expect(page.getByTestId("oos-status")).toHaveText("SEALED");
  await expect(
    page.getByRole("button", { name: "Run / Reveal OOS", exact: true }),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Run Development", exact: true })
    .click();
  await expect(
    page
      .getByRole("row")
      .filter({
        has: page.getByRole("cell", { name: "development", exact: true }),
      }),
  ).toContainText("completed", { timeout: 90000 });
  await page
    .getByRole("button", { name: "Run Validation", exact: true })
    .click();
  await expect(
    page
      .getByRole("row")
      .filter({
        has: page.getByRole("cell", { name: "validation", exact: true }),
      }),
  ).toContainText("completed", { timeout: 90000 });
  await page
    .getByRole("button", { name: "Freeze for Out-of-Sample", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Run / Reveal OOS", exact: true }),
  ).toBeEnabled();
  page.once("dialog", (d) => d.accept());
  await page
    .getByRole("button", { name: "Run / Reveal OOS", exact: true })
    .click();
  await expect(page.getByTestId("oos-status")).toHaveText("REVEALED");
  await expect(
    page
      .getByRole("row")
      .filter({
        has: page.getByRole("cell", { name: "out-of-sample", exact: true }),
      }),
  ).toContainText("completed", { timeout: 90000 });
  await page
    .getByRole("button", { name: "Combined revealed segments" })
    .click();
  await expect(page.getByText(/not an independent backtest/)).toBeVisible();
  await page.screenshot({ path: "../work/v11-experiment.png", fullPage: true });
});
