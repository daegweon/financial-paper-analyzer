import { test as base, expect, type Page } from "@playwright/test";
import { validateBrowserQaTarget } from "../../lib/browser-qa-target";

const target = validateBrowserQaTarget(process.env.PAPERSIGNAL_BROWSER_QA_URL);
export const test = base;
export { expect };

/**
 * A short-lived Vercel trusted-source token is sent ONLY to our own Preview host.
 * A global context extraHTTPHeaders value would leak it to Supabase and Google.
 */
test.beforeEach(async ({ context }) => {
  const token = process.env.VERCEL_OIDC_TOKEN;
  if (target.kind !== "preview" || !token) return;
  await context.route(target.origin + "/**", (route) => {
    return route.continue({
      headers: { ...route.request().headers(), "x-vercel-trusted-oidc-idp-token": token },
    });
  });
});

export function requireQaCredentials(suffix: "" | "_B" = "") {
  const email = process.env["PAPERSIGNAL_QA" + suffix + "_EMAIL"];
  const password = process.env["PAPERSIGNAL_QA" + suffix + "_PASSWORD"];
  if (!email || !password) {
    throw new Error("Read-only browser QA requires separately configured test account " + (suffix || "A") + " credentials.");
  }
  return { email, password };
}

export async function signIn(page: Page, email: string, password: string) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "다시 만나서 반갑습니다." })).toBeVisible();
  await page.getByLabel("이메일").fill(email);
  await page.getByLabel("비밀번호").fill(password);
  await page.getByRole("button", { name: /^로그인/ }).click();
  await expect(page.getByRole("heading", { name: "나의 연구 라이브러리" })).toBeVisible({ timeout: 30_000 });
}

export async function openPaper(page: Page, title: string) {
  if (!title) throw new Error("PAPERSIGNAL_QA_PAPER_TITLE must name a pre-existing analyzed QA PDF.");
  // Always use an existing paper: browser QA never uploads or re-analyzes.
  const row = page.getByRole("button").filter({ hasText: title }).first();
  await expect(row).toBeVisible();
  await row.click();
  const dialog = page.getByRole("dialog", { name: title, exact: true });
  await expect(dialog).toBeVisible();
  return { row, dialog };
}

export async function signOut(page: Page) {
  const button = page.getByRole("button", { name: "로그아웃", exact: true }).first();
  await expect(button).toBeVisible();
  await button.click();
  await expect(page.getByRole("heading", { name: "다시 만나서 반갑습니다." })).toBeVisible();
}
