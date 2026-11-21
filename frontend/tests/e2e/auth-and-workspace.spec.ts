import { expect, test, type Page } from "@playwright/test";

const SUPABASE_REF = "hwmtayrecsfxernhssro";
const SUPABASE_URL = `https://${SUPABASE_REF}.supabase.co`;
const USER_ID = "11111111-1111-4111-8111-111111111111";
const PAPER_ID = "22222222-2222-4222-8222-222222222222";

async function seedAuthenticatedSession(page: Page) {
  await page.addInitScript(({ userId, projectRef }) => {
    // addInitScript runs on every navigation; seed only the first document.
    if (sessionStorage.getItem("papersignal-e2e-session-seeded") === "1") return;
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
    sessionStorage.setItem("papersignal-e2e-session-seeded", "1");
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
  await page.route(`${SUPABASE_URL}/rest/v1/analysis_jobs**`, route => {
    if (route.request().method() === "GET") {
      return route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
    }
    return route.continue();
  });
  await page.route(`${SUPABASE_URL}/storage/v1/object/sign/papers/**`, route =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ signedUrl: "https://storage.mock.papersignal.test/signed/fixture.pdf" }),
    }),
  );
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

test("sign-out remains available on mobile, tablet and desktop", async ({ page }) => {
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
  for (const viewport of [
    { width: 320, height: 640 },
    { width: 390, height: 844 },
    { width: 768, height: 900 },
    { width: 1024, height: 768 },
    { width: 1440, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    await expect(logout).toBeVisible();
    const box = await logout.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(viewport.width);
  }
  await logout.click();

  await expect(page.getByRole("heading", { name: "다시 만나서 반갑습니다." })).toBeVisible();
  await expect.poll(() =>
    page.evaluate(() => localStorage.getItem("sb-hwmtayrecsfxernhssro-auth-token")),
  ).toBeNull();

  await page.reload();
  await page.waitForTimeout(1000);
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
  await expect(page.getByRole("status").filter({ hasText: "PDF 업로드가 완료되지 않았습니다" })).toBeVisible();
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
  let analysisRequests = 0;
  await page.route("https://api.mock.papersignal.test/api/analyze/**", async route => {
    analysisRequests += 1;
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Gemini temporarily unavailable" }),
    });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "E2E 금융논문" }).click();
  const analyze = page.getByRole("button", { name: "분석 시작 →" });
  await expect(analyze).toBeVisible();
  await analyze.click();
  await expect.poll(() => analysisRequests).toBe(1);
  const errorMessage = page.locator(".message");
  await expect(errorMessage).toBeVisible();
  await expect(errorMessage).toContainText("분석 작업 등록 응답이 일시적으로 실패했습니다");
  await expect(analyze).toBeEnabled();
});


