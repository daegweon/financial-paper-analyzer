# PaperSignal — Project closeout checklist

**Date:** 2026-11-22 (KST)  
**Repository:** https://github.com/daegweon/financial-paper-analyzer  
**Production:** https://financial-paper-analyzer.vercel.app  
**Current main:** documentation closeout committed; query GitHub for the current HEAD (application runtime unchanged from release commit `0c2e5b10`)

## Administrator navigation feature release deployment

- Application commit: `1b543c07840e69873b74c90571226ca6a19c0b31`.
- Vercel Production deployment: `dpl_Gqps3z6RJedj6YpDSgU78UL1SX1S` — READY, canonical alias assigned.
- Railway API deployment: `981f77e2-51ae-49b4-84f0-214b05e1fd68` — SUCCESS, Online 1/1.
- Railway Worker deployment: `4a6c98ea-28eb-4b58-b52e-cc9e103afe32` — SUCCESS, Online 1/1.
- Subsequent documentation-only commits triggered automatic redeployments. Always query Vercel/Railway live state for current deployment IDs; do not treat the feature-release IDs above as necessarily the latest deployment.
- Railway build verification for this application release: **250 passed, 1 skipped**. GitHub Actions were not run.

## Latest administrator-navigation release — 2026-11-22

- Administrator workspace menu added to the left sidebar; mobile header shortcut shown when the sidebar is hidden.
- Visibility is based on a server-verified Supabase UUID allowlist via `GET /api/admin/access`, not a client-side email check.
- The endpoint returns only a boolean flag; admin summary and budget APIs still enforce their own authorization.
- Three backend tests cover admin, non-admin and unauthenticated cases.
- Application commit: `1b543c07840e69873b74c90571226ca6a19c0b31`.
- Vercel Production deployment: `dpl_Gqps3z6RJedj6YpDSgU78UL1SX1S` — READY, canonical alias assigned.
- Railway API deployment: `981f77e2-51ae-49b4-84f0-214b05e1fd68` — SUCCESS, Online 1/1.
- Railway Worker deployment: `4a6c98ea-28eb-4b58-b52e-cc9e103afe32` — SUCCESS, Online 1/1.
- Railway backend test build: 250 passed, 1 skipped. GitHub Actions: not run.

See [Administrator dashboard navigation](ADMIN_DASHBOARD_NAVIGATION_2026-11-22.md) for the full UI/API/security contract.

## Release state

- [x] Core research library and authenticated user workspace released.
- [x] Durable analysis queue and Railway API/Worker released.
- [x] Gemini-backed financial-paper analysis and page-level evidence released.
- [x] Public finance-paper discovery and private PDF import released.
- [x] Junior paper-reading, visual-reading and comprehension learning features released.
- [x] Inline hover evidence preview and click-to-open citation popover released.
- [x] Reader control baseline corrected: UI label 100% equals the former 90% visual size.
- [x] Equation parameter explanations removed; formulas retained.
- [x] Comprehension-check typography enlarged.
- [x] Duplicate variable evidence citations grouped under the parent icon; unique evidence remains local.
- [x] Administrator AI usage ledger and monthly budget reporting implemented.
- [x] Administrator-only workspace navigation added; `/api/admin/access` confirms the server allowlist before displaying the dashboard menu.
- [x] Administrator navigation is available on desktop sidebar and mobile header; visibility endpoint has admin/non-admin/unauthenticated tests.
- [x] Supabase production migration ledger checked: 14 versions applied through `20261121032957`.
- [x] Vercel Production READY; Railway API and Worker Online 1/1 at the latest status check.
- [x] 15 obsolete/duplicate PRs closed; branches and commit history retained.
- [x] GitHub open Issues checked: 0.
- [x] GitHub Actions were not run for this closeout.

## Remaining external / human-owned checks

These items cannot be truthfully completed by source-code or documentation changes alone.

| Priority | Item | Current status | Required owner/action |
|---|---|---|---|
| High | B01–B10 finance expert review | 6 findings across 5 claim units remain `review` | Qualified finance reviewer checks publisher PDFs and signs off |
| High | Public-paper live integration | OpenAlex and publisher PDF calls are mocked in CI | Run one real Production search and permitted PDF import |
| High | iOS Safari / Android Chrome | Native-device PDF and session behavior unverified | Test on actual devices |
| High before external beta | SMTP / sender domain | External provider not configured | Configure custom SMTP and test signup/reset email |
| Medium | Leaked-password protection | Supabase Security Advisor WARN | Project owner decides/enables in Auth settings |
| Medium | Gemini billing mode | Unknown | Confirm Free or Paid Standard in Google AI Studio; never infer |
| Medium | GitHub Actions spend cap | Account-level setting not readable through repository connector | Check account billing settings if $0 stop-usage protection is required |
| Medium | Production Google OAuth regression | Earlier Preview OAuth flow passed; latest Production-domain retest not recorded | Sign in/out once on canonical domain |

## Supabase Advisor snapshot (2026-11-22)

- **WARN:** leaked-password protection disabled.
- **INFO:** `ai_admin_settings` and `ai_usage_events` have RLS enabled without policies. This is intentional for the service-role-only accounting tables; browser roles have no direct grants.
- **INFO:** `ai_usage_events_provider_model_created_idx` unused at the time of the check. Do not drop it without workload review.
- **Health:** no notices.

## Intentionally deferred — not release blockers

- OCR for scanned/image-only PDFs.
- Separate extraction/rendering of figures and tables as image assets.
- Interactive per-paper model/algorithm simulators.
- Additional paper-provider/DOI integrations beyond OpenAlex.
- Structured DB provenance fields for imported-paper DOI, original URL and license.

## Project disposition

The planned product-development scope is concluded. The application is released and the repository is closed to routine feature work. Remaining items above are explicitly external/human-owned operational checks, not hidden implementation tasks. Keep the analysis engine frozen and move to maintenance-only operation. Reopen development only for a reproducible production defect or a new, explicit scope decision.

## Guardrails

- Keep the analysis engine frozen; no further prompt/model tuning for cosmetic reasons.
- Do not claim benchmark accuracy from alias coverage or the AI second-pass audit.
- Do not treat the AI cost report as an invoice or hard spending cap.
- Do not run GitHub Actions unless explicitly requested.
- Do not create unnecessary deployments or apply unnecessary database migrations.
- Preserve old PR branches/commits unless separately approved for deletion.

## References

- [Project handoff](PROJECT_HANDOFF.md)
- [Administrator dashboard navigation](ADMIN_DASHBOARD_NAVIGATION_2026-11-22.md)
- [Public paper discovery/import runbook](PUBLIC_PAPER_DISCOVERY_IMPORT_2026-11-21.md)
- [Benchmark and human-review protocol](../benchmark/README.md)
- [Six-finding second-pass audit](../benchmark/results/assistant-second-pass-evidence-audit-2026-11-20.md)
- [Production integration verification](production-e2e-verification.md)
- [Beta release runbook](BETA_RELEASE_RUNBOOK.md)
