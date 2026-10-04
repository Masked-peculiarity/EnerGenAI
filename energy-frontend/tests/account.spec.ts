import { test, expect } from "@playwright/test";
import { email, mockAccount } from "./auth-fixture";

test("app opens at login, login shows profile, settings sync and logout guards routes",async({page})=>{
  await mockAccount(page);
  await page.goto("/");
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading",{name:"Log in",exact:true})).toBeVisible();
  await page.getByLabel("Email",{exact:true}).fill(email);
  await page.getByLabel("Password",{exact:true}).fill("ExamplePassword123");
  await page.getByRole("button",{name:"Log in",exact:true}).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.getByRole("button",{name:"Open profile menu"}).click();
  await expect(page.getByRole("menuitem",{name:"User details"})).toBeVisible();
  await page.getByRole("menuitem",{name:"User details"}).click();
  await expect(page.getByRole("dialog")).toContainText(email);
  await page.getByRole("dialog").getByRole("button",{name:"Close",exact:true}).click();
  await page.getByRole("button",{name:"Open profile menu"}).click();
  await page.screenshot({path:"../energy-backend/runtime/screenshots/profile-menu.png"});
  await page.getByRole("menuitem",{name:"Settings",exact:true}).click();
  await page.getByRole("dialog").getByLabel("Rate per kWh (your currency)").fill("9");
  await page.getByRole("dialog").getByLabel("Grid factor (kg CO2 / kWh)").fill("0.4");
  await page.getByRole("button",{name:"Save settings"}).click();
  await expect(page.getByRole("dialog")).toBeHidden();
  await expect(page.getByLabel("Rate per kWh (your currency)")).toHaveValue("9");
  await expect(page.getByLabel("Grid factor (kg CO2 / kWh)")).toHaveValue("0.4");
  await page.reload();
  await expect(page.getByRole("button",{name:"Open profile menu"})).toBeVisible();
  await page.getByRole("button",{name:"Open profile menu"}).click();
  await page.getByRole("menuitem",{name:"Log out"}).click();
  await expect(page).toHaveURL(/\/login$/);
  expect(await page.evaluate(()=>localStorage.getItem("token"))).toBeNull();
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/login$/);
});

test("creating an account logs in automatically",async({page})=>{
  await mockAccount(page);
  await page.goto("/signup");
  await page.getByLabel("Email",{exact:true}).fill(email);
  await page.getByLabel("Password",{exact:true}).fill("ExamplePassword123");
  await page.getByRole("button",{name:"Sign Up",exact:true}).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("button",{name:"Open profile menu"})).toBeVisible();
});

test("profile menu works on mobile",async({page})=>{
  await mockAccount(page,true);
  await page.setViewportSize({width:390,height:844});
  await page.goto("/dashboard");
  await page.getByRole("button",{name:"Open profile menu"}).click();
  await expect(page.getByRole("menuitem",{name:"Settings",exact:true})).toBeVisible();
  await page.screenshot({path:"../energy-backend/runtime/screenshots/profile-mobile.png"});
});