test("paper analysis opens as a full-width report with visible section navigation and logout", async ({ page }) => {
  const desktopViewport = { width: 1280, height: 900 };
  await page.setViewportSize(desktopViewport);
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
          status: "completed",
          storage_path: `${USER_ID}/fixture.pdf`,
          created_at: new Date().toISOString(),
          page_count: 2,
        }]),
      });
    }
    return route.continue();
  });
  await page.unroute(`${SUPABASE_URL}/rest/v1/analyses**`);
  await page.route(`${SUPABASE_URL}/rest/v1/analyses**`, route => {
    if (route.request().method() === "GET") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([{
          paper_id: PAPER_ID,
          model: "gemini-3.5-flash-lite",
          created_at: new Date().toISOString(),
          result: {
            mode: "llm",
            analysis_version: "v6.4.2",
            summary: "표본 기간 동안 주요 설명변수와 수익률 사이의 관계를 분석한 연구입니다.",
            bibliographic: {
              title: "E2E 금융논문",
              authors: ["테스트 저자"],
              year: "2026",
              venue: "E2E Journal",
              doi: "",
              evidence: [{ page: 1, quote: "연구 목적과 데이터 설명" }],
            },
            research_question: "주요 설명변수가 자산 수익률과 어떤 관계를 가지는가?",
            research_question_evidence: [{ page: 1, quote: "본 연구는 자산 수익률의 결정요인을 분석한다." }],
            methodology: {
              design: "패널 회귀분석",
              sample: "기업 100개",
              period: "2015~2024년",
              data_sources: ["공개 재무자료"],
              empirical_strategy: "고정효과 회귀",
              identification_strategy: "통제변수 및 고정효과",
              variables: [{
                name: "C (비용)",
                role: "설명변수",
                definition: "기업의 운영 비용을 나타내는 변수입니다.",
                evidence: [{ page: 2, quote: "C denotes the operating cost." }],
              }],
              equations: [
                "L(C) = aCb + c",
                "-E_P[log(pass_rate(C))] = α*C^-k",
              ],
              evidence: [{ page: 2, quote: "고정효과 모형을 추정한다." }],
            },
            findings: [{
              claim: "주요 설명변수는 종속변수와 양(+)의 관계를 보였습니다.",
              direction: "양(+)의 관계",
              estimate: "0.12",
              statistical_significance: "5% 수준",
              table_reference: "Table 1",
              model_or_column: "Model 1",
              evidence: [{ page: 2, quote: "The coefficient is positive and significant." }],
              verification: {
                status: "screen_passed",
                numeric_supported: true,
                direction_consistent: true,
                significance_supported: true,
                unsupported_numeric_tokens: [],
              },
            }],
            findings_coverage: {
              status: "supported",
              supported_findings_count: 1,
              review_findings_count: 0,
              empirical_result_signals_detected: true,
              method: "fixture",
            },
            robustness_checks: [],
            limitations: [{ description: "표본 범위가 제한적입니다." , evidence: [{ page: 2, quote: "The sample is limited." }] }],
            implications: [],
            hypotheses: [],
            contributions: [],
            keywords: ["패널", "수익률"],
            evidence: [{ page: 1, quote: "연구 대상 및 기간" }],
            warnings: [],
            page_count: 2,
          },
        }]),
      });
    }
    return route.continue();
  });

  await page.route(`${SUPABASE_URL}/auth/v1/logout**`, route =>
    route.fulfill({ status: 204, body: "" }),
  );

  await page.goto("/");
  const workspaceBeforeDiscovery = await page.locator("#personal-research-workspace").evaluate(workspace => {
    const discovery = document.querySelector(".public-paper-discovery");
    return Boolean(discovery && (workspace.compareDocumentPosition(discovery) & Node.DOCUMENT_POSITION_FOLLOWING));
  });
  expect(workspaceBeforeDiscovery).toBe(true);
  await expect(page.getByRole("heading", { name: "나의 연구 라이브러리" })).toBeVisible();
  await page.getByRole("button", { name: "E2E 금융논문" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  const bounds = await dialog.boundingBox();
  expect(bounds).not.toBeNull();
  expect(bounds!.width).toBeGreaterThanOrEqual(desktopViewport.width * 0.9);

  for (const viewport of [
    { width: 320, height: 640 },
    { width: 390, height: 844 },
    { width: 768, height: 900 },
    { width: 1280, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    const responsiveBounds = await dialog.boundingBox();
    expect(responsiveBounds).not.toBeNull();
    expect(responsiveBounds!.width).toBeGreaterThanOrEqual(viewport.width * 0.9);
    const logout = page.locator(".detail-sign-out");
    await expect(logout).toBeVisible();
    const logoutBounds = await logout.boundingBox();
    expect(logoutBounds).not.toBeNull();
    expect(logoutBounds!.x).toBeGreaterThanOrEqual(0);
    expect(logoutBounds!.x + logoutBounds!.width).toBeLessThanOrEqual(viewport.width);
  }
  await page.setViewportSize(desktopViewport);

  await expect(page.getByRole("navigation", { name: "분석 보고서 목차" })).toBeVisible();
  const evidenceTrigger = dialog.locator(".evidence-info-button").first();
  const evidencePopover = evidenceTrigger.locator("xpath=..").locator(".evidence-popover");
  await expect(evidenceTrigger).toBeVisible();
  await expect(evidenceTrigger).toHaveAttribute("aria-expanded", "false");
  await expect(evidencePopover).toBeHidden();
  await expect(dialog.locator("details.evidence")).toHaveCount(0);

  const evidencePreview = evidencePopover.locator(".evidence-popover-preview");
  const evidenceDetail = evidencePopover.locator(".evidence-popover-detail");

  // Keyboard focus opens a lightweight tooltip; Enter opens the full interactive dialog.
  await evidenceTrigger.focus();
  await expect(evidencePreview).toBeVisible();
  await expect(evidenceDetail).toBeHidden();
  await evidenceTrigger.press("Enter");
  await expect(evidenceDetail).toBeVisible();
  await expect(evidencePreview).toBeHidden();
  await page.keyboard.press("Escape");
  await expect(evidencePopover).toBeHidden();
  await expect(evidenceTrigger).toBeFocused();

  // Hovering the claim text itself reveals a cursor-adjacent quote preview.
  const evidenceAnchor = evidenceTrigger.locator("xpath=..");
  const evidenceText = evidenceAnchor.locator(".evidence-inline-copy");
  await expect(evidenceText).toContainText("테스트 저자");
  await evidenceText.hover();
  await expect(evidencePreview).toBeVisible();
  await expect(evidenceDetail).toBeHidden();
  await expect(evidencePreview).toContainText("연구 목적과 데이터 설명");

  // The preview follows the pointer over the claim, then remains hoverable itself.
  const claimBounds = await evidenceText.boundingBox();
  const firstPopoverBounds = await evidencePopover.boundingBox();
  expect(claimBounds).not.toBeNull();
  expect(firstPopoverBounds).not.toBeNull();
  await page.mouse.move(claimBounds!.x + claimBounds!.width - 3, claimBounds!.y + claimBounds!.height / 2);
  const movedPopoverBounds = await evidencePopover.boundingBox();
  expect(movedPopoverBounds).not.toBeNull();
  expect(Math.abs(movedPopoverBounds!.x - firstPopoverBounds!.x) + Math.abs(movedPopoverBounds!.y - firstPopoverBounds!.y)).toBeGreaterThan(5);
  await evidencePopover.hover();
  await expect(evidencePopover).toBeVisible();
  await expect(evidencePreview).toBeVisible();
  await page.mouse.move(5, 5);
  await expect(evidencePopover).toBeHidden();

  // Clicking the small i opens the complete citations and PDF page actions.
  await evidenceTrigger.click();
  await expect(evidenceTrigger).toHaveAttribute("aria-expanded", "true");
  await expect(evidenceDetail).toBeVisible();
  await expect(evidencePreview).toBeHidden();
  await expect(evidenceDetail).toContainText("연구 목적과 데이터 설명");
  await page.keyboard.press("Escape");
  await expect(evidencePopover).toBeHidden();
  await expect(evidenceTrigger).toBeFocused();
  await evidenceTrigger.click();
  await expect(evidenceDetail).toBeVisible();
  await dialog.locator("#analysis-summary").click();
  await expect(evidencePopover).toBeHidden();

  // Print/PDF keeps every source quote even when the screen popover is closed.
  await page.emulateMedia({ media: "print" });
  await expect(evidenceTrigger).toBeHidden();
  await expect(evidencePreview).toBeHidden();
  await expect(evidenceDetail).toBeVisible();
  await page.emulateMedia({ media: "screen" });
  await page.mouse.move(5, 5);
  await expect(evidencePopover).toBeHidden();

  const juniorEvidenceTrigger = dialog.locator("#analysis-junior-guide .evidence-info-button").first();
  const juniorEvidenceAnchor = juniorEvidenceTrigger.locator("xpath=..");
  const juniorEvidencePopover = juniorEvidenceAnchor.locator(".evidence-popover");
  await expect(juniorEvidenceTrigger).toBeVisible();
  await expect(juniorEvidenceTrigger.locator("xpath=ancestor::li[1]").locator(".evidence-info-button")).toHaveCount(1);
  await expect(juniorEvidencePopover.locator(".evidence-popover-preview")).toBeHidden();
  await juniorEvidenceAnchor.locator(".evidence-inline-copy").hover();
  await expect(juniorEvidencePopover.locator(".evidence-popover-preview")).toBeVisible();
  await expect(juniorEvidencePopover.locator(".evidence-popover-detail")).toBeHidden();
  await expect(juniorEvidencePopover.locator(".evidence-popover-preview")).toContainText("The coefficient is positive and significant.");
  await page.mouse.move(5, 5);
  await expect(juniorEvidencePopover).toBeHidden();
  await expect(page.locator("#analysis-summary")).toContainText("표본 기간 동안");
  await expect(page.locator("#analysis-findings")).toHaveCount(1);

  const equationGuide = dialog.locator(".equation-explainer");
  await expect(equationGuide).toBeVisible();
  await expect(equationGuide).toContainText("기호별 설명");
  await expect(equationGuide).toContainText("기업의 운영 비용을 나타내는 변수입니다.");
  await expect(equationGuide).toContainText("계수 또는 크기 조정 파라미터");
  await expect(equationGuide).toContainText("거듭제곱 지수 파라미터");
  await expect(equationGuide).toContainText("상수항");
  await expect(equationGuide).toContainText("확률분포 P 아래의 기댓값 연산자");
  await expect(equationGuide.locator(".equation-symbol-row")).toHaveCount(10);
  const reportText = dialog.locator(".result #analysis-summary > p");
  await expect(reportText).toBeVisible();
  expect(Number(await reportText.evaluate(el => getComputedStyle(el).fontSize.replace("px", "")))).toBeGreaterThanOrEqual(15);
  const evidenceGap = evidenceAnchor.locator(".evidence-inline-gap");
  await expect(evidenceGap).toHaveCount(1);
  const gapWidth = await evidenceGap.evaluate(el => el.getBoundingClientRect().width);
  expect(gapWidth).toBeGreaterThanOrEqual(8);

  const equationSymbols = await equationGuide.locator(".equation-symbol-token").allTextContents();
  expect(equationSymbols).toEqual(["L", "C", "a", "b", "c", "E_P", "log", "pass_rate", "α", "k"]);
  expect(equationSymbols).toContain("C");
  expect(equationSymbols).toContain("c");

  const readingControls = dialog.getByRole("group", { name: "보고서 글자 크기" });
  await expect(readingControls).toBeVisible();
  await expect(readingControls.locator("output")).toHaveText("100%");
  await readingControls.getByRole("button", { name: "글자 크기 키우기" }).click();
  await expect(readingControls.locator("output")).toHaveText("110%");
  await expect.poll(() => page.evaluate(() => localStorage.getItem("papersignal-reading-scale"))).toBe("110");
  const scaledReportFont = await reportText.evaluate(el => getComputedStyle(el).fontSize);
  expect(Number(scaledReportFont.replace("px", ""))).toBeGreaterThan(15);
  await readingControls.getByRole("button", { name: "글자 크기 기본값으로" }).click();
  await expect(readingControls.locator("output")).toHaveText("100%");
  await expect.poll(() => page.evaluate(() => localStorage.getItem("papersignal-reading-scale"))).toBe("100");
  await expect(page.locator(".detail-sign-out")).toBeVisible();

  await page.getByRole("link", { name: "실증 결과", exact: true }).click();
  await expect(page.locator("#analysis-findings")).toBeInViewport();

  await page.getByRole("button", { name: "원문 PDF 함께 보기" }).click();
  await expect(page.locator("#paper-original-pdf iframe")).toBeVisible();

  await page.locator(".detail-sign-out").click();
  await expect(page.getByRole("heading", { name: "다시 만나서 반갑습니다." })).toBeVisible();
});


test("public-paper search and one-click import preserve user-owned PDF upload", async ({ page }) => {
  await seedAuthenticatedSession(page);
  let uploaded = false;
  let storageAuthorized = false;
  let searchAuthorized = false;
  let downloadAuthorized = false;
  const paper = {
    id: PAPER_ID, title: "ETF asset pricing", status: "pending",
    storage_path: `${USER_ID}/imported-test.pdf`, created_at: new Date().toISOString(), page_count: null,
  };

  await page.unroute(`${SUPABASE_URL}/rest/v1/papers**`);
  await page.route(`${SUPABASE_URL}/rest/v1/papers**`, route => {
    if (route.request().method() === "GET") return route.fulfill({
      status: 200, contentType: "application/json", body: JSON.stringify(uploaded ? [paper] : []),
    });
    if (route.request().method() === "POST") {
      uploaded = true;
      return route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(paper) });
    }
    return route.continue();
  });
  await page.route(`${SUPABASE_URL}/storage/v1/object/papers/**`, route => {
    storageAuthorized = route.request().headers()["authorization"]?.startsWith("Bearer ") ?? false;
    return route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ Key: paper.storage_path }),
    });
  });
  await page.route("https://api.mock.papersignal.test/api/public-papers/recommendations", route =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ results: [] }) }),
  );
  await page.route("https://api.mock.papersignal.test/api/public-papers/search**", route => {
    searchAuthorized = route.request().headers()["authorization"]?.startsWith("Bearer ") ?? false;
    return route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        query: "ETF", page: 1, total: 1, has_more: false,
        results: [{
          id: "https://openalex.org/W123", title: "ETF asset pricing", year: 2025,
          cited_by_count: 87,
          doi: "https://doi.org/10.1234/etf", authors: ["Researcher"],
          pdf_url: "https://journal.example.org/etf.pdf",
          landing_url: "https://journal.example.org/etf",
          license: "cc-by", is_open_access: true,
        }],
      }),
    });
  });
  await page.route("https://api.mock.papersignal.test/api/public-papers/download", route => {
    downloadAuthorized = route.request().headers()["authorization"]?.startsWith("Bearer ") ?? false;
    expect(route.request().postDataJSON()).toEqual({ url: "https://journal.example.org/etf.pdf" });
    return route.fulfill({
      status: 200, contentType: "application/pdf",
      body: Buffer.from("%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"),
    });
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "공개 금융 논문 찾아보기" })).toBeVisible();
  await page.getByRole("searchbox", { name: "공개 학술 논문 검색 (OpenAlex)" }).fill("ETF");
  await page.getByRole("button", { name: "논문 검색" }).click();
  await expect(page.getByText("ETF asset pricing").first()).toBeVisible();
  await page.getByRole("button", { name: "PDF 가져오기" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  expect(searchAuthorized).toBe(true);
  expect(downloadAuthorized).toBe(true);
  expect(storageAuthorized).toBe(true);
  expect(uploaded).toBe(true);
});


