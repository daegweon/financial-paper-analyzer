# PaperSignal — Project State / Session Handoff

## 2026-11-17 — 주니어 금융 실무 학습 기능 4종 추가, 전체 개발 추정 ~74%

- 사용자 지시: 개발 진행률을 높이되 **금융 기초가 부족한 주니어 실무자**를 최우선 사용자로 유지.
- 스택형 격리 브랜치 `feat/junior-role-guides-and-briefing`; **Draft PR #10**: `https://github.com/daegweon/financial-paper-analyzer/pull/10`. PR #9 `feat/junior-first-paper-reading`에 쌓여 있고, PR #9는 PR #8 `feat/research-job-status-resilience`에 쌓여 있음. 세 PR 모두 운영 미병합.
- 추가 구현: (1) 추출된 방법론 필드에 명시된 금융모형명에만 연결한 '왜 쓰는가·가정·주의점' 교육 카드, (2) WM·리스크·리서치·상품기획·개발데이터 5개 직무별 학습 질문, (3) 원문 연구질문/모형/표본과 자동 1차 대조 통과 인용(최대 2건)·페이지·한계를 포함한 1쪽 브리핑 초안 복사/TXT 내보내기, (4) 학습자가 스스로 원문을 대조하는 3문항 확인.
- **엄격한 소스 분리:** 논문에서 실제 추출한 내용 / 독립적인 금융지식 설명 / 직무별 가상 점검 질문을 분리. 근거 없는·review_required Finding은 브리핑에서 제외. 원문 인용문의 줄바꿈을 보존하고 화면 자동 근거 대조는 독립 인간 검증이 아님을 명시. 새로운 Gemini 호출/소스 분석 로직 수정/매매 추천 없음.
- 코드: `frontend/lib/junior-workflow.ts`, `frontend/components/JuniorWorkplaceGuide.tsx`, `frontend/components/JuniorWorkplaceGuide.module.css`, `frontend/tests/junior-workflow.test.mjs`, `frontend/app/page.tsx`; `frontend/package.json`, `frontend/tsconfig.json` 갱신.
- 별도 Vercel 샌드박스 실측: `npm run lint` **TypeScript 통과 + 단위 테스트 총 38/38 통과**(OAuth 5, durable-job 13, junior reading 7, 새 role-method-briefing 13). `NEXT_TELEMETRY_DISABLED=1 npm run build` **Next.js 16.4.6 성공**. 기존 Gemini/PyMuPDF 백엔드 테스트는 이번 UI-only 변경에서 다시 실행하지 않음.
- 진행률 기록: 주관적 코어 UX 엔지니어링 추정 87% → 91%(가중치 25%), 전체 **72.75% → 73.75% ≈ 74%**. 기능 완료도 추정치이며 **실사용 주니어 이해도 개선률이나 출시 적합성 인증 아님**. 공개 베타 준비 추정 ~45%, Q0/Q1/Q2/P0 **0/4 통과**, 운영 배포 불가.
- 자세한 구현·검증: `feat/junior-role-guides-and-briefing/docs/JUNIOR_WORKFLOW_PACK_2026-11-17.md`; 진행률 산정: 같은 브랜치 `docs/PROJECT_PROGRESS_2026-11-17.md`.
- 추가 QA Supabase Secret Key는 사용자가 지금 입력할 수 없어 **보류 유지**. 다음은 실제 주니어 금융 사용자 검증, 원문 PDF·도표 내비게이션, 자가 학습 도구의 사용성 테스트, 프런트엔드 사용자 E2E·시각적 퇴행 점검. 배포는 Q0/Q1/Q2/P0 합격 후.
  
## 2026-11-17 — 제품 방향 확정: 금융 기초가 부족한 주니어 실무자 우선

