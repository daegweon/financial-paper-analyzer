import { expect, test, type Page } from "@playwright/test";

const SUPABASE_REF = "hwmtayrecsfxernhssro";
const SUPABASE_URL = `https://${SUPABASE_REF}.supabase.co`;
const USER_ID = "11111111-1111-4111-8111-111111111111";
const PAPER_ID = "22222222-2222-4222-8222-222222222222";

async function seedAuthenticatedSession(page: Page) {
  await page.addInitScript(({ userId, projectRef }) => {
    const encode = (value: object) =>
      btoa(JSON.stringify(value)).replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_");
    const now = Math.floor(Date.now() / 1000);
    const accessToken = [
      encode({ alg: "HS256", typ: "JWT" }),
      encode({ sub: userId, aud: "authenticated", role: "authenticated", exp: now + 3600, iat: now }),
      "e2e-signature",
    ].join(".");
    const user = {
      id: userId,
      aud: "authenticated",
      role: "authenticated",
      email: "papersignal-e2e@example.test",
      app_metadata: { provider: "google", providers: ["google"] },
      user_metadata: { full_name: "PaperSignal E2E" },
      created_at: new Date().toISOString(),
    };
    localStorage.setItem(
      `sb-${projectRef}-auth-token`,
      JSON.stringify({
        access_token: accessToken,
        token_type: "bearer",
        expires_in: 3600,
        expires_at: now + 3600,
        refresh_token: "e2e-refresh-token",
        user,
      }),
    );
  }, { userId: USER_ID, projectRef: SUPABASE_REF });

  await page.route(`${SUPABASE_URL}/rest/v1/papers**`, route => {
    if (route.request().method() === "GET") {
      return route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
    }
    return route.continue();
  });
  await page.route(`${SUPABASE_URL}/rest/v1/analyses**`, route => {
    if (route.request().method() === "GET") {
      return route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
    }
    return route.continue();
  });
  await page.route("https://api.mock.papersignal.test/health", route =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ok", analysis_mode: "ai", ai_provider: "gemini" }),
    }),
  );
}

test("Google sign-in is visible in the first mobile viewport", async ({ page }) => {
  for (const viewport of [
    { width: 320, height: 640 },
    { width: 375, height: 667 },
    { width: 390, height: 844 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    const google = page.getByRole("button", { name: "Google로 계속하기" });
    await expect(google).toBeVisible();
    const box = await google.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.y + box!.height).toBeLessThanOrEqual(viewport.height);
    const form = await page.locator(".form form").boundingBox();
    expect(form).not.toBeNull();
    expect(box!.y + box!.height).toBeLessThan(form!.y);
  }
});

test("Google OAuth requests the Google provider and same-origin callback", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  const authorizationUrls: URL[] = [];
  await page.route(`${SUPABASE_URL}/auth/v1/authorize**`, async route => {
    authorizationUrls.push(new URL(route.request().url()));
    await route.fulfill({
      status: 200,
      contentType: "text/html",
      body: "<title>Mock Google authorization</title><p>OAuth redirect intercepted by E2E.</p>",
    });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "Google로 계속하기" }).click();
  await expect.poll(() => authorizationUrls[0]?.searchParams.get("provider") ?? null).toBe("google");
  const requestedUrl = authorizationUrls[0];
  expect(requestedUrl).toBeDefined();
  expect(requestedUrl!.searchParams.get("redirect_to")).toBe("http://127.0.0.1:3000/");
  expect(requestedUrl!.searchParams.get("prompt")).toBe("select_account");
});

test("mobile sign-out clears the local session and remains signed out after reload", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await seedAuthenticatedSession(page);
  let unexpectedUserLookups = 0;
  await page.route(`${SUPABASE_URL}/auth/v1/user**`, async route => {
    unexpectedUserLookups += 1;
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ message: "No active session" }),
    });
  });
  await page.route(`${SUPABASE_URL}/auth/v1/logout**`, async route => {
    await route.fulfill({ status: 204, body: "" });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "나의 연구 라이브러리" })).toBeVisible();
  expect(unexpectedUserLookups).toBe(0);
  const logout = page.getByRole("button", { name: "로그아웃" });
  await expect(logout).toBeVisible();
  await logout.click();

  await expect(page.getByRole("heading", { name: "다시 만나서 반갑습니다." })).toBeVisible();
  await expect.poll(() =>
    page.evaluate(() => localStorage.getItem("sb-hwmtayrecsfxernhssro-auth-token")),
  ).toBeNull();

  await page.reload();
  await page.waitForTimeout(1000);
  console.log("AFTER_SESSION_RELOAD", await page.locator("body").innerText(), await page.evaluate(() => ({ local: Object.keys(localStorage).map(key => [key, localStorage.getItem(key)]), session: Object.keys(sessionStorage).map(key => [key, sessionStorage.getItem(key)]), cookies: document.cookie })));
  await expect(page.getByRole("heading", { name: "다시 만나서 반갑습니다." })).toBeVisible();
  await expect(page.getByRole("button", { name: "로그아웃" })).toHaveCount(0);
  expect(unexpectedUserLookups).toBe(0);
});

test("PDF upload failure is visible and the upload control can be retried", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await seedAuthenticatedSession(page);
  let storageAttempts = 0;
  await page.route(`${SUPABASE_URL}/storage/v1/object/papers/**`, async route => {
    if (route.request().method() === "POST") {
      storageAttempts += 1;
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          statusCode: "503",
          error: "Service Unavailable",
          message: "storage temporarily unavailable",
        }),
      });
      return;
    }
    await route.continue();
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "나의 연구 라이브러리" })).toBeVisible();
  const fileInput = page.locator('input[type="file"]').last();
  await fileInput.setInputFiles({
    name: "broken.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("not a PDF"),
  });
  await expect(page.getByRole("status").filter({ hasText: "유효한 PDF" })).toBeVisible();
  expect(storageAttempts).toBe(0);

  await fileInput.setInputFiles({
    name: "sample.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-1.4\n% PaperSignal E2E fixture\n"),
  });
  await expect(page.getByRole("status").filter({ hasText: "storage temporarily unavailable" })).toBeVisible();
  await expect(fileInput).toBeEnabled();
  expect(storageAttempts).toBe(1);
});

test("analysis API failure is surfaced and the user can retry", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await seedAuthenticatedSession(page);
  await page.unroute(`${SUPABASE_URL}/rest/v1/papers**`);
  await page.route(`${SUPABASE_URL}/rest/v1/papers**`, route => {
    if (route.request().method() === "GET") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{
          id: PAPER_ID,
          title: "E2E 금융논문",
          status: "uploaded",
          storage_path: `${USER_ID}/fixture.pdf`,
          created_at: new Date().toISOString(),
          page_count: 1,
        }]),
      });
    }
    return route.continue();
  });
  await page.route("https://api.mock.papersignal.test/api/analyze/**", route =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Gemini temporarily unavailable" }),
    }),
  );

  await page.goto("/");
  await page.getByRole("button", { name: "E2E 금융논문" }).click();
  const analyze = page.getByRole("button", { name: "분석 시작 →" });
  await expect(analyze).toBeVisible();
  await analyze.click();
  await expect(page.getByRole("status").filter({ hasText: "Gemini temporarily unavailable" })).toBeVisible();
  await expect(analyze).toBeEnabled();
});