test("shows recommended public finance papers without a search query and sorts by citations/authors", async ({ page }) => {
  await seedAuthenticatedSession(page);
  await page.route("https://api.mock.papersignal.test/api/public-papers/recommendations", route =>
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        source: "OpenAlex",
        results: [
          { id: "W1", title: "Zeta Markets", year: 2023, authors: ["Zed Author"], cited_by_count: 1200,
            category: "자산가격·금융시장", pdf_url: "https://journal.example.org/zeta.pdf",
            landing_url: "https://journal.example.org/zeta", license: "cc-by", is_open_access: true },
          { id: "W2", title: "Alpha Portfolio", year: 2025, authors: ["Alice Author"], cited_by_count: 45,
            category: "포트폴리오·위험관리", pdf_url: "https://journal.example.org/alpha.pdf",
            landing_url: "https://journal.example.org/alpha", license: "cc-by", is_open_access: true },
          { id: "W3", title: "Beta ETF", year: 2024, authors: ["Bob Author"], cited_by_count: 430,
            category: "ETF·시장 미시구조", pdf_url: "https://journal.example.org/beta.pdf",
            landing_url: "https://journal.example.org/beta", license: "cc-by", is_open_access: true },
        ],
      }),
    }),
  );
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "어떤 논문을 읽을지 모르겠다면, 여기서 시작하세요" })).toBeVisible();
  await expect(page.getByText("OpenAlex 인용 1,200회")).toBeVisible();

  await page.locator("#public-paper-sort").selectOption("citations_desc");
  let titles = await page.locator(".public-paper-result-info strong").allTextContents();
  expect(titles).toEqual(["Zeta Markets", "Beta ETF", "Alpha Portfolio"]);

  await page.locator("#public-paper-sort").selectOption("author_asc");
  titles = await page.locator(".public-paper-result-info strong").allTextContents();
  expect(titles).toEqual(["Alpha Portfolio", "Beta ETF", "Zeta Markets"]);
});

