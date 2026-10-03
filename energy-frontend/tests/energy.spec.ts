import { test, expect } from "@playwright/test";
import { mockAccount } from "./auth-fixture";
test.beforeEach(async ({page},info) => {
  if(!info.title.startsWith("private bills")) await mockAccount(page,true);
});

test("dashboard loads real KPIs and configurable costs", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/dashboard");
  await expect(page.getByText("Selected-period appliances", { exact: true })).toBeVisible();
  await expect(page.getByText("109/144 intervals recorded", { exact: false })).toBeVisible();
  await page.getByLabel("Rate per kWh (your currency)").fill("8");
  await expect(page.getByText("Recorded hourly energy", { exact: true })).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.locator(".recharts-surface").first()).toBeVisible();
  await page.screenshot({ path: "../energy-backend/runtime/screenshots/dashboard.png", fullPage: true });
  expect(errors).toEqual([]);
});

test("forecast supports both horizons and historical actual comparison", async ({ page }) => {
  await page.goto("/forecast");
  await expect(page.getByText("Next-hour forecast", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Next 24 hours" }).click();
  await expect(page.getByText("Next-day forecast", { exact: true })).toBeVisible();
  await expect(page.getByText("The negative R", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Next hour", exact: true }).click();
  await page.getByLabel("Historical origin (optional)").fill("2016-05-20T12:00");
  await expect(page.getByText("60 minutes after 2016-05-20 12:00", { exact: true })).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await page.screenshot({ path: "../energy-backend/runtime/screenshots/forecast.png", fullPage: true });
});

test("anomalies expose evidence and training coverage", async ({ page }) => {
  await page.goto("/anomalies");
  await expect(page.getByText("Residual threshold", { exact: true })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Evidence", exact: true })).toBeVisible();
  await page.screenshot({ path: "../energy-backend/runtime/screenshots/anomalies.png", fullPage: true });
  await page.getByLabel("From", { exact: true }).fill("2016-01-13");
  await page.getByLabel("Until (exclusive)", { exact: true }).fill("2016-01-14");
  await expect(page.getByText("No held-out intervals are evaluated in this range.", { exact: true })).toBeVisible();
});

test("copilot returns computed tools and cited guidance", async ({ page }) => {
  await page.goto("/copilot");
  await page.getByLabel("Energy question").fill("Why was usage high yesterday?");
  await page.getByRole("button", { name: "Send question", exact: true }).click();
  await expect(page.getByText("Tools: Energy summary", { exact: false })).toBeVisible({ timeout: 55000 });
  await expect(page.getByText("Retrieval:", { exact: false })).toBeVisible();
  await page.getByLabel("Energy question").fill("How can LED lighting reduce energy consumption?");
  await page.getByRole("button", { name: "Send question", exact: true }).click();
  await expect(page.getByRole("link", { name: /LED/i }).first()).toBeVisible({ timeout: 55000 });
  await page.screenshot({ path: "../energy-backend/runtime/screenshots/copilot.png", fullPage: true });
});

test("private bills and prediction page require login", async ({ page }) => {
  await page.goto("/bills");
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/predict");
  await expect(page).toHaveURL(/\/login$/);
});
