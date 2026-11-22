# PaperSignal — Project closeout checklist

**Date:** 2026-11-22 (KST)  
**Repository:** https://github.com/daegweon/financial-paper-analyzer  
**Production:** https://financial-paper-analyzer.vercel.app  
**Current main:** `4595cd33d33c939e1490d9bd5375dec833594b10` (documentation closeout; application runtime unchanged from `0c2e5b10`)

## Latest deployment

- Vercel Production deployment: `dpl_HX8eqE5j3HXr4bxXc82kZhnTcgay` — READY, canonical alias assigned.
- Railway API deployment: `9a89be17-5408-41a2-91d0-cc7a7ca4779c` — SUCCESS, health check passed.
- Railway Worker deployment: `0b23b313-1cf0-468e-ab3e-f06087cd1320` — SUCCESS, worker started.
- These deployments follow the documentation-only closeout commit; application runtime code is unchanged from the previous release.

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

## Guardrails

- Keep the analysis engine frozen; no further prompt/model tuning for cosmetic reasons.
- Do not claim benchmark accuracy from alias coverage or the AI second-pass audit.
- Do not treat the AI cost report as an invoice or hard spending cap.
- Do not run GitHub Actions unless explicitly requested.
- Do not create unnecessary deployments or apply unnecessary database migrations.
- Preserve old PR branches/commits unless separately approved for deletion.

## References

- [Project handoff](PROJECT_HANDOFF.md)
- [Public paper discovery/import runbook](PUBLIC_PAPER_DISCOVERY_IMPORT_2026-11-21.md)
- [Benchmark and human-review protocol](../benchmark/README.md)
- [Six-finding second-pass audit](../benchmark/results/assistant-second-pass-evidence-audit-2026-11-20.md)
- [Production integration verification](production-e2e-verification.md)
- [Beta release runbook](BETA_RELEASE_RUNBOOK.md)
