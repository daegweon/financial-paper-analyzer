# PaperSignal — Project State / Session Handoff

## Latest candidate / CI confirmation (2026-11-17)

- PR #7 remains draft; latest branch head after documentation updates: `343e53a98f32b8175d88ee093f26b6a6df56387e`. Latest code-changing commit: `e7782e1c1531dcc658a52246bfb61faa94d1d932`.
- GitHub Actions runs `43979921435` and `43979839645` both ended `startup_failure` before any jobs were created (0 jobs). This does not contradict the separate local result: candidate backend suite 123 passed, 1 skipped, 0 failed on Python 3.12.16 / PyMuPDF 1.26.3.
- Railway production API and Worker remain online on frozen production SHA `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`; candidate not deployed.
- Q0/Q1/Q2/P0 remain blocked. Do not merge or deploy.


## 2026-11-17 — pinned-runtime verification and next baseline gate

- Candidate branch: `experiment/engine-quality-v6-4-2-b01-b10-locked`; PR #7 remains draft. Latest candidate head before this handoff update: `e7782e1c1531dcc658a52246bfb61faa94d1d932`.
- Runtime verified: Python 3.12.16 / PyMuPDF 1.26.3, matching production pin.
- Backend tests on this runtime: frozen production 102 passed / 1 skipped / 0 failed; candidate 123 passed / 1 skipped / 0 failed. The skipped test is opt-in live E2E. GitHub Actions still fails `startup_failure` before creating jobs (latest run 43978680210, 0 jobs).
- Source fingerprint file: `benchmark/source_fingerprint_v6.4.2_2026-11-17.json`. Analysis version, prompt, schema, extraction, model config, requirements and Dockerfile hashes match; Gemini transport hash changed as intended. No secrets read or stored.
- B07 exact locked PDF: 23/23 pages extracted, zero empty pages, 69,414 chars, 73,295 prompt chars. Production/candidate text and prompt hashes match. Paired 10-run extraction+prompt A/B: p50 67.226 ms production vs 68.100 ms candidate (1.013 ratio), maxima 69.456 vs 68.968 ms. Extraction-only; not full-pipeline Q2.
- Historical Supabase results are mixed: B03-B08 v6.3.9, B01/B02/B09 v6.4.0, B10 v6.4.2. Only B10 is a historical v6.4.2 result (job-created-to-completed 27.701 s; worker-started-to-completed 26.575 s; two Gemini calls, 39,653 total tokens). Provider cost, per-call elapsed and RSS unavailable. Do not pool these mixed versions.
- Q0 remains BLOCKED: full same-version v6.4.2 baseline for all B01-B10 plus held-out H01/H02 Gemini runs still pending. Q1/Q2/P0 remain blocked. No production deploy or database mutation.
- Next: execute the frozen v6.4.2 end-to-end baseline on all 10 locked regression PDFs and both locked held-out PDFs in an isolated environment with provider usage/cost and peak RSS telemetry; then compare the telemetry-only candidate under matched conditions. Keep PR #7 draft until gates pass.


## 2026-11-17 — Production SHA and repeated CI confirmation

- Railway API and Worker latest successful deployments both remain on frozen production SHA 8cd5e37ee8eab3bf4b726b75af89e410ab48396e; candidate PR #7 has not been deployed.
- GitHub Actions runs 43969788375 and 43970441861 both ended startup_failure before creating jobs (0 jobs); repository tests did not execute. Retry was rejected with HTTP 403.
- Main API and Worker are online. No production deployment or data mutation occurred.

## 2026-11-17 — New candidate CI status

- New branch workflow run 43969788375 ended `startup_failure` before any job was created (0 jobs). Repository tests were not executed.
- GitHub API rejected retry with HTTP 403 (`This workflow run cannot be retried`). No test pass is claimed. Candidate remains draft and isolated; no production deployment.

## 2026-11-17 — B01-B10 exact SHA lock complete; v6.4.2 baseline pending

- Attached B01-B10 PDFs verified: 10/10 valid, unencrypted, 209 pages, 17,760,530 bytes. Exact SHA-256 hashes are in benchmark/legacy_regression_binary_lock_2026-11-17.json.
- First B01-B10 binary manifest commit: 342a2ed30b6e270c9a8f167d2a6cbc8dedeaf80c. Follow-up lock-reference commit: 14ed46fd032b42813dd0ccf372447bd71bd363aa. Candidate branch experiment/engine-quality-v6-4-2-b01-b10-locked starts from that follow-up commit.
- H01/H02 remain locked at 149311ec2993cac3bd410c10ac7feb202d582fc7. Both corpus lock commits are ancestors of the candidate.
- Exact frozen production extract_pages/sanitize_pdf_text logic reproduced locally on B01-B10 using PyMuPDF 1.26.7 (production pins 1.26.3): 209/209 pages with text, 691,985 chars; five-run local extraction-only preflight. Not production baseline/Q2.
- Current v6.4.2 full-pipeline baseline has not run. Q0 remains BLOCKED pending pinned runtime + Gemini baseline; Q1/Q2/P0 also BLOCKED. No production deploy or DB mutation.


