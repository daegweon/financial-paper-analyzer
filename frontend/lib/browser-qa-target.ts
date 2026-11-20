/**
 * Explicit, read-only browser QA target policy.
 * This code must never resolve to the production PaperSignal origin or arbitrary hosts.
 */
export type BrowserQaTarget = { origin: string; hostname: string; kind: "preview" | "local" };

const PREVIEW_HOST = /^financial-paper-analyzer-[a-z0-9]{8,24}-daegweonai-9583\.vercel\.app$/;
const FEATURE_ALIAS = /^financial-paper-analyzer-git-feat-[a-z0-9-]+-daegweonai-9583\.vercel\.app$/;

export function validateBrowserQaTarget(raw: string | undefined): BrowserQaTarget {
  if (!raw) throw new Error("PAPERSIGNAL_BROWSER_QA_URL must be set to an explicit Preview URL.");
  let target: URL;
  try { target = new URL(raw); }
  catch { throw new Error("Browser QA target must be a valid URL."); }

  if (target.username || target.password || target.search || target.hash || target.pathname !== "/") {
    throw new Error("Browser QA target may not contain credentials, a path, a query or a fragment.");
  }

  const hostname = target.hostname.toLowerCase();
  if (target.protocol === "http:" &&
      (hostname === "localhost" || hostname === "127.0.0.1") && target.port === "3000") {
    return { origin: target.origin, hostname, kind: "local" };
  }

  if (target.protocol === "https:" &&
      (PREVIEW_HOST.test(hostname) || FEATURE_ALIAS.test(hostname))) {
    return { origin: target.origin, hostname, kind: "preview" };
  }

  // In particular: reject the production domain and the git-main deployment.
  throw new Error("Browser QA allows only the PaperSignal feature Preview host or localhost:3000; never production.");
}
