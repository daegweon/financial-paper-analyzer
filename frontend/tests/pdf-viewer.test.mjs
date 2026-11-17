import test from "node:test";
import assert from "node:assert/strict";
import { clampPdfPage, originalPdfPageUrl } from "../lib/pdf-viewer.ts";

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
