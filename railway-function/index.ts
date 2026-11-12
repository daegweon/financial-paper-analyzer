import { PDFParse } from "pdf-parse@2.4.5";

const MAX_BYTES = 30 * 1024 * 1024;
const MAX_SCAN_PAGES = 50;
const MAX_PAGES = 300;
const SUPABASE_URL = (Bun.env.SUPABASE_URL || "").replace(/\/+$/, "");
const SUPABASE_PUBLISHABLE_KEY = Bun.env.SUPABASE_PUBLISHABLE_KEY || "";
const allowedOrigins = (Bun.env.FRONTEND_ORIGIN || "http://localhost:3000")
  .split(",").map(s => s.trim().replace(/\/+$/, "")).filter(Boolean);
const keywords = [
  "asset pricing", "portfolio", "factor", "volatility", "liquidity",
  "market risk", "interest rate", "exchange rate", "yield", "return",
  "regression", "causal", "panel data", "risk premium", "inflation",
  "credit risk", "금리", "환율", "변동성", "수익률",
];
const idPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
type Page = { page: number; text: string };

function headersForOrigin(origin: string | null): Record<string,string> {
  const h: Record<string,string> = {
    "Content-Type": "application/json; charset=utf-8",
    "Vary": "Origin",
    "Cache-Control": "no-store",
  };
  if (origin && allowedOrigins.includes(origin)) {
    h["Access-Control-Allow-Origin"] = origin;
    h["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS";
    h["Access-Control-Allow-Headers"] = "Authorization, Content-Type";
    h["Access-Control-Max-Age"] = "300";
  }
  return h;
}
function reply(body: unknown, status: number, origin: string|null): Response {
  return new Response(JSON.stringify(body), { status, headers: headersForOrigin(origin) });
}
async function supabaseRequest(path: string, token: string, init?: RequestInit) {
  const headers = new Headers(init?.headers ?? {});
  headers.set("apikey", SUPABASE_PUBLISHABLE_KEY);
  headers.set("Authorization", "Bearer " + token);
  const response = await fetch(SUPABASE_URL + path, { ...init, headers, signal: AbortSignal.timeout(30000) });
  return response;
}
async function extractPdf(buffer: ArrayBuffer): Promise<{ pageCount: number, pages: Page[] }> {
  const signature = new TextDecoder().decode(buffer.slice(0,5));
  if (signature !== "%PDF-" || buffer.byteLength > MAX_BYTES) throw new Error("INVALID_PDF");
  const parser = new PDFParse({ data: new Uint8Array(buffer) });
  try {
    const result = await parser.getText({ first: MAX_SCAN_PAGES });
    const pageCount = Number(result.total);
    if (!Number.isInteger(pageCount) || pageCount < 1 || pageCount > MAX_PAGES) {
      throw new Error("PAGE_LIMIT");
    }
    const pages: Page[] = (result.pages || []).map((p: any) => ({
      page: Number(p.num),
      text: String(p.text || "").replace(/\s+/g, " ").trim().slice(0,4500),
    })).filter(p => p.text.length > 0 && Number.isInteger(p.page) && p.page >= 1);
    if (!pages.length) throw new Error("NO_TEXT");
    return {pageCount, pages};
  } finally { await parser.destroy(); }
}
function extractiveResult(pageCount: number, pages: Page[]) {
  const text = pages.map(p => p.text).join(" ").toLowerCase();
  const warnings = [
    "추출 기반 분석으로, 본문 일부의 발췌와 키워드만 제공합니다. 연구 결론을 독립적으로 검증한 결과가 아닙니다.",
  ];
  if (pageCount > MAX_SCAN_PAGES) warnings.push("처음 50페이지만 분석했습니다. 나머지 페이지를 원문에서 확인하세요.");
  return {
    mode: "extractive",
    summary: "총 " + pageCount + "페이지 논문에서 텍스트를 추출했습니다. 연구 질문과 실증 결과는 원문을 직접 확인해 주세요.",
    keywords: keywords.filter(k => text.includes(k)).slice(0, 16),
    evidence: pages.slice(0,8).map(p => ({page:p.page, quote:p.text.slice(0,420)})),
    page_count: pageCount,
    warnings,
  };
}
async function analyze(req: Request, origin: string|null, paperId: string) {
  if (!SUPABASE_URL || !SUPABASE_PUBLISHABLE_KEY) return reply({detail:"API 환경설정이 완료되지 않았습니다."},503,origin);
  const auth = req.headers.get("authorization") ?? "";
  if (!auth.startsWith("Bearer ") || !auth.slice(7).trim()) return reply({detail:"로그인이 필요합니다."},401,origin);
  const token = auth.slice(7).trim();
  try {
    const profile = await supabaseRequest("/auth/v1/user", token);
    if (!profile.ok) return reply({detail:"인증 세션이 유효하지 않습니다."},401,origin);
    const user = await profile.json() as { id?: string };
    if (!user.id || !idPattern.test(user.id)) return reply({detail:"사용자 인증에 실패했습니다."},401,origin);
    const paperSearch = new URLSearchParams({ id:"eq." + paperId, select:"id,user_id,storage_path" });
    const paperResponse = await supabaseRequest("/rest/v1/papers?" + paperSearch.toString(), token);
    if (!paperResponse.ok) return reply({detail:"논문 조회에 실패했습니다."},502,origin);
    const papers = await paperResponse.json() as Array<{user_id:string,storage_path:string}>;
    if (!papers.length || papers[0].user_id !== user.id) return reply({detail:"논문을 찾을 수 없습니다."},404,origin);
    const path = papers[0].storage_path;
    if (typeof path !== "string" || !path.startsWith(user.id + "/") || path.includes("..")) {
      return reply({detail:"파일 접근 권한이 없습니다."},403,origin);
    }
    const fileResponse = await supabaseRequest("/storage/v1/object/authenticated/papers/" + path.split("/").map(encodeURIComponent).join("/"),token);
    if (!fileResponse.ok) return reply({detail:"PDF를 읽을 수 없습니다."},502,origin);
    const contentLength = Number(fileResponse.headers.get("content-length") || "0");
    if (contentLength > MAX_BYTES) return reply({detail:"30MB 초과 파일입니다."},413,origin);
    const file = await fileResponse.arrayBuffer();
    if (file.byteLength > MAX_BYTES) return reply({detail:"30MB 초과 파일입니다."},413,origin);
    let pageCount: number, pages: Page[];
    try {
      ({pageCount,pages} = await extractPdf(file));
    } catch (error) {
      const reason = error instanceof Error ? error.message : "";
      const msg = reason === "PAGE_LIMIT" ? "1~300페이지 PDF만 지원합니다." :
        reason === "NO_TEXT" ? "본문 텍스트가 없습니다. 스캔 PDF는 OCR이 필요합니다." : "PDF를 해석할 수 없습니다.";
      return reply({detail:msg},422,origin);
    }
    const result = extractiveResult(pageCount,pages);
    const commonHeaders = { "Content-Type":"application/json", "Prefer":"return=minimal" };
    const save = await supabaseRequest("/rest/v1/analyses", token, {
      method:"POST", headers:commonHeaders,
      body:JSON.stringify({paper_id:paperId,user_id:user.id,status:"completed",model:"extractive-v1",result}),
    });
    if (!save.ok) return reply({detail:"분석 결과를 저장하지 못했습니다."},502,origin);
    const updateParams = new URLSearchParams({id:"eq."+paperId});
    const updated = await supabaseRequest("/rest/v1/papers?" + updateParams.toString(),token,{
      method:"PATCH",headers:commonHeaders,
      body:JSON.stringify({status:"completed",page_count:pageCount}),
    });
    if (!updated.ok) return reply({detail:"분석 상태 갱신에 실패했습니다."},502,origin);
    return reply({status:"completed",mode:"extractive",page_count:pageCount},200,origin);
  } catch(error) {
    console.error("Analysis request failed", error instanceof Error ? error.name : "unknown");
    return reply({detail:"분석 처리 중 서버 오류가 발생했습니다."},502,origin);
  }
}
Bun.serve({
  port: Number(Bun.env.PORT || "3000"),
  async fetch(req: Request) {
    const origin = req.headers.get("origin");
    const url = new URL(req.url);
    if (req.method === "OPTIONS") {
      return new Response(null, {status:204,headers:headersForOrigin(origin)});
    }
    if (req.method === "GET" && url.pathname === "/health") {
      return reply({status:"ok",service:"papersignal-api",mode:"extractive-v1"},200,origin);
    }
    const route = url.pathname.match(/^\/api\/analyze\/([0-9a-f-]+)$/i);
    if (req.method === "POST" && route && idPattern.test(route[1])) {
      return await analyze(req,origin,route[1]);
    }
    return reply({detail:"Not found"},404,origin);
  },
});