test("clearing the search box does not break pagination of the saved search result set", async ({ page }) => {
  await seedAuthenticatedSession(page);
  const requests: Array<{ query: string | null; page: string | null }> = [];
  await page.route("https://api.mock.papersignal.test/api/public-papers/recommendations", route =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ results: [] }) }),
  );
  await page.route("https://api.mock.papersignal.test/api/public-papers/search**", route => {
    const url = new URL(route.request().url());
    const query = url.searchParams.get("query");
    const pageNumber = url.searchParams.get("page");
    requests.push({ query, page: pageNumber });
    const secondPage = pageNumber === "2";
    const title = secondPage ? "ETF saved-query page two" : "ETF saved-query page one";
    const results = Array.from({ length: 10 }, (_, index) => ({
      id: "https://openalex.org/" + (secondPage ? "W2" : "W1") + "-" + index,
      title: title + " paper " + index,
      year: 2025,
      authors: ["Research Author"],
      cited_by_count: 10 + index,
      pdf_url: null,
      landing_url: "https://journal.example.org/paper",
      license: "미확인",
      is_open_access: true,
    }));
    return route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        query: "ETF", page: Number(pageNumber), per_page: 100,
        total: 200, has_more: true, results,
      }),
    });
  });

  await page.goto("/");
  const search = page.getByRole("searchbox", { name: "공개 학술 논문 검색 (OpenAlex)" });
  await search.fill("ETF");
  await page.getByRole("button", { name: "논문 검색" }).click();
  await expect(page.getByText("ETF saved-query page one paper 0")).toBeVisible();

  await search.fill("");
  await expect(page.getByText(/검색 당시의 결과입니다/)).toBeVisible();
  await page.getByRole("button", { name: "다음" }).click();
  await expect(page.getByText("ETF saved-query page two paper 0")).toBeVisible();
  expect(requests).toEqual([
    { query: "ETF", page: "1" },
    { query: "ETF", page: "2" },
  ]);
});
