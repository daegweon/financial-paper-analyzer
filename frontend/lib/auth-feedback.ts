/**
 * Parse only OAuth error indicators. Never render the opaque OAuth code,
 * access token or raw server response as a message to users.
 */
export function authCallbackError(search: string, hash: string): string | null {
  const query = new URLSearchParams(search.replace(/^\?/, ""));
  const fragment = new URLSearchParams(hash.replace(/^#/, ""));
  const error = query.get("error") ?? fragment.get("error");
  const code = query.get("error_code") ?? fragment.get("error_code");
  if (!error && !code) return null;

  const description = (query.get("error_description") ??
    fragment.get("error_description") ?? "").toLowerCase();

  if (error === "access_denied" || description.includes("user denied")) {
    return "Google 로그인이 취소되었습니다. 다시 시도해 주세요.";
  }

  if (
    description.includes("unable to exchange external code") ||
    code === "unexpected_failure"
  ) {
    return "Google 계정 인증 코드를 교환하지 못했습니다. Google Cloud의 OAuth Client ID와 Client Secret이 같은 클라이언트에 속하는지 확인하고, Supabase 인증 설정의 Site URL이 PaperSignal 주소인지 확인해 주세요.";
  }

  return "외부 계정 로그인에 실패했습니다. 잠시 후 다시 시도해 주세요.";
}

/** Hide stale OAuth errors from the browser address bar without touching PKCE codes. */
export function cleanAuthErrorUrl(href: string): string | null {
  const url = new URL(href);
  if (!authCallbackError(url.search, url.hash)) return null;
  for (const key of ["error", "error_code", "error_description", "sb"]) {
    url.searchParams.delete(key);
  }
  if (url.hash.startsWith("#error=") || url.hash.startsWith("#error_code=")) {
    url.hash = "";
  }
  return url.pathname + url.search + url.hash;
}
