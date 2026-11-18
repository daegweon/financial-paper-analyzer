# PaperSignal — Consolidated beta release candidate gates (2026-11-19)

Release candidate: https://github.com/daegweon/financial-paper-analyzer/pull/18 (Draft, base main, head fa526369, 0 commits behind latest main at integration). Engine frozen; no Production mutation on this milestone.

## Verified automated / provider checks

| Gate | State | Evidence / qualification |
| --- | --- | --- |
| GitHub Actions real runner allocation | PASS | https://github.com/daegweon/financial-paper-analyzer/actions/runs/44368096096 |
| Candidate Python backend regression CI | PASS | https://github.com/daegweon/financial-paper-analyzer/actions/runs/44370323274 |
| Candidate frontend lint/test/Next.js production build | PASS | Same Checks run, frontend job |
| Real PostgreSQL 17 security migration test in isolation | PASS | Same Checks run, db-policy job: cross-owner RLS and Storage metadata, owner upload defaults, deny client-forged analyses/jobs/status, permit service-role results |
| Candidate Vercel Preview production build | READY | Feature-preview deployment, not Production or authenticated E2E |
| Core Railway API and Worker current deployment | Online | Production health overview, 0 failures in recent 24h; still old code, not candidate |
| Supabase advisors | No ERROR or CRITICAL | Health 0 findings, security one accepted Leaked Password Protection WARN (Free-tier limitation) |
| Local isolated browser UI tests | 15/15 PASS | Chromium desktop, Android-emulated Chromium, iPhone-emulated WebKit with synthetic Supabase responses, not real accounts |

## Mandatory pending live gates (not passed)

1. **Real authenticated Preview browser test:** actual Google and verified-email login to the protected candidate Preview; open a real existing public/synthetic PDF and cite pages; verify authorization errors, keyboard and original bytes. Owner can perform Google consent; the assistant has no authorized identity or mailbox session. Do not disable Vercel protection.
2. **Two-user live E2E:** opt-in `backend/tests/test_live_e2e.py` with disposable test accounts and synthetic uploaded PDF, completed API/Worker analysis, signed file and RLS denial for user B. Requires verified secrets in the private runner; no unattended run on PR changes. If job remains active, retain fixture for Worker safety.
3. **External email signup:** configure and verify custom SMTP and real inbox delivery before public signup. Supabase Free built-in SMTP is insufficient for arbitrary public email recipients. Do not disable email confirmation.
4. **Mobile native smoke:** iOS Safari actual device and Android Chrome original PDF embedded/new-tab fallback, page navigation, 200% zoom, keyboard/VoiceOver announcements; renewal after 50 min, account switch isolation.
5. **Backend/API rollout BEFORE DB grant revocation:** the current running Railway API still registers jobs using client JWT. Deploy candidate API with server-side key, verify owned job enqueue and unauthorized paper 404, check retries and Worker health before the migration. Do not deploy the Worker just to change API behavior.
6. **Security migration:** after step 5 succeeds, apply ONLY `supabase/migrations/20261117215315_beta_server_owned_result_writes.sql` using an explicitly reviewed migration mechanism. Existing Supabase migration history versions differ from baseline repo file names. Do not `supabase db push` indiscriminately. Run read-only postgrant assertions `supabase/tests/beta_write_grants.sql` and the advisors.
7. **Staged Production preview and rollback:** build a Production-environment release with `--skip-domain`; retest protected URL and core flows. Only after explicit approval promote that exact immutable Production deployment. Record eligible prior deployment ID and exercise rollback/forward promotion with no schema downgrade.
8. **Financial research quality handoff:** targeted human review of all remaining screen-required findings and their cited PDF pages, and public-beta AI quota/budget policy. A completed analysis is not a verified empirical finding.

## Rollback / nonnegotiable safety rules

- Existing Production Vercel main deployment when checked: `dpl_33BMEgCAGgZVW9XWDk2n2VvFgmZg` (READY, commit `f5d0345cf4d4f507c0c4a521bfea71adbc14541d`). Prior READY candidate `dpl_BSDxZJFMPXrpFNvaf6i38iGScANj`.
- Railway API old deployment `17c9134b-f49c-4358-a879-7ca77b55b936`; Worker old deployment `dc501061-d434-454a-bc7d-4658b991a2f1`.
- Once DB revokes client analysis writes, do NOT roll the API backward to a version that requires browser INSERT, as it will break queueing. Roll forward to the verified server-owned API or explicitly review any exceptional rollback.
- Do not raise GitHub Actions $1 budget automatically. Do not turn public/protection settings off to bypass a failed gate.
- No Production alias assignment, privileged live E2E, new paid Supabase project, destructive migration, or auth secret disclosure is authorized by build readiness alone.

## Decision

**Technical candidate assembled, not yet beta launch-ready.** Automated gates pass, real auth/Storage E2E and release-time server/database sequencing remain pending.

## Browser smoke as an automatic PR gate — 2026-11-19

The release candidate now runs 15 synthetic, localhost-only Playwright scenarios on three browser profiles in a dedicated `browser-qa` GitHub Actions job; first CI execution is pending. See `docs/BETA_BROWSER_CI_2026-11-19.md`. This does not satisfy live authentication, PDF Storage or device release gates.
