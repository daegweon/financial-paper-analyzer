import { test, expect } from "./helpers";
import type { Page, Route } from "@playwright/test";

const fakeUrl = "http://127.0.0.1:54321";
const qaA = "11111111-1111-4111-8111-111111111111";
const qaB = "22222222-2222-4222-8222-222222222222";
const paperA = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
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
      const mine = currentUser?.id === qaA ? paperA : paperB;
      const title = currentUser?.id === qaA ? "Synthetic A paper" : "Synthetic B paper";
      return respond(route, 200, [{id:mine, title, status:"completed",
        storage_path:(currentUser?.id??qaA)+"/fixture.pdf",
        created_at:stamp, page_count:5}]);
    }
    if (path === "/rest/v1/analysis_jobs") return respond(route, 200, []);
    if (path === "/rest/v1/analyses") {
      return respond(route, 200, [{ model:"mock-frontend-qa", created_at:stamp,
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
});
