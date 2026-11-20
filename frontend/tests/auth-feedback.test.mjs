import test from "node:test";
import assert from "node:assert/strict";
import { authCallbackError, cleanAuthErrorUrl } from "../lib/auth-feedback.ts";

test("recognizes a Google code-exchange failure without showing token fragments", () => {
  const error = authCallbackError(
    "?error=server_error&error_code=unexpected_failure&error_description=Unable+to+exchange+external+code%3A+4%2F0A",
    "#error=server_error&error_description=Unable%20to%20exchange%20external%20code%253A%204%252F0A&sb="
  );
  assert.match(error, /Client Secret/);
  assert.doesNotMatch(error, /4\/0A|4%2F0A/);
});

test("handles user-canceled Google login", () => {
  assert.match(authCallbackError("?error=access_denied", ""), /취소/);
});

test("does not mistake a valid PKCE callback for an error", () => {
  assert.equal(authCallbackError("?code=one-time-auth-code", ""), null);
  assert.equal(
    cleanAuthErrorUrl("https://financial-paper-analyzer.vercel.app/?code=one-time-auth-code"),
    null
  );
});

test("removes duplicated OAuth error data but preserves unrelated URL parameters", () => {
  const cleaned = cleanAuthErrorUrl(
    "https://financial-paper-analyzer.vercel.app/?next=library&error=server_error&error_code=unexpected_failure&error_description=Unable+to+exchange+external+code%3A+4%2F0A#error=server_error&sb="
  );
  assert.equal(cleaned, "/?next=library");
});

test("supports fragment-only OAuth errors", () => {
  assert.match(authCallbackError("", "#error=server_error&error_code=unexpected_failure"), /인증/);
  assert.equal(
    cleanAuthErrorUrl("https://financial-paper-analyzer.vercel.app/#error=server_error"),
    "/"
  );
});
