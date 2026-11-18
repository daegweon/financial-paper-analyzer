# Browser QA as an automatic PaperSignal CI gate — 2026-11-19

Pull-request Checks now includes a separate `browser-qa` job with Playwright 1.65.1 running the actual Next.js UI on Ubuntu Chromium and WebKit.

## Test matrix

| Browser | Anonymous UI / narrow 320px | Synthetic login → original PDF citation → logout | Signing retry | A→B account switch |
| --- | ---: | ---: | ---: | ---: |
| Desktop Chromium | 2 | 1 | 1 | 1 |
| Android-emulated Chromium | 2 | 1 | 1 | 1 |
| iPhone-emulated WebKit | 2 | 1 | 1 | 1 |

Total: 15 browser cases. This is emulation, not physical Android/iPhone devices.

## Hard isolation

- The CI script refuses all targets unless `PAPERSIGNAL_BROWSER_QA_URL=http://localhost:3000` and the Supabase/API URLs and public key equal fixed synthetic values.
- Client requests to fake Supabase are intercepted by Playwright inside the browser, with synthetic users, papers, analysis, PDF and response failures.
- No real auth accounts, passwords, Supabase/Railway environment secrets, service-role key, private PDF, production mutations, videos, traces or screenshots. The temporary dev-server log is erased.
- Runs every PR and blocks merging if a browser scenario fails. Browser installation is limited to Chromium and WebKit. The owner-set GitHub Actions $1 budget is not changed.

## Execution

From frontend after `npm install` and `npx playwright install --with-deps chromium webkit`, use the exact fixed environment variables in `.github/workflows/checks.yml`, then run `bash scripts/test-browser-ci.sh`.

**Scope limitation:** Passing does not prove real OAuth, actual private PDF bytes or signed URL authorization, two-user Supabase HTTP RLS, long-duration link renewal, real iPhone Safari rendering, SMTP delivery, or any live production deployment.

The first GitHub Actions result must be observed before marking the new CI gate PASS.
