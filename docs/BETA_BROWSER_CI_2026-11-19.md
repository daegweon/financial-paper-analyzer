# Browser QA as an automatic PaperSignal CI gate — 2026-11-19

**Latest verification:** 24/24 Playwright scenarios PASS in real GitHub Actions run https://github.com/daegweon/financial-paper-analyzer/actions/runs/44403257361 (commit e069c96). The previous initial 15/15 suite also passed: https://github.com/daegweon/financial-paper-analyzer/actions/runs/44402413548 .

## Browser matrix

| Browser profile | Anonymous UI / 320px | Auth / PDF / retry / tenant | Junior study / quiz / citation | Total |
| --- | ---: | ---: | ---: | ---: |
| Desktop Chromium | 2 | 3 | 3 | 8 |
| Android-emulated Chromium | 2 | 3 | 3 | 8 |
| iPhone-emulated WebKit | 2 | 3 | 3 | 8 |
| **All profiles** | **6** | **9** | **9** | **24** |

Junior-focused checks verify 4-step learning completion persists after reopening the same paper, account B cannot inherit A's saved progress, switching from WM to technology leaves each role's progress independent, four-question quiz grading and reset work, and a learning-plan citation opens the right original PDF page **under synthetic mock conditions**.

## Isolation and use

- The CI shell script refuses execution unless all browser QA flags, URLs and the publishable key match exact dummy localhost values: `PAPERSIGNAL_BROWSER_QA=1`, URL `http://localhost:3000`, mocks `1`, Supabase `http://127.0.0.1:54321`, fake publishable key `sb_publishable_local_qa_only`, API `http://127.0.0.1:54322`.
- `frontend/scripts/test-browser-ci.sh` starts the actual Next.js app locally; Playwright intercepts Supabase Auth/REST/Storage with synthetic identity, paper, evidence and PDF responses.
- No production Supabase/Railway URLs, secrets, account creation, real uploaded files, customer data, screenshots, videos or saved auth state. The temporary dev-server log is removed.
- A failing scenario turns the GitHub Checks run red. Requiring status checks for merging is an additional repository branch-protection/ruleset setting; CI alone does not enforce a merge block.
- The job has a 15-minute limit and does not raise the user's GitHub Actions $1 budget. The project runs in a normal GitHub-hosted Ubuntu runner.

## Reproduction

From `frontend`, run `npm install`, `npx playwright install --with-deps chromium webkit`, set the exact dummy values listed in `.github/workflows/checks.yml`, then run `bash scripts/test-browser-ci.sh`. Browser test code lives in `frontend/tests/browser`.

**Important:** These are real browsers exercising **synthetic** login/storage, not real OAuth, a private uploaded PDF or an actual iOS Safari/Android device. Live Supabase RLS over HTTP, signed PDF bytes, SMTP, long-session link expiry and staged Production rollout remain separate release gates.
