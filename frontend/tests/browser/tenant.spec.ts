import { test, expect, openPaper, requireQaCredentials, signIn, signOut } from "./helpers";

test("after account switching, B cannot see or open A's paper", async ({ page }) => {
  const A = requireQaCredentials();
  const B = requireQaCredentials("_B");
  if (A.email.toLowerCase() === B.email.toLowerCase()) {
    throw new Error("Tenant QA requires two distinct, dedicated verified test accounts.");
  }
  const id = process.env.PAPERSIGNAL_QA_PAPER_ID;
  if (!id || !/^[a-f0-9-]{36}$/i.test(id)) throw new Error("A pre-existing QA paper UUID is required.");

  await signIn(page, A.email, A.password);
  const { dialog } = await openPaper(page, id);
  await expect(dialog).toBeVisible();
  await signOut(page);
  await signIn(page, B.email, B.password);
  await expect(page.locator('button[data-paper-id="' + id + '"]')).toHaveCount(0);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  // Browser UI isolation is not RLS verification. The separate backend
  // two-tenant integration E2E must also pass before public beta.
  await signOut(page);
});
