# PaperSignal — Project State / Session Handoff

Last updated: 2026-11-16 (Asia/Seoul)
Source of truth: Git branch feat/research-workspace-mvp
Open development PR: https://github.com/daegweon/financial-paper-analyzer/pull/2 (Draft; do not merge without release gates)

## Product north star

Build an evidence-first financial research workspace that accurately extracts research design, methodology, empirical findings, statistical significance and page-level PDF evidence; supports cross-paper comparison and a durable private research library. Prefer verifiable incompleteness over fabricated claims.

## Current progress estimate

Overall: approximately 72% (engineering estimate, not a measured product KPI).
- Core service and user workflows: ~85%
- Authentication and tenant isolation: ~80%
- Analysis engine reliability: ~70%
- Real-user workflow verification: ~75%
- Quantitative analysis-quality benchmark: ~40%
- Public beta readiness: ~45%

Do not raise these percentages without new verified evidence.

## Architecture

- Frontend: Next.js 16 / React 19 on Vercel.
- Auth, PostgreSQL and private PDF Storage: Supabase project hwmtayrecsfxernhssro, Seoul region.
- API: FastAPI + PyMuPDF on Railway.
- Durable queue/worker: Supabase job tables and independent Railway Worker.
- AI: Gemini primary gemini-3.5-flash-lite, fallback gemini-3.6-flash.
- Analysis version: new analyses use finance-structured-v6.3.
- GitHub repository: daegweon/financial-paper-analyzer.

## Verified complete

- Research library, upload, analysis history, search/sort, up-to-four-paper comparison, CSV export and A4 report.
- Private PDF Storage, signed source links, per-user RLS.
- Email/password and Google OAuth UI; a real Google PKCE login succeeded. Supabase logs recorded Google callback, token exchange HTTP 200 and user lookup HTTP 200.
- The Google identity is distinct from the legacy email identity. Legacy account has 11 papers / 44 analyses; Google account has three test papers / three analyses. Do not merge automatically.
- RLS rollback tests showed Google user can access own paper/analysis/job rows and the legacy account cannot read those rows; Google user initially sees none of the legacy account's records. Test rows were rolled back; no leftovers.
- Durable Worker: atomic claim, leases, heartbeat, retries, checkpoint resume, idempotent result persistence and terminal checkpoint cleanup.
- CORS accepts explicit origins plus a narrowly scoped Vercel Preview hostname regex for this Vercel project/team. Unrelated Vercel origins are rejected.
- PDF/model text is sanitized before JSONB persistence to prevent Postgres 22P05 from control characters.
- Three real Google-account PDFs completed v6.2 analysis: Acharya/Pedersen liquidity risk (50 of 60 pages scanned, 21 evidence quotes, 6 findings); Bank funding constraints (17 pages, 26 quotes, 0 structured findings); Monetary policy/funding cost/risk-taking (20 pages, 40 quotes, 0 structured findings). The latter two are known findings-quality gaps.
- Latest v6.3 Railway API and Worker BuildKit test stages each reported 78 passed, 1 skipped.
- Latest observed Railway services API, Worker and Extractive API are Online with zero active warnings/critical alerts. There are historical failed deployment attempts; inspect the latest deployment before future promotion.

## Current in-progress work

- v6.3: conditional table-first third-pass recovery for papers whose first two findings passes return no supported claims.
- v6.3 adds findings_coverage: supported / review_required / incomplete / not_assessable.
- Frontend displays findings coverage and rescue status.
- Latest UI commit: 264d79a0c062cee74581241526e8fcd4dbf571f5. Verify Vercel Preview build for this commit.
- Latest backend v6.3 commit: f30698cfa46766d3b8f96da4eeb9a14f9bbdee59.
- The three previously analyzed PDFs are v6.2 results; they have NOT yet been reanalyzed with v6.3. Reanalysis should be done only after preview/production deployment and should create a new analysis version without deleting v6.2 history.

## Known remaining work

### P0 — before public beta
1. Reanalyze the two known empty-findings papers with v6.3 and human-review recovered claims.
2. Run the full ten-paper benchmark, save a scorecard and complete human review of material findings/citations.
3. Complete a live two-user E2E with disposable accounts and real API/Worker upload-analysis.
4. Configure custom SMTP and verify external mailbox signup/confirmation; Supabase Free built-in SMTP is limited to team-member recipients and 2 emails/hour.
5. Resolve GitHub Actions runner provisioning: synthetic BuildFailed, startup_failure, zero jobs. Railway BuildKit is the backend fallback.
6. Verify production domain auth, Google sign-in, logout/relogin, PDF upload and analysis.
7. Review findings completeness and all material coefficient/significance claims against publisher PDFs.

### P1 — product quality and operations
- OCR for scanned/image-only PDFs.
- Expand beyond 50 scanned pages, especially appendix/table pages.
- Paper deletion, retention and account export lifecycle.
- Usage, token/cost limits, abuse controls and operational observability.
- Model/provider quality and cost comparison.

### P2 — long-term product
- Research knowledge graph and variable/methodology index.
- Cross-paper hypothesis and findings synthesis.
- Library-wide grounded AI research assistant.
- Team workspace, role management, billing and subscription.

## Accepted product decisions

- Keep Supabase on Free. Do not upgrade to Pro solely for Leaked Password Protection.
- Leaked Password Protection stays disabled; its single security-advisor WARN is an accepted residual risk. Do not claim it is enabled.
- No automatic account merging or cross-account data migration.
- No secrets in browser code, GitHub or chat; service-role and AI keys remain server-side.
- Public papers only for Gemini Free Tier testing; never upload confidential/internal/company/customer/personal data to the free tier.
- Preserve existing papers and analyses unless the user explicitly authorizes deletion.
- Prefer user-facing result status that distinguishes job completion from extraction quality.
- The user prefers the assistant to choose the best implementation path and report outcomes rather than repeatedly ask for design opinions.

## Session startup checklist

At the beginning of every new project session:
1. Read this file, docs/PROJECT_DECISIONS.md, and the last 20 entries of docs/PROJECT_CHANGELOG.md.
2. Inspect current Git branch/PR head, Railway active deployments, latest Vercel Preview, and Supabase job/result state before making claims.
3. Compare live code with this handoff. If they differ, update this state document first.
4. Continue the next P0 task unless the user explicitly changes priorities.

## Checkpoint cadence

Update PROJECT_STATE.md and append PROJECT_CHANGELOG.md:
- every five substantial development tasks/conversation turns;
- immediately after architecture/provider/schema decisions;
- after every production deployment, migration, or user-data E2E;
- before a session handoff.
