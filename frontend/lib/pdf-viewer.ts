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
