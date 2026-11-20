import { test, expect } from "./helpers";
import AxeBuilder from "@axe-core/playwright";
import type { Page, Route } from "@playwright/test";

const fakeUrl = "http://127.0.0.1:54321";
const qaA = "11111111-1111-4111-8111-111111111111";
const qaB = "22222222-2222-4222-8222-222222222222";
const paperA = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const paperA2 = "cccccccc-cccc-4ccc-8ccc-cccccccccccc";
const paperB = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";
const stamp = "2026-11-17T00:00:00.000Z";
const dummyPdf = "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n";

type LocalUser = { id: string; aud: string; email: string; app_metadata: { provider: string; providers: string[] }; user_metadata: Record<string, never>; created_at: string };
function makeUser(email: string): LocalUser {
  return { id: email.startsWith("qa-a") ? qaA : qaB, aud: "authenticated", email,
    app_metadata: { provider: "email", providers: ["email"] }, user_metadata: {}, created_at: stamp };
}

async function mockSupabase(page: Page, options: { failFirstSign?: boolean } = {}) {
  let currentUser: LocalUser | null = null;
  let signCalls = 0;
  let unexpected = 0;
  const allow = {
    "access-control-allow-origin": "*",
    "access-control-allow-headers": "apikey, authorization, content-type, x-client-info, x-supabase-api-version",
    "access-control-allow-methods": "GET, POST, OPTIONS",
  };
  function respond(route: Route, status: number, data: unknown) {
    return route.fulfill({ status, headers: { ...allow, "content-type": "application/json" }, body: JSON.stringify(data) });
  }
  await page.route(fakeUrl + "/**", async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    const path = url.pathname;
    if (req.method() === "OPTIONS") return route.fulfill({ status: 204, headers: allow });

    if (path === "/auth/v1/token" && req.method() === "POST") {
      const fields = JSON.parse(req.postData() || "{}") as { email?: string };
      const email = fields.email || "qa-a@example.invalid";
      currentUser = makeUser(email);
      return respond(route, 200, {
        access_token: currentUser.id === qaA ? "mock-a-access" : "mock-b-access",
        token_type: "bearer", expires_in: 3600,
        expires_at: Math.floor(Date.now()/1000) + 3600,
        refresh_token: "mock-refresh",
        user: currentUser,
      });
    }
    if (path === "/auth/v1/user") {
      return currentUser ? respond(route, 200, currentUser) : respond(route, 401, { message: "no session" });
    }
    if (path === "/auth/v1/logout") {
      currentUser = null;
      return respond(route, 204, {});
    }
    if (path === "/rest/v1/papers") {
      const owner = currentUser?.id ?? qaA;
      const rows = owner === qaA
        ? [
            {id:paperA,title:"Synthetic A paper",status:"completed",storage_path:owner+"/fixture-a.pdf",created_at:stamp,page_count:5},
            {id:paperA2,title:"Synthetic A second paper",status:"completed",storage_path:owner+"/fixture-b.pdf",created_at:stamp,page_count:3},
          ]
        : [{id:paperB,title:"Synthetic B paper",status:"completed",storage_path:owner+"/fixture.pdf",created_at:stamp,page_count:5}];
      return respond(route, 200, rows);
    }
    if (path === "/rest/v1/analysis_jobs") return respond(route, 200, []);
    if (path === "/rest/v1/analyses") {
      return respond(route, 200, [{ paper_id:paperA, model:"mock-frontend-qa", created_at:stamp,
        result: {
          mode:"llm", summary:"Synthetic demonstration — not a real financial finding.",
          research_question:"Does a synthetic example have an estimate?",
          research_question_evidence:[{page:2,quote:"Synthetic research question."}],
          methodology:{design:"OLS regression",sample:"10 synthetic observations",period:"2020–2024",
            empirical_strategy:"OLS regression",identification_strategy:"Not identified",data_sources:[],
            variables:[],equations:[],evidence:[{page:2,quote:"Synthetic method."}]},
          findings:[{claim:"Synthetic coefficient is positive in a fake example.", direction:"positive",
            estimate:"0.20",statistical_significance:"p=0.04",
            evidence:[{page:3,quote:"Synthetic table reports 0.20."}],table_reference:"Table 1",
            verification:{status:"screen_passed",numeric_supported:true,direction_consistent:true,
              significance_supported:true,unsupported_numeric_tokens:[],method:"mock"}}],
          keywords:[],evidence:[{page:3,quote:"Synthetic table reports 0.20."}],page_count:5,
        },
      }]);
    }
    if (path.startsWith("/storage/v1/object/sign/papers/")) {
      if (req.method() === "POST") {
        signCalls++;
        if (options.failFirstSign && signCalls===1) return respond(route, 503, { message:"simulated failure" });
        return respond(route, 200, { signedURL: "/object/sign/papers/mock.pdf?token=synthetic-only" });
      }
      return route.fulfill({status:200, headers:{...allow,"content-type":"application/pdf"},body:dummyPdf});
    }
    unexpected++;
    return respond(route, 404, { message:"No mock handler for requested route" });
  });
  return { getSignCalls:()=>signCalls, unexpected:()=>unexpected };
}

