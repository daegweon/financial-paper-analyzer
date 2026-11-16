# PaperSignal — Project State / Session Handoff

## 2026-11-17 — Ongoing isolated engine-quality work (newest session checkpoint)

Branch: `experiment/engine-quality-v6-4-x`, PR #4 (Draft, targeting handoff branch). Full detail in `docs/ENGINE_QUALITY_PROGRESS_2026-11-17.md`.

- Added narrow PyMuPDF v6.4.2-compatible written-portfolio-fraction numeric audit (with unsupported-count/estimate tests).
- Added fail-closed Q0/Q1/Q2/P0 evidence evaluator and deterministic 18-item historical human review queue generator. Empty reviewer slots are NOT human gold.
- Read-only query confirms stored v6.3.9 review counts 4+6+1+2+3+2 = 18; original user data untouched.
- Tightened source/PDF SHA/page anchors, held-out segregation, and **made final_deploy_allowed always false** until separately verified external release authorization.
- Local reproduction of gate checks 9 passed; full backend CI not executed due GitHub Actions startup_failure. New Railway test resource creation failed Free plan limit. Preview-only Vercel build READY. No overall performance/accuracy improvement declared.
- Crucial: this test branch began tuning BEFORE new held-outs were SHA-locked; a future release-eligible candidate must be rebuilt from frozen baseline after independent held-out pre-registration. Do not retroactively claim Q0.
- All Q0/Q1/Q2/P0 remain BLOCKED. Production API + Worker on `8cd5e37ee8eab3bf4b726b75af89e410ab48396e` (v6.4.2), no production merge or release.

## 2026-11-17 — 사용자 최종 지시: OSS 종료, 기존 PyMuPDF 엔진 개선 → 임계점 충족 → 최종 배포

**이 항목이 아래 과거 '오픈소스 평가' 및 'v6.3.9가 운영'이라는 구형 계획보다 우선합니다.** 사용자는 추가 OSS/파서 교체 탐색을 **종료**하고 **현재 PyMuPDF / finance-structured-v6.4.2 운영 엔진**만 개선하기로 최종 결정했습니다. 현재 운영 엔진과 사용자의 기존 논문은 변경하지 않았습니다. 향후 개선은 독립 인간 골드·원문 인용 보존·전체 정확도·지연/메모리/비용·실제 사용자 E2E의 합격 기준을 충족한 다음에만 최종 배포합니다. 목표 달성 후 사소한 최적화 반복을 종료하며, 전체 엔진 성능을 해치는 개선은 거부/롤백합니다.

**새 세션 첫 작업:** `docs/SESSION_HANDOFF_NEXT.md`, `docs/ENGINE_QUALITY_RELEASE_PLAN_2026-11-17.md` 및 `benchmark/engine_release_gates_2026-11-17.json`을 읽으세요. GitHub 전용 문서 브랜치 `plan/engine-quality-release-handoff`를 현재 핸드오프 기준으로 사용합니다. 실제 엔진 개발은 이 브랜치를 출발점으로 별도 실험 브랜치에서 시작하고, 평가 게이트 전에는 운영 브랜치 `feat/research-workspace-mvp`에 push하지 마세요 (자동 Railway 배포 주의).

운영 코드 고정 SHA `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`; `ANALYSIS_VERSION="finance-structured-v6.4.2"`. Historical v6.3.9 결과(71 findings/53 screenpass/18 review-required)와 v6.4.2 validator로 historical result를 재검증한 54 screenpass/346 quotes는 구분합니다. **독립 human gold 아직 0명, 현재 전체-model 비교 503 오류로 미완료**, 품질 및 배포 게이트 모두 아직 BLOCKED. 코드 교체나 배포는 하지 않았습니다.

오픈소스 최종 실측: PyMuPDF의 346/346 기존 직접 인용 대비 Docling Parse 296/346, pypdfium2 292/346, pdfplumber 14/346. GROBID/MinerU는 현재 자원으로 미실행, Marker는 변환 실행 권한 오류로 정확도 미측정. OSS 전면 대체/운영 신규 도입 0건, 이후 비교 중단. 세부 보고서: `experiment/ranked-pdf-parser-trial/docs/RANKED_PDF_PARSERS_2026-11-17.md`.

