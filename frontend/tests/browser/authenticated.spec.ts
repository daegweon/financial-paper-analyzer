import { test, expect, openPaper, requireQaCredentials, signIn, signOut } from "./helpers";

function paperId(): string {
  const id = process.env.PAPERSIGNAL_QA_PAPER_ID;
  if (!id || !/^[a-f0-9-]{36}$/i.test(id)) {
    throw new Error("PAPERSIGNAL_QA_PAPER_ID must refer to an existing multi-page analyzed QA paper UUID.");
  }
  return id;
}

test("verified email sign-in, original PDF bytes, cited page and keyboard close", async ({ page, request }) => {
  const { email, password } = requireQaCredentials();
  await signIn(page, email, password);
  const { row, dialog } = await openPaper(page, paperId());

  const openSource = dialog.getByRole("button", { name: "원문 PDF 함께 보기" });
  await expect(openSource).toBeVisible();
  await openSource.click();

  const frame = dialog.locator("iframe.inline-pdf-frame");
  await expect(frame).toBeVisible();
  const src = await frame.getAttribute("src");
  expect(typeof src === "string" && src.startsWith("https://")).toBe(true);
  const pdf = new URL(src as string);
  expect(pdf.hostname.endsWith(".supabase.co")).toBe(true);
  expect(pdf.pathname.startsWith("/storage/v1/object/sign/papers/")).toBe(true);
  expect(pdf.searchParams.has("token")).toBe(true);
  expect(pdf.hash).toBe("#page=1");

  // A framed PDF loading event cannot prove it is authorized. Fetch the
  // existing short-lived signed source with read-only HTTP and check PDF bytes.
  // Never print the URL, response body or signing token on failure.
  let signedPdfReadable = false;
  try {
    const response = await request.get(pdf.origin + pdf.pathname + pdf.search, {
      timeout: 20_000,
      failOnStatusCode: false,
    });
    signedPdfReadable = response.ok() && (await response.body()).subarray(0, 5).toString("ascii") === "%PDF-";
  } catch { signedPdfReadable = false; }
  expect(signedPdfReadable, "Original signed PDF was not readable as a real PDF.").toBe(true);

  // QA fixture must have at least two pages and one cited analysis finding.
  const next = dialog.getByRole("button", { name: "다음", exact: true });
  await expect(next).toBeEnabled();
  await next.click();
  await expect(frame).toHaveAttribute("title", / 2페이지$/);

  const pageField = dialog.getByRole("textbox", { name: "원문 PDF 페이지 번호" });
  await pageField.fill("1");
  await pageField.press("Enter");
  await expect(frame).toHaveAttribute("title", / 1페이지$/);

  const cited = dialog.locator("button.evidence-source-link").first();
  await expect(cited).toBeVisible();
  const caption = (await cited.innerText()).match(/원문 p\.(\d+) 함께 보기/);
  expect(Boolean(caption), "QA paper must have an existing positive page citation.").toBe(true);
  await cited.click();
  await expect(frame).toHaveAttribute("title", new RegExp(" " + Number(caption?.[1]) + "페이지$"));

  // On a browser that does not embed PDFs natively, a new-tab fallback exists.
  await expect(dialog.getByRole("link", { name: /새 탭/ })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(row).toBeFocused();
  await signOut(page);
});

test("injected PDF signing error exposes a recoverable manual retry", async ({ page }) => {
  const { email, password } = requireQaCredentials();
  await signIn(page, email, password);
  let injected = false;
  await page.route("**/storage/v1/object/sign/papers/**", async (route) => {
    if (injected) return route.continue();
    injected = true;
    return route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ message: "transient error; token=do-not-display" }),
    });
  });
  const { dialog } = await openPaper(page, paperId());
  expect(injected, "The app did not attempt to sign the original uploaded PDF.").toBe(true);
  await expect(dialog.getByRole("button", { name: "다시 연결" })).toBeVisible();
  await expect(dialog).not.toContainText("do-not-display");
  await dialog.getByRole("button", { name: "다시 연결" }).click();
  await expect(dialog.getByRole("button", { name: "원문 PDF 함께 보기" })).toBeVisible();
  await signOut(page);
});
