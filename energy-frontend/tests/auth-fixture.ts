import { Page } from "@playwright/test";
export const email = "viewer@example.com";
export function testToken() {
  return "test." + Buffer.from(JSON.stringify({ sub: email, exp: Math.floor(Date.now()/1000)+3600 })).toString("base64url") + ".test";
}
// Browser-only auth fixtures. Real JWT validation/account isolation is tested by pytest.
export async function mockAccount(page: Page, authenticated=false) {
  await page.route("**/api/**", async route => {
    const path=new URL(route.request().url()).pathname;
    if(path==="/api/auth/me") return route.fulfill({json:{email}});
    if(path==="/api/auth/login") return route.fulfill({json:{token:testToken()}});
    if(path==="/api/auth/signup") return route.fulfill({status:201,json:{msg:"Account created successfully"}});
    const headers={...route.request().headers()};
    delete headers.authorization;
    return route.continue({headers});
  });
  if(authenticated) await page.addInitScript(token => localStorage.setItem("token",token),testToken());
}
