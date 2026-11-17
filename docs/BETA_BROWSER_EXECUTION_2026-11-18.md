# PaperSignal beta browser execution record — 2026-11-18

Environment: ephemeral Vercel Sandbox papersignal-browser-anon-qa-20261118, Next.js dev server on localhost:3000, Playwright Chromium and WebKit with temporary system dependencies. Source from PR #16 at commit 9efae505bf7fce6808846291d11cd5246c6ddf7b. No production secrets, private PDF contents, real auth users or live backend mutations.

| Scope | Browser profile | Passed | Failed |
| --- | --- | ---: | ---: |
| Anonymous login and narrow screen | desktop Chromium | 2 | 0 |
| Anonymous login and narrow screen | Android Chromium emulation | 2 | 0 |
| Anonymous login and narrow screen | iPhone WebKit emulation | 2 | 0 |
| Synthetic Supabase UI flows | desktop Chromium | 3 | 0 |
| Synthetic Supabase UI flows | Android Chromium emulation | 3 | 0 |
| Synthetic Supabase UI flows | iPhone WebKit emulation | 3 | 0 |
| **Total** | | **15** | **0** |

Synthetic UI integration intercepted all requests to a fake local Supabase REST/Auth/Storage endpoint. It validates browser-driven React state and citation navigation but is **not** a live auth check, actual original PDF integrity verification, RLS enforcement, or actual deployed Preview test.

Remaining release gates: real verified email / Google OAuth login on protected Preview, signed uploaded PDF and iPhone physical-device rendering, two-user backend Storage/RLS check, 50-minute signed-link refresh, external SMTP, GitHub Actions startup incident, and an approved staged Production rollback rehearsal.

No production deployment, promotion, rollback, database migration, Railway Worker or analysis-engine modification occurred.
