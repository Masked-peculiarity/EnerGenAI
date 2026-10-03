import { test, expect } from "@playwright/test";
import { mockAccount } from "./auth-fixture";

test.beforeEach(async({page})=>{await mockAccount(page,true);});
test("conditions predictor uses held-out actuals and resets comparisons after edits",async({page})=>{
  await page.goto("/predict");
  await expect(page.getByRole("heading",{name:"Energy consumption predictor"})).toBeVisible();
  await page.getByRole("button",{name:"Load held-out example"}).click();
  await page.getByRole("button",{name:"Predict consumption",exact:true}).click();
  await expect(page.getByTestId("prediction-value")).toContainText("Wh per 10-minute interval");
  await expect(page.getByText("Held-out actual:",{exact:false})).toBeVisible();
  await expect(page.getByText("Weak predictive skill:",{exact:false})).toBeVisible();
  await page.getByLabel("Average room temperature (°C)").fill("24");
  await expect(page.getByTestId("prediction-value")).toHaveCount(0);
  await page.getByRole("button",{name:"Predict consumption",exact:true}).click();
  await expect(page.getByTestId("prediction-value")).toBeVisible();
  await expect(page.getByText("Held-out actual:",{exact:false})).toHaveCount(0);
  await page.screenshot({path:"../energy-backend/runtime/screenshots/predict-conditions.png",fullPage:true});
});
test("home profile predicts annual energy and explicitly labels monthly average",async({page})=>{
  await page.goto("/predict");
  await page.getByRole("button",{name:"Home profile",exact:true}).click();
  await page.getByRole("button",{name:"Load held-out example"}).click();
  await page.getByRole("button",{name:"Predict consumption",exact:true}).click();
  await expect(page.getByTestId("prediction-value")).toContainText("kWh per year");
  await expect(page.getByText("Annual estimate ÷ 12:",{exact:false})).toBeVisible();
  await expect(page.getByText("Absolute error for this example:",{exact:false})).toBeVisible();
  await page.screenshot({path:"../energy-backend/runtime/screenshots/predict-home.png",fullPage:true});
});
test("prediction inputs and results fit a mobile screen",async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await page.goto("/predict");
  await page.getByRole("button",{name:"Home profile",exact:true}).click();
  await page.getByRole("button",{name:"Load held-out example"}).click();
  await page.getByRole("button",{name:"Predict consumption",exact:true}).click();
  await expect(page.getByTestId("prediction-value")).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
  await page.screenshot({path:"../energy-backend/runtime/screenshots/predict-mobile.png",fullPage:true});
});