메모리 제한: **이 프로젝트의 ChatGPT 메모리는 비활성화**되어 있습니다. 이 결정은 계정 메모리에 저장된 것이 아니라 **GitHub 문서로 지속 보존**됩니다. 새로운 세션에서도 해당 브랜치·문서를 먼저 조회해야 합니다.

---


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
- Quantitative analysis-quality benchmark: ~55%
- Public beta readiness: ~45%

Do not raise these percentages without new verified evidence. The v6.3.9 benchmark is complete, but page-level citation fidelity and independent human review remain open.

## Architecture

- Frontend: Next.js 16 / React 19 on Vercel.
- Auth, PostgreSQL and private PDF Storage: Supabase project hwmtayrecsfxernhssro, Seoul region.
- API: FastAPI + PyMuPDF on Railway.
- Durable queue/worker: Supabase job tables and independent Railway Worker.
- AI: Gemini primary gemini-3.5-flash-lite, fallback gemini-3.6-flash.
- Analysis version: current production API/Worker commit reports finance-structured-v6.3.9.
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
- Latest observed Railway API and Worker deployments are SUCCESS on branch commit d9c684e5a4bcccbb95feaed6385429bd8ff85567; API health returned HTTP 200.
- Reanalyzed B01–B10 on finance-structured-v6.3.9. All ten durable jobs completed; prior analysis records were retained.
- v6.3.9 ten-paper scorecard: 71 findings, 53 screen-passed, 18 review-required; screen-passed share 74.6%; weighted lexical Gold-fact screen 90.5%.
- Baseline mixed v6.1/v6.2 snapshot: 24 findings, 15 screen-passed, 9 review-required; screen-passed share 62.5%; weighted lexical Gold-fact screen 84.9%.
- Gold-fact metric is a lexical alias-presence screen, not human-verified precision/recall or page-level citation accuracy. Cost/latency comparison is unavailable because complete per-paper usage totals were not persisted.
- Worker logs showed a Gemini Free Tier quota/rate-limit event during B02; durable retry succeeded. Do not claim the Free Tier quota is sufficient for sustained public-beta traffic.

## Current in-progress work

- v6.3.9 ten-paper benchmark completed and recorded at benchmark/results/scorecard-v6.3.9-2026-11-16.md.
- Do not begin v6.4 or add broad new heuristics until the remaining 18 review-required findings receive targeted human audit.
- Prioritize B01, B02, B09 and B10 because they have the largest review-required counts (4, 6, 3 and 2 respectively).
- Validate every material coefficient, direction, p-value/significance legend, table/figure reference and page citation against the exact stored PDF.
- Inspect B02's Gemini quota/retry event and define a sustainable provider quota/cost plan before public beta.
- Capture per-job model, prompt/candidate token counts, provider attempts, wall-clock latency and estimated cost in a durable usage record before claiming cost/latency improvements.
- Preserve all historical analysis versions; do not delete or overwrite prior results.

## Known remaining work

### P0 — before public beta
1. Complete targeted human review of all 18 review-required findings, starting with B01, B02, B09 and B10.
2. Audit all material coefficient, sign, p-value/significance legend and page-citation claims against the exact PDFs; record reviewer decisions and citation-level scorecard.
3. Persist per-job model/token/provider-attempt/latency/cost telemetry and define sustainable quotas; B02 hit Gemini Free Tier quota before succeeding on retry.
4. Complete a live two-user E2E with disposable accounts and real API/Worker upload-analysis.
5. Configure custom SMTP and verify external mailbox signup/confirmation; Supabase Free built-in SMTP is limited to team-member recipients and 2 emails/hour.
6. Resolve GitHub Actions runner provisioning: synthetic BuildFailed, startup_failure, zero jobs. Railway BuildKit is the backend fallback.
7. Verify production domain auth, Google sign-in, logout/relogin, PDF upload and analysis.

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