- **새 핵심 페르소나:** 금융 지식이 풍부한 전문 퀀트보다, 금융업에 종사하지만 투자·금융공학·계량경제 기초가 부족한 **주니어 실무자**. 제품 약속은 `논문 이해 → 원문 근거 검증 → 업무 적용 시 고려사항`을 학습시키는 것.
- 이 방향은 단순한 카피 수정이 아니라 전체 UX·로드맵 우선순위 변경이다. 다만 기존 분석 엔진의 정확도, 인용 근거, 저장 보존 원칙은 그대로 유지하며 Q0/Q1/Q2/P0 품질 기준을 낮추지 않는다.
- 기능 구현: `feat/junior-first-paper-reading` / **Draft PR #9**, 기존 Draft PR #8에 스택. 새 `주니어를 위한 3분 논문 읽기`를 결과 상세 화면 최상단에 배치. 원문 기반 연구 질문·방법·검증 화면 1차 통과 결과 최대 3건과 실제 인용문/PDF 페이지, 개념 학습 카드, 업무 적용 전 질문 3개 제공.
- 신규 학습 콘텐츠는 반드시 **원문 유래 주장**, **일반 금융 교육용 개념**, **실무 적용을 위한 가상 점검 질문**으로 표시를 분리. `screen_passed`는 독립 인간 검증이 아니라 자동 1차 스크린이며, 누락·검증 불충분 결과는 추측으로 대체하지 않음. 매매·투자 추천 없음.
- 실제 isolated Vercel sandbox 검증: `npm run lint` TypeScript 통과 + **25/25 단위 테스트**(기존 5 OAuth/13 durable-job + 신규 7 주니어 가이드). `npm run build` Next.js 16.4.6 통과. 생산환경 배포 안 함.
- 전략 문서 `feat/junior-first-paper-reading/docs/JUNIOR_FIRST_PRODUCT_DIRECTION_2026-11-17.md`. PR #9: `https://github.com/daegweon/financial-paper-analyzer/pull/9`.
- **다음 개발 우선순위:** (1) 자주 등장하는 모델을 “왜 이 방법을 쓰는가/가정과 한계”로 설명, (2) 직무별 WM·리스크·리서치·상품/기술 연결 학습, (3) 원문 인용 PDF·표·그래프 탐색, (4) 한 장짜리 근거·한계 구분 보고서. 그다음 문서 질문/퀴즈. 모호하거나 검증되지 않은 인용·수치의 자동 미화 금지.
- 개발 추정 진행률 **약 73% 유지** (정식 주니어 사용자 대상 이해도 테스트 미실시). 출시 게이트 **0/4** 미충족 및 운영 SHA 고정. 새 Supabase 키 요청/실험 트랙은 사용자 요청대로 보류.
  
## 2026-11-17 — 본 프로젝트 복원 기능 개발 완료 / 진행률 재산정

- 새 Supabase `papersignal-benchmark` Secret Key 연결은 사용자의 요청에 따라 계속 보류. 운영 Supabase와 배포 서비스 변경 없음.
- 격리된 메인 제품 개발 브랜치 `feat/research-job-status-resilience`, Draft PR **#8**: https://github.com/daegweon/financial-paper-analyzer/pull/8.
- **브라우저 재접속 후 진행 중 분석 복원 UI 구현**: 논문을 열면 RLS 보호 `analysis_jobs`에서 `queued`/`processing` 작업을 다시 검색, 상세 팝업·논문 목록·작업 이력에서 `이어 확인` 버튼 제공.
- 새 분석 시작 직전에 현재 작업을 다시 조회하여 기존 Job이 있으면 **새 POST 없이 GET 상태 추적**. 조회 실패 시 안전하게 새 작업 등록 보류. 탭 이동/팝업 닫기 시 오래된 브라우저 상태 폴링을 종료하고 서버 Worker 분석은 유지.
- 기존 `Failed to fetch` 오류 대신 한국어 설명, 일시적 408/429/5xx 대응 및 제한된 재조회 구현. 기존 PDF/Gemini 엔진 코드 미변경.
- 독립 Vercel sandbox에서 `npm run lint`: **TypeScript 통과 + 18개 테스트 모두 통과**(기존 인증 5, 신규 분석·복원 13). `npm run build`: **Next.js 16.4.6 운영 빌드 성공**. 실사용 E2E는 아직 미실행.
- **전체 엔지니어링 추정 72.25% → 72.75% ≈ 73%**. 근거: 제품 UX 작업영역(전체 가중치 25%) 85%→87% 증가, 나머지 영역 추정치 유지. 정밀한 KPI나 출시 확률이 아님. **출시 게이트 Q0/Q1/Q2/P0 = 0/4 완료**, 베타 출시 준비 추정치 ~45% 유지.
- 변경 근거 문서: `feat/research-job-status-resilience/docs/PROJECT_PROGRESS_2026-11-17.md`. PR #8은 Draft, 출시 게이트 통과 전 본 운영 병합·배포 금지.
- 다음 제품 개발 우선순위: 실제 브라우저 재접속·동시 탭 E2E, 원문 근거/방법론 UX, 미분석·실패 논문의 회복 흐름. 비운영 DB 비밀키를 재요청하지 말 것.

