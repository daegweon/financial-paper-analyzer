import test from "node:test";
import assert from "node:assert/strict";
import { clampPdfPage, commitPdfPageInput, originalPdfPageUrl, pdfLinkNeedsRefresh } from "../lib/pdf-viewer.ts";

test("PDF page navigation clamps values to the original document range", () => {
  assert.equal(clampPdfPage(1, 20), 1);
  assert.equal(clampPdfPage(5, 20), 5);
  assert.equal(clampPdfPage(0, 20), 1);
  assert.equal(clampPdfPage(-3, 20), 1);
  assert.equal(clampPdfPage(99, 20), 20);
});

test("invalid or missing page counts still reject nonpositive pages", () => {
  assert.equal(clampPdfPage(3, null), 3);
  assert.equal(clampPdfPage(0, null), 1);
  assert.equal(clampPdfPage(Number.NaN, 10), 1);
});

test("uses the exact signed PDF URL with a browser-native page fragment", () => {
  const signed = "https://example.supabase.co/storage/v1/object/sign/papers/a.pdf?token=opaque";
  assert.equal(originalPdfPageUrl(signed, 7, 20), signed + "#page=7");
  assert.equal(originalPdfPageUrl(signed + "#old", 30, 20), signed + "#page=20");
  assert.equal(originalPdfPageUrl(signed, -1, 20), signed + "#page=1");
});

test("page field commits only a complete valid value, then clamps it", () => {
  assert.equal(commitPdfPageInput("24", 2, 80), 24);
  assert.equal(commitPdfPageInput("99", 2, 80), 80);
  assert.equal(commitPdfPageInput("0", 12, 80), 1);
  assert.equal(commitPdfPageInput("", 12, 80), 12);
  assert.equal(commitPdfPageInput(" ", 12, 80), 12);
  assert.equal(commitPdfPageInput("1e2", 12, 80), 12);
  assert.equal(commitPdfPageInput("1000000", 12, 80), 12);
  assert.equal(commitPdfPageInput("7", 12, null), 7);
});

test("private signed links refresh at 50 minutes and on invalid timestamps", () => {
  const t = 1700000000000;
  assert.equal(pdfLinkNeedsRefresh(t, t), false);
  assert.equal(pdfLinkNeedsRefresh(t, t + 49 * 60 * 1000), false);
  assert.equal(pdfLinkNeedsRefresh(t, t + 50 * 60 * 1000), true);
  assert.equal(pdfLinkNeedsRefresh(t, t - 1), true);
  assert.equal(pdfLinkNeedsRefresh(Number.NaN, t), true);
});
