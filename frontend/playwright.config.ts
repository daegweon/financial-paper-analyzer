import { defineConfig, devices } from "@playwright/test";
import { validateBrowserQaTarget } from "./lib/browser-qa-target";

// No implicit production fallback, even for a manually invoked test command.
if (process.env.PAPERSIGNAL_BROWSER_QA !== "1") {
  throw new Error("Browser QA is opt-in. Set PAPERSIGNAL_BROWSER_QA=1 for read-only tests.");
}
const target = validateBrowserQaTarget(process.env.PAPERSIGNAL_BROWSER_QA_URL);

export default defineConfig({
  testDir: "./tests/browser",
  testMatch: "**/*.spec.ts",
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  reporter: [["list"]],
  outputDir: "./.playwright-test-results",
  use: {
    baseURL: target.origin,
    locale: "ko-KR",
    timezoneId: "Asia/Seoul",
    trace: "off",
    screenshot: "off",
    video: "off",
    ignoreHTTPSErrors: false,
  },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
    { name: "android-chromium", use: { ...devices["Pixel 7"], viewport: { width: 375, height: 812 } } },
    { name: "iphone-webkit", use: { ...devices["iPhone 13"], viewport: { width: 390, height: 844 } } },
  ],
});