- Added benchmark/parse_railway_telemetry.py on the candidate branch to aggregate Worker claims/completion/retry events with Gemini job/call IDs, model attempt outcomes, latency and token counts. Provider cost remains null until a dated price schedule is supplied. Missing token metadata is explicitly marked incomplete, not treated as a verified zero.
- Added four synthetic parser tests; these and the telemetry tests are committed but unexecuted because GitHub Actions startup_failure happens before any job is created.

- GitHub commit metadata independently confirms lock chronology: lock commit 149311ec2993cac3bd410c10ac7feb202d582fc7 at 2026-11-16T21:11:16Z; first commit on the new candidate branch 356b4d688657fc2c55b828d2b12b3062e1c9434b at 2026-11-16T21:15:33Z. The immutable lock preceded the candidate branch's first commit by 4 minutes 17 seconds.
## 2026-11-17 — Candidate-only Gemini telemetry added, not yet validated

- Candidate branch experiment/engine-quality-v6-4-2-heldout-locked adds per-job/per-call Gemini attempt telemetry (status, model, attempt count, elapsed, token usage), without changing prompt/schema/extraction/request body/retry policy/output version.
- Two mocked provider telemetry tests and one job-context integration assertion added. GitHub Actions startup_failure before job creation; no test execution or overhead measurement.
- Candidate main SHA-256 0886879ed41dec90450894cc14963ac7b3fd6daa7a44a631daae57ef48dbd8ed. Prompt/schema/extraction function hashes remain identical to frozen production.
- PR #5 Draft. No production changes. All Q0/Q1/Q2/P0 remain BLOCKED.

## 2026-11-17 — H01/H02 binary lock and new baseline candidate

- Exact user-uploaded H01/H02 PDF bytes locked: H01 40 pages / SHA-256 816e404d2f1dee7df84d52bf4238a75d7d777878cf100b42e3f220cc1da9b127; H02 30 pages / SHA-256 d385806b9a448e399dfc9f6017710561bf15bfd50ec514536303978ad07eb283.
- Lock commit 149311ec2993cac3bd410c10ac7feb202d582fc7; lock-reference commit 59b68fbc902bd17b656d606246d17b19a5614acf.
- Fresh branch experiment/engine-quality-v6-4-2-heldout-locked created from frozen production SHA 8cd5e37ee8eab3bf4b726b75af89e410ab48396e after the lock. PR #5 Draft. No engine code changes.
- Baseline source fingerprints saved in benchmark/baseline_lock_v6.4.2_2026-11-17.json on the candidate branch. Local extraction preflight uses PyMuPDF 1.26.7, not production pin 1.26.3; its timings are not Q2 evidence.
- Added repeatable source fingerprint and locked extraction-only preflight tools/tests. GitHub Actions still startup_failure before job creation; full tests not run.
- Original B01-B10 PDFs are absent from current Project file inventory; hashes missing. H01/H02 full Gemini runs, independent gold, full p95/cost/RSS and P0 remain missing. Q0/Q1/Q2/P0 BLOCKED. Production remains on 8cd5e37.

## 2026-11-17 — Held-out PDF lock utility test correction

- Local reproduction of the exact-byte lock utility tests initially exposed one incorrect expected error-message substring (test-only mismatch; utility correctly rejected the wrong record type).
- Updated the repository test to match the documented exception message. Re-ran the local synthetic reproduction: 7/7 passed.
- This does not constitute a verified run of the connected repository backend suite or GitHub Actions.
- Publisher PDF binary retrieval was unavailable from the isolated runtime. Exact SHA-256 remains null; both held-outs are preselected, not binary locked; Q0 remains blocked.

## 2026-11-17 — Held-out papers preselected; PDF binary lock still pending

- Registered two new open-access CC BY 4.0 finance papers (H01 40 pages, VAR/TVP-VAR + DMA/DMS + genetic algorithm; H02 30 pages, LASSO/Elastic Net/tree ML + FX/global portfolio) in benchmark/heldout_preregistration_2026-11-17.json.
- Exact publisher PDF URLs and DOI/version metadata are recorded. Execution runtime could not download raw PDF bytes, so SHA-256 fields remain null and Q0 is BLOCKED.
- Added benchmark/lock_heldout_pdfs.py and six synthetic tests to hash exact original bytes, check PyMuPDF page counts, and reject duplicates/regression overlap. No PDF files are stored in Git.
- The next release-eligible candidate branch must be created only after PDF bytes are supplied/obtained, the binary hashes are committed, and that Git commit is recorded as the lock commit. Existing experiment branch remains ineligible because tuning predated holdout preselection.
- No production change or user-data write.

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