async function login(page:Page, email: string) {
  await page.goto("/", {waitUntil:"domcontentloaded"});
  await expect(page.getByRole("heading",{name:"다시 만나서 반갑습니다."})).toBeVisible();
  await page.getByLabel("이메일").fill(email);
  await page.getByLabel("비밀번호").fill("fixture-only-password");
  await page.getByRole("button",{name:/^로그인/}).click();
  await expect(page.getByRole("heading",{name:"나의 연구 라이브러리"})).toBeVisible({timeout:20000});
}

test.describe("isolated synthetic Supabase browser flows", () => {
  test.skip(process.env.PAPERSIGNAL_BROWSER_QA_MOCKS!=="1" ||
    process.env.PAPERSIGNAL_BROWSER_QA_URL!=="http://localhost:3000",
    "Synthetic mocks are allowed ONLY against the explicit localhost dev server.");

  test("login → existing PDF → cited page → logout", async ({page}) => {
    const mock=await mockSupabase(page);
    await login(page,"qa-a@example.invalid");
    await expect(page.locator('[data-paper-id="'+paperA+'"]')).toBeVisible();
    await page.locator('[data-paper-id="'+paperA+'"]').click();
    const dialog=page.locator("section.details[role=dialog]");
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button",{name:"원문 PDF 함께 보기"}).click();
    const frame=dialog.locator("iframe.inline-pdf-frame");
    await expect(frame).toHaveAttribute("src",/#page=1$/);
    await dialog.locator("button.evidence-source-link").first().click();
    await expect(frame).toHaveAttribute("src",/#page=[23]$/);
    await page.keyboard.press("Escape");
    await expect(dialog).toHaveCount(0);
    await page.getByRole("button",{name:"로그아웃",exact:true}).first().click();
    await expect(page.getByRole("heading",{name:"다시 만나서 반갑습니다."})).toBeVisible();
    expect(mock.getSignCalls()).toBeGreaterThan(0);
    expect(mock.unexpected()).toBe(0);
  });

  test("failed PDF signing has a manual recovery button", async ({page}) => {
    const mock=await mockSupabase(page,{failFirstSign:true});
    await login(page,"qa-a@example.invalid");
    await page.locator('[data-paper-id="'+paperA+'"]').click();
    const dialog=page.locator("section.details[role=dialog]");
    await expect(dialog.getByRole("button",{name:"다시 연결"})).toBeVisible();
    await dialog.getByRole("button",{name:"다시 연결"}).click();
    await expect(dialog.getByRole("button",{name:"원문 PDF 함께 보기"})).toBeVisible();
    expect(mock.getSignCalls()).toBe(2);
  });

  test("switching users removes the previous paper", async ({page}) => {
    await mockSupabase(page);
    await login(page,"qa-a@example.invalid");
    await expect(page.locator('[data-paper-id="'+paperA+'"]')).toBeVisible();
    await page.getByRole("button",{name:"로그아웃",exact:true}).first().click();
    await expect(page.getByRole("heading",{name:"다시 만나서 반갑습니다."})).toBeVisible();
    await login(page,"qa-b@example.invalid");
    await expect(page.locator('[data-paper-id="'+paperB+'"]')).toBeVisible();
    await expect(page.locator('[data-paper-id="'+paperA+'"]')).toHaveCount(0);
  });
  test("junior study progress stays with the same user after reopen, never another user", async ({page}) => {
    await mockSupabase(page);
    await login(page, "qa-a@example.invalid");
    await page.locator('[data-paper-id="' + paperA + '"]').click();
    const dialog = page.locator("section.details[role=dialog]");
    const learning = dialog.locator('section[aria-labelledby="study-route-heading"]');
    await expect(learning).toBeVisible();
    await expect(learning.getByText("0 / 4 단계", { exact: true })).toBeVisible();
    await expect(learning.locator('article input[type="checkbox"]')).toHaveCount(4);
    await learning.locator('article input[type="checkbox"]').first().check();
    await expect(learning.getByText("1 / 4 단계", { exact: true })).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(dialog).toHaveCount(0);
    await page.locator('[data-paper-id="' + paperA + '"]').click();
    await expect(dialog.locator('section[aria-labelledby="study-route-heading"]')
      .getByText("1 / 4 단계", { exact: true })).toBeVisible();

    await page.keyboard.press("Escape");
    await page.getByRole("button", {name:"로그아웃",exact:true}).first().click();
    await expect(page.getByRole("heading", {name:"다시 만나서 반갑습니다."})).toBeVisible();
    await login(page, "qa-b@example.invalid");
    await page.locator('[data-paper-id="' + paperB + '"]').click();
    const otherLearning = page.locator('section[aria-labelledby="study-route-heading"]');
    await expect(otherLearning.getByText("0 / 4 단계", { exact: true })).toBeVisible();
    await expect(otherLearning.locator('article input[type="checkbox"]').first()).not.toBeChecked();
  });

  test("junior role-specific quiz grades explanations and separates role progress", async ({page}) => {
    await mockSupabase(page);
    await login(page, "qa-a@example.invalid");
    await page.locator('[data-paper-id="' + paperA + '"]').click();
    const dialog = page.locator("section.details[role=dialog]");
    const workplace = dialog.locator('section[aria-label="주니어를 위한 금융모형과 업무 활용 학습"]');
    const select = workplace.getByRole("combobox", {name:"관심 직무"});
    const learning = workplace.locator('section[aria-labelledby="study-route-heading"]');
    await expect(select).toHaveValue("wealth");
    await learning.locator('article input[type="checkbox"]').first().check();
    await expect(learning.getByText("1 / 4 단계", {exact:true})).toBeVisible();

    await select.selectOption("technology");
    await expect(learning.getByText("0 / 4 단계", {exact:true})).toBeVisible();
    await expect(learning.locator("fieldset")).toHaveCount(4);
    for (let i = 0; i < 4; i++) {
      await learning.locator("fieldset").nth(i).locator('input[type="radio"]').first().check();
    }
    await learning.getByRole("button", {name:"채점하고 해설 보기"}).click();
    await expect(learning.getByText(/이번 점검: \d \/ 4점/)).toBeVisible();

    await select.selectOption("wealth");
    await expect(learning.getByText("1 / 4 단계", {exact:true})).toBeVisible();
    await select.selectOption("technology");
    await expect(learning.getByText("0 / 4 단계", {exact:true})).toBeVisible();
    await learning.getByRole("button", {name:"이 직무의 학습 기록 초기화"}).click();
    await expect(learning.getByText("이 논문과 직무의 학습 기록을 초기화했습니다.")).toBeVisible();
  });

  test("junior study source-page action opens the original cited PDF page", async ({page}) => {
    await mockSupabase(page);
    await login(page, "qa-a@example.invalid");
    await page.locator('[data-paper-id="' + paperA + '"]').click();
    const dialog = page.locator("section.details[role=dialog]");
    const learning = dialog.locator('section[aria-labelledby="study-route-heading"]');
    const sourceAction = learning.getByRole("button", {name:"원문 페이지 열기"}).first();
    await expect(sourceAction).toBeEnabled();
    await sourceAction.click();
    await expect(dialog.locator("iframe.inline-pdf-frame")).toHaveAttribute("src", /#page=2$/);
  });


  test("authenticated library meets WCAG 2.1 AA automated checks", async ({page}) => {
    await mockSupabase(page);
    await login(page,"qa-a@example.invalid");
    const results = await new AxeBuilder({page})
      .withTags(["wcag2a","wcag2aa","wcag21a","wcag21aa"])
      .analyze();
    expect(results.violations, JSON.stringify(results.violations.map((v) => ({
      id:v.id, impact:v.impact, description:v.description,
      nodes:v.nodes.map((n) => ({target:n.target,summary:n.failureSummary})),
    })))).toEqual([]);
  });

  test("comparison dialog meets WCAG 2.1 AA and contains keyboard focus", async ({page}) => {
    await mockSupabase(page);
    await login(page,"qa-a@example.invalid");
    await page.getByLabel("Synthetic A paper 비교 대상으로 선택").check();
    await page.getByLabel("Synthetic A second paper 비교 대상으로 선택").check();
    const trigger = page.getByRole("button",{name:"선택 논문 비교"});
    await expect(trigger).toBeEnabled();
    await trigger.click();
    const dialog = page.getByRole("dialog",{name:"논문 비교 분석"});
    await expect(dialog).toBeVisible();
    const close = dialog.getByRole("button",{name:"비교 창 닫기"});
    await expect(close).toBeFocused();

    const results = await new AxeBuilder({page})
      .withTags(["wcag2a","wcag2aa","wcag21a","wcag21aa"])
      .analyze();
    expect(results.violations, JSON.stringify(results.violations.map((v) => ({
      id:v.id, impact:v.impact, description:v.description,
      nodes:v.nodes.map((n) => ({target:n.target,summary:n.failureSummary})),
    })))).toEqual([]);

    await page.keyboard.press("Shift+Tab");
    await expect(dialog.getByRole("region",{name:"논문 비교 표 가로 스크롤"})).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(close).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(dialog).toHaveCount(0);
    await expect(trigger).toBeFocused();
  });

});


  test("non-admin cannot view AI costs or service budget", async ({page}) => {
    await mockSupabase(page);
    await page.route("http://127.0.0.1:54322/api/admin/ai-usage/summary**", route =>
      route.fulfill({status:403,contentType:"application/json",body:JSON.stringify({detail:"관리자 권한이 필요합니다."})})
    );
    await login(page,"qa-a@example.invalid");
    await page.goto("/admin/ai-usage",{waitUntil:"domcontentloaded"});
    await expect(page.getByText("관리자 권한이 확인되지 않았습니다. 일반 사용자에게는 AI 사용량과 비용 정보가 공개되지 않습니다.", {exact:true})).toBeVisible();
    await expect(page.getByText("월간 추정 비용")).toHaveCount(0);
    await expect(page.getByText("서비스 전체 월간 AI 예산 설정")).toHaveCount(0);
  });

  test("administrator dashboard displays aggregate costs and saves only the global monthly budget", async ({page}) => {
    await mockSupabase(page);
    let budget = "100.00";
    const summary = () => ({
      month:"2026-11",currency:"USD",event_count:3,known_cost_events:2,unknown_cost_events:1,
      estimated_cost_usd:"12.50000000",monthly_budget_usd:budget,budget_status:"incomplete_truncated",
      cost_coverage_complete:false,
      models:[{model:"gemini-3.5-flash-lite",event_count:3,known_cost_events:2,unknown_cost_events:1,estimated_cost_usd:"12.50000000"}],
      users:[{user_id:qaA,event_count:3,known_cost_events:2,unknown_cost_events:1,estimated_cost_usd:"12.50000000"}],
      truncated:true,notice:"관리자 전용 운영 지표",
    });
    await page.route("http://127.0.0.1:54322/api/admin/ai-usage/summary**", route =>
      route.fulfill({status:200,contentType:"application/json",body:JSON.stringify(summary())})
    );
    await page.route("http://127.0.0.1:54322/api/admin/ai-usage/budget", async route => {
      const body = route.request().postDataJSON() as {monthly_budget_usd:string};
      budget = Number(body.monthly_budget_usd).toFixed(2);
      await route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({monthly_budget_usd:budget,updated:true})});
    });
    await login(page,"qa-a@example.invalid");
    await page.goto("/admin/ai-usage",{waitUntil:"domcontentloaded"});
    await expect(page.getByText("월간 추정 비용")).toBeVisible();
    await expect(page.getByRole("region",{name:"전체 사용량 요약"}).getByText("$12.50")).toBeVisible();
    await expect(page.getByText("gemini-3.5-flash-lite")).toBeVisible();
    await expect(page.getByText("사용자별 내부 운영 집계")).toBeVisible();
    await expect(page.getByText("조회 한도 도달 · 전체 비용 미확인")).toBeVisible();
    await expect(page.getByText(/조회 한도에 도달했습니다/)).toBeVisible();
    await page.getByLabel("월간 전체 예산 (USD)").fill("150");
    await page.getByRole("button",{name:"전체 예산 저장"}).click();
    await expect(page.getByRole("status")).toContainText("월간 전체 AI 예산을 저장했습니다.");
    await expect(page.getByLabel("월간 전체 예산 (USD)")).toHaveValue(/150(?:\.00)?/);
    const violations = await new AxeBuilder({page})
      .withTags(["wcag2a","wcag2aa","wcag21a","wcag21aa"])
      .analyze();
    const violationDetails = violations.violations.map(item => ({
      id: item.id,
      impact: item.impact,
      nodes: item.nodes.map(node => ({ target: node.target, summary: node.failureSummary })),
    }));
    expect(violations.violations.map(item => item.id), JSON.stringify(violationDetails)).toEqual([]);
  });
