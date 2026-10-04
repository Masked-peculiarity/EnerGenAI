import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  timeout: 60000,
  workers: 1,
  reporter: "list",
  outputDir: "../energy-backend/runtime/browser-results",
  use: {
    baseURL: "http://localhost:8080",
    channel: process.env.PLAYWRIGHT_CHANNEL || "chrome",
    headless: true,
    viewport: { width: 1440, height: 1000 },
    screenshot: "only-on-failure"
  }
});
