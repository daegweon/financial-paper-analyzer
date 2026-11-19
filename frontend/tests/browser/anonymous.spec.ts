import { test, expect } from "./helpers";
import AxeBuilder from "@axe-core/playwright";

test("unauthenticated sign-in works on desktop, Android Chrome and iPhone WebKit", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  // A Vercel SSO page is NOT an application login. For protected Preview,
  // use a short-lived VERCEL_OIDC_TOKEN scoped by helpers.ts.
  await expect(page.getByRole("heading", { name: "다시 만나서 반갑습니다." })).toBeVisible();
  await expect(page.getByRole("button", { name: "Google로 계속하기" })).toBeVisible();
  await expect(page.getByRole("button", { name: /^로그인/ })).toBeEnabled();
  await page.getByRole("button", { name: /계정이 없나요\? 회원가입/ }).click();
  await expect(page.getByRole("heading", { name: "연구 공간 만들기" })).toBeVisible();
  await page.getByRole("button", { name: /로그인으로 돌아가기/ }).click();
  await expect(page.getByRole("heading", { name: "다시 만나서 반갑습니다." })).toBeVisible();
});

test("320px narrow screen has usable form without horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const signIn = page.getByRole("button", { name: /^로그인/ });
  await expect(signIn).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  expect(overflow).toBe(false);
});


test("login and signup surfaces meet WCAG 2.1 AA automated checks", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations, JSON.stringify(results.violations.map((v) => ({
    id: v.id, impact: v.impact, description: v.description,
    nodes: v.nodes.map((n) => ({ target: n.target, summary: n.failureSummary })),
  })))).toEqual([]);
});