## 2026-11-17 — 사용자 지시: 신규 Supabase 키 설정 보류, 본 서비스 개발 복귀

- 사용자 현재 새 `papersignal-benchmark` Supabase 프로젝트의 Secret Key를 입력할 수 없음. **새 QA DB 연결 및 v6.4.2 전체 Gemini 기준선 실험을 보류**하고 반복적인 키 요청 없이 본 프로젝트의 비밀키 불필요 작업으로 계속 진행한다.
- 전체 개발률은 기존 문서의 주관적 엔지니어링 추정치 **약 72%**를 유지한다. 정확한 방식: 제품 UX 25% × 85% + 인증·사용자 격리 20% × 80% + 분석엔진 25% × 70% + 실사용 흐름 10% × 75% + 정량 검증 10% × 55% + 베타 준비 10% × 45% = **72.25% ≈ 72%**. **출시 게이트 Q0/Q1/Q2/P0는 0/4 통과**이며 베타 준비도는 별도 추정치 45%; 개발률을 출시 승인률로 오해하면 안 됨.
- 운영 고정 SHA `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`에서 격리 브랜치 `feat/research-job-status-resilience`를 생성하고 PaperSignal 프런트엔드 내구성 향상 구현.
- Draft PR #8: `https://github.com/daegweon/financial-paper-analyzer/pull/8`. 일시적 408/429/500/502/503/504 및 네트워크 오류의 작업 상태 재조회, 최초 POST 자동 중복 제출 방지, 한국어 `Failed to fetch` 대체 안내, 다른 논문으로 이동/닫기 후 이전 결과 팝업 재오픈 방지.
- isolated Vercel 샌드박스: `npm run lint` (**tsc 통과 + 테스트 15/15 통과**, 새 10/기존 OAuth 5), `npm run build` (**Next.js 16.4.6 최적화 빌드 성공**). PR diff는 `frontend/*` 4개 파일 + `docs/PROJECT_PROGRESS_2026-11-17.md` **총 5개**뿐; 백엔드/Gemini/PyMuPDF/운영 API/Worker/DB에 수정 없음.
- 운영 Railway `papersignal-api`와 `papersignal-worker` 모두 online, 기존 배포 ID 유지. PR #8은 Draft, **병합·운영 배포 금지**.
- 다음 우선 작업: 새로운 Secret Key 없이도 가능한 분석 작업 재연결 UX, 연구 라이브러리 지속성, 서지/근거 정렬 개선, 기존 고정 PDF 기반 회귀 테스트 및 인간 검토용 증거 패키지 준비. 엔진 품질 골드/전체 모델 A/B/베타 E2E의 충족을 추측하지 말 것.
- 자세한 진행률 산정: `feat/research-job-status-resilience/docs/PROJECT_PROGRESS_2026-11-17.md`.

## 2026-11-17 — 3단계 독립 Supabase 프로젝트 구축 완료 (새 체크포인트)

