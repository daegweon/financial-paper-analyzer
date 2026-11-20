/** Page navigation helpers for the original, unmodified PDF. */
export function clampPdfPage(requested: number, pageCount: number | null | undefined): number {
  const valid = Number.isFinite(requested) ? Math.floor(requested) : 1;
  const lowerBounded = Math.max(1, valid);
  return Number.isInteger(pageCount) && (pageCount as number) > 0
    ? Math.min(pageCount as number, lowerBounded)
    : lowerBounded;
}

export function originalPdfPageUrl(
  signedUrl: string,
  requestedPage: number,
  pageCount?: number | null,
): string {
  const base = signedUrl.split("#", 1)[0];
  return base + "#page=" + clampPdfPage(requestedPage, pageCount);
}

/** Commit a page field only on Enter/blur so multi-digit mobile input is possible. */
export function commitPdfPageInput(input: string, currentPage: number, pageCount: number | null | undefined): number {
  const trimmed = input.trim();
  if (!/^[0-9]{1,6}$/.test(trimmed)) return clampPdfPage(currentPage, pageCount);
  return clampPdfPage(Number(trimmed), pageCount);
}

/** Supabase private Storage URLs are issued for an hour; refresh before expiry. */
export function pdfLinkNeedsRefresh(issuedAt: number, now: number = Date.now()): boolean {
  return !Number.isFinite(issuedAt) || now < issuedAt || now - issuedAt >= 50 * 60 * 1000;
}