- 사용자 승인 후 별도 Supabase 프로젝트 `papersignal-benchmark` 생성: ID `cstaglfqviojdxisckjm`, 조직 `eevee`, 서울 리전, 생성 견적 월 $0, 상태 `ACTIVE_HEALTHY`.
- 운영 저장소 SQL 9개 + 전용 private JSON artifact bucket 1개 마이그레이션 적용. 신규 `papers`/`analyses`/`analysis_jobs`/`analysis_job_checkpoints` 모두 RLS ON, 사용자/논문/분석/Job 0건, PDF/결과 버킷 비공개.
- Worker RPC 4개는 `anon`/`authenticated` 실행 불가, `service_role`만 허용함을 실측 확인. Security Advisor 0건, Performance Advisor는 빈 DB 미사용 인덱스 11개 INFO.
- Railway 실험 서비스 `papersignal-table-benchmark`의 `SUPABASE_URL` 및 publishable key를 신규 QA 프로젝트로 변경. 운영 서비스 역할 키를 사용하지 않도록 `SUPABASE_SERVICE_ROLE_KEY`를 무효 플레이스홀더로 교체. `BENCHMARK_ALLOWED_SUPABASE_HOST=cstaglfqviojdxisckjm.supabase.co`, `BENCHMARK_ENABLE_ISOLATED_WRITES=false`로 쓰기 계속 차단.
- **사용자 조치 필요:** 새 Supabase 프로젝트 Secret Key를 Railway `papersignal-table-benchmark → Variables → SUPABASE_SERVICE_ROLE_KEY`에 직접 입력. 키는 대화로 보내지 않음. 현재 도구는 새 Secret Key 값을 조회할 수 없음.
- 이후 전용 서비스 재배포, 12편 SHA 사전 검증 재실행, 1편 Gemini E2E 스모크, 12편 v6.4.2 전체 기준선 순서. Q0/Q1/Q2/P0 모두 BLOCKED.
- 운영 API/Worker, 운영 Supabase 사용자/논문/분석 데이터 변경 없음.
- 검증 근거: `docs/BASELINE_SUPABASE_STAGE3_2026-11-17.md`.

## 2026-11-17 — Stage 2 complete: 12/12 locked PDF preflight, production writes prohibited

- Railway experiment runner `experiment/v642-full-pipeline-baseline-runner-2026-11-17`, code SHA `fc8d95ee95691750bdbe8db4708eaa79391327f3` (not production API/Worker).
- Exact locked B01–B10 Supabase originals **10/10** verified by SHA-256, byte length and PDF page count. H01 and H02 source PDFs were retrieved from publisher with authentication redirects and their binaries matched the existing locked user-uploaded SHA-256 exactly; uploaded to RAM-only authenticated runner endpoints, HTTP 200 for each.
- The full `POST /benchmark/prepare` returned HTTP 200 / `all_hashes_and_page_counts_verified=true` / **12/12 verified (279 pages)**, `provider_calls=0`. `/benchmark/diagnostics` reports `status=prepared` and all 12 paper IDs `verified`.
- Confirmed `POST /benchmark/run` returns **HTTP 403 `Dedicated non-production Supabase required`**. Production Supabase Auth/Storage/rows were NOT mutated; no Gemini analysis executed.
- Runtime Python 3.12.16 / PyMuPDF 1.26.3. Full report: `docs/BASELINE_PREFLIGHT_STAGE2_2026-11-17.md`.
- Runner is a separate Railway service in the production Railway environment, **not a non-production Supabase DB**. H01/H02 in-memory bytes and prepared state are lost on runner restart.
- **Next separate stage:** create an isolated Supabase database, configure dedicated credentials and E2E QA schema, repeat 12/12 preflight, then run the real Gemini baseline. All Q0/Q1/Q2/P0 remain BLOCKED and production API/Worker unchanged.

## 2026-11-17 — Q0 Stage 1 complete: B01-B10 preflight verified; H01 binary transfer pending

- Isolated baseline runner: `experiment/v642-full-pipeline-baseline-runner-2026-11-17`, code SHA `fc8d95ee95691750bdbe8db4708eaa79391327f3`. The original frozen v6.4.2 analysis engine and production API/Worker are untouched.
- Real Railway read-only Storage preflight downloaded each B01–B10 original: **10/10 verified** against locked SHA-256, byte size and PDF pages. H01 publisher endpoint returned a non-PDF; H02 not attempted. No model calls.
- Added authenticated exact-binary H01/H02 in-memory upload endpoints and a strict non-production DB write guard. Local tests **4 passed**; Railway Docker tests **106 passed, 1 skipped**. The runner uses a recycled test service in the production Railway environment, but writes to production Supabase are blocked by code.
- No Gemini full baseline, no cost or RSS, no production DB writes. Q0/Q1/Q2/P0 remain BLOCKED. Full details: `docs/BASELINE_PREFLIGHT_STAGE1_2026-11-17.md`.


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
