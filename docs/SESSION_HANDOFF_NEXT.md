# PaperSignal — 새 세션 인계 및 최종 제품 방향
기록일: 2026-11-17 (Asia/Seoul)
**이 문서가 이전 세션의 구형 오픈소스 실험 계획보다 우선합니다.**

## 사용자 최종 결정 — 확정
1. PDF 파서/오픈소스 탐색 및 **전면 교체 연구는 종료**합니다. 더 이상 Docling, Camelot, PDFium, pdfplumber, GROBID, MinerU, Marker를 탐색하는 데 개발 시간을 쓰지 않습니다. 예외는 기존 엔진의 검증된 특정 오류를 해결하는 데 반드시 필요한 경우뿐이며, 무분별한 파서 교체는 금지합니다.
2. PaperSignal의 **현재 PyMuPDF 기반 분석 엔진을 개선**합니다. 현재 운영 API·Worker의 코드 및 품질 기준을 보존하며, 작은 수정 때문에 전체 성능이 떨어지면 즉시 되돌립니다.
3. **독립 검증된 품질 임계점**을 만족하면 과도한 미세 튜닝을 중단하고 마지막 제품 출시 요건을 마친 뒤 **최종 배포**합니다. '무한한 이론적 최고값'은 요구하지 않습니다.
4. 사용자는 다음 세션에서 추가적인 설계 확인 없이 목표에 맞게 자율적으로 개발 진행하기를 원합니다. 데이터 삭제, 비밀 키 노출, 위험한 설정 변경은 승인받지 않았습니다. 기존 분석 결과/개인별 접근 제어를 보존합니다.

## 지속성 — 반드시 이곳에서 시작
- 이 ChatGPT 프로젝트의 **모델 메모리는 비활성화**되어 있습니다. 이 결정을 ChatGPT의 계정 메모리에 넣었다고 주장하지 마세요.
- 전환 기준은 GitHub **`plan/engine-quality-release-handoff` 브랜치**에 있는 `docs/PROJECT_STATE.md`, `docs/PROJECT_DECISIONS.md`, `docs/ENGINE_QUALITY_RELEASE_PLAN_2026-11-17.md` 및 `benchmark/engine_release_gates_2026-11-17.json`입니다.
- 실험 내용을 참조하려면 `experiment/ranked-pdf-parser-trial`의 `docs/RANKED_PDF_PARSERS_2026-11-17.md` 및 `experiment/full-analysis-ab-runner`의 `benchmark/results/full-analysis-docling-ab-replay-2026-11-17.md`를 읽으세요.
- **운영 브랜치 `feat/research-workspace-mvp`는 Railway API·Worker가 Git 연동으로 자동 배포할 수 있으므로** 문서만 저장하려고 여기에 push하지 마세요. 새 개발은 안전한 분리 브랜치에서 하고 검증된 변경만 배포하세요.
- 신규 세션 초반 먼저 GitHub의 최신 위 파일을 읽고 Railway/Vercel/Supabase 현재 상태와 소스 버전을 직접 확인합니다. 문서에 적힌 숫자와 실시간 상태가 다르면 실시간 상태로 조정합니다.

## 현재 제품 및 배포 상태(마지막 확인)
- 저장소: `daegweon/financial-paper-analyzer`.
- 운영 소스 브랜치: `feat/research-workspace-mvp`, 커밋 `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`, 분석 엔진 소스 버전 `finance-structured-v6.4.2`.
- Railway 프로젝트 `c663389c-453c-4645-a83d-299b94089864`, 환경 `0b4f06c3-504a-4610-8995-395c2f4d3d1f`. API `81b678e2-7136-436d-9058-7d20647dc1b7`, Worker `238af942-0628-47d5-9280-04a49373423f` 모두 SUCCESS / 실행 중. 기존 API deployment `17c9134b-f49c-4358-a879-7ca77b55b936`, Worker `dc501061-d434-454a-bc7d-4658b991a2f1`.
- Supabase `hwmtayrecsfxernhssro` (Free/Seoul), Vercel Next.js 프런트엔드/Google+이메일 인증, 비공개 PDF Storage와 RLS, 지속형 작업 큐 및 복구, 도서관/비교/CSV/A4 보고서.
- 마지막 검증된 DB 수치(실시간이 아님): 논문 14, 분석 103, 완료 작업 102, 과거 실패 작업 28, 원본 비공개 PDF 14. 실험 JSON 보관함 객체 99개. 사용자 데이터/논문은 수정하지 않았습니다.
- 기존 문서의 'v6.3.9가 현재 운영' 주장은 **폐기**합니다. v6.3.9는 과거 분석 결과 버전이고 현재 배포 코드 기준은 v6.4.2입니다.
- 제품 개발 진행률 약 72%는 이전 엔지니어링 추정값이며 **신규 측정으로 갱신된 숫자가 아닙니다**.

## 왜 오픈소스 계획을 종료했는가
- 원본 B01–B10 10편, 209페이지에 대한 이전 **v6.3.9 저장 분석 결과를 v6.4.2 검증기에 재검증**한 기준: 기존 PyMuPDF 인용 346/346, 직접 출처 근거를 유지한 Findings 71, 현재 검증기 screen-passed 54.
- Docling Parse: 296/346, Findings 65, screen-passed 51. PDF 추출 속도와 메모리도 해당 단독 실험에서 악화.
- pypdfium2: 292/346, Findings 64, screen-passed 50. 추출 속도와 RSS는 조금 좋아졌지만 인용·Findings가 감소.
- pdfplumber: 14/346, Findings 2, screen-passed 1. 현재 strict 인용 형식과 호환성이 크게 떨어짐.
- Camelot 전면 추출은 동일 B01 18페이지 Table 2가 원문에 있음에도 놓쳤고 독립 출처 정확도를 입증하지 못했습니다.
- GROBID·MinerU는 현재 1GB 격리 환경에서 **미실행**, Marker는 설치/CLI 테스트 이후 B01 변환이 비관리자 쓰기 권한으로 실패해 **정확도 미측정**. 이 세 제품의 실제 정확도가 낮다고 주장하지 않습니다.
- 이러한 수치는 **과거 PyMuPDF가 만든 인용문을 다시 맞추는 호환성 실험**이지 독립 인간 골드 정확도/새 Gemini 모델 출력 정확도가 아닙니다. v6.4.2 신규 모델 A/B는 Gemini 기본·대체 모델 HTTP 503으로 실패하여 미완료. 이 제한을 차후 답변에서 반드시 표시합니다.
- **새 오픈소스 운영 도입 0건**, 최종 전면 교체 승인 0건. 기존 엔진 유지가 현 인프라에서의 검증된 최선의 결정이지만 세계 최고 PDF 엔진이라는 주장은 금지합니다.

## 다음 실제 작업 (우선순위)
1. `docs/ENGINE_QUALITY_RELEASE_PLAN_2026-11-17.md`에 선언한 품질·자원·출시 임계값을 계측 가능한 검증 하네스로 옮깁니다. 기존 `v6.4.2` 운영 소스 SHA를 '고정 기준'으로 유지하고, 작업 브랜치 `experiment/engine-quality-v6-4-x` 등을 따로 생성하세요.
2. 과거 검토 필요 18건(B01 4, B02 6, B03 1, B05 2, B09 3, B10 2)을 원본 PDF 페이지·행·열·계수 부호·유의성 근거와 실제 두 명의 독립 검토 결과로 판단할 수 있는 워크플로우를 구축하세요. **AI가 만든 시각 검수 초안은 사람의 정답이 아닙니다.**
3. PyMuPDF 기반 **원래 분석 엔진의 확인된 문제**—근거 누락, 잘못된 수치/모델 열 연결, 의미상 서로 다른 통계값 혼동, 중복, Gemini 503·429 복구·토큰/비용 계측—을 오류별로 고치고 전체 회귀 테스트를 수행합니다. B01/Table2와 B10/Table5는 파서 교체 실험에서 나온 교차참조 사례이며 운영에서 같은 오류가 발생했다고 단정하지 마세요.
4. 방법론 및 Findings의 페이지별 검증 정확도를 독립 골드로 측정하고 2개 이상의 별도 미튜닝 논문(held-out)을 사전 SHA 잠금해 테스트하세요. 10편의 기존 결과 인용 346개와 screen-passed 54개는 레거시 호환성 검사이며 정확도 증명이 아닙니다.
5. 모델/토큰/요청 시도/p95/메모리/예상 비용을 누락 없이 계측하세요. B01/B03 실제 Gemini 전체 분석 요청 HTTP 503의 원인이 해소되기 전에는 성능 개선을 선언하지 않습니다.
6. 모든 품질 게이트 통과 시 최종 출시 검증: 2계정 실제 PDF 업로드/분석, RLS/원본 비공개, Google 로그인, 외부 SMTP 확인, 프런트/백엔드 빌드, Railway 작업 복구, Vercel 릴리스 확인. 기존 데이터를 삭제하거나 시크릿을 노출하면 안 됩니다.
7. 위 조건을 충족하면 **추가 미세 튜닝을 중단**하고 테스트된 커밋만 제한적 배포 후 헬스·E2E·품질을 검증해 최종 배포합니다. 문제가 발생하면 즉시 롤백하고 이전 운영 SHA를 유지합니다.


## 2026-11-17 — Held-out preselection and exact PDF lock preparation (newest)

- Preselected two held-out candidates **before creating any new release-eligible candidate branch**:
  - H01: Monteiro, Sebastião & Silva, "Prediction and Allocation of Stocks, Bonds, and REITs in the US Market", DOI 10.1007/s10614-024-10589-2, publisher PDF reports 40 pages, CC BY 4.0; methods VAR/TVP-VAR, DMA/DMS, genetic algorithm and portfolio optimization.
  - H02: Chun, Kang & Kim, "Forecasting returns with machine learning and optimizing global portfolios: evidence from the Korean and U.S. stock markets", DOI 10.1186/s40854-024-00648-w, publisher PDF reports 30 pages, CC BY 4.0; methods LASSO/Ridge/Elastic Net, Random Forest, LightGBM, XGBoost, FX and portfolio optimization.
- Metadata and PDF links registered in benchmark/heldout_preregistration_2026-11-17.json and benchmark/HELDOUT_PREREGISTRATION_2026-11-17.md.
- **Not binary-locked:** this session could inspect publisher PDF pages but the execution runtime could not download raw PDF bytes. Both SHA-256 values intentionally remain null; Q0 remains BLOCKED. Never hash parsed text instead of exact PDF bytes.
- Added benchmark/lock_heldout_pdfs.py: PyMuPDF exact-byte verification, page count matching, SHA-256, duplicate and optional regression-overlap rejection. Added six synthetic tests. A local isolated reproduction verified hash, page count, overlap and mismatch fail-closed behavior; full repository CI still unavailable.
- **Do not create the next candidate branch yet.** Obtain exact H01/H02 PDF bytes, run the lock utility, commit the binary-verified manifest, add the actual Git lock commit SHA in a follow-up commit, then create a new candidate branch from frozen production SHA 8cd5e37ee8eab3bf4b726b75af89e410ab48396e.
- Current experiment experiment/engine-quality-v6-4-x remains ineligible for release because it was tuned before held-out pre-registration. PR #4 remains Draft and isolated. Production API/Worker unchanged.


- Local synthetic test reproduction for the exact-byte lock logic: **7/7 passed** after correcting one test's expected error-message substring. This is a local reproduction only; GitHub Actions/full backend CI still has not executed.
- Exact Springer PDF binary downloads were attempted but unavailable from this execution runtime (network/DNS restriction). Publisher-parsed PDF page counts and article metadata do not substitute for exact binary hashes.


## 2026-11-17 — User-uploaded held-out PDFs binary-locked; fresh baseline branch started (newest)

- User uploaded exact publisher PDFs H01/H02. PyMuPDF opened the original bytes and verified page counts, PDF metadata, DOI and CC BY 4.0 licence text:
  - H01, 40 pages, 2,521,298 bytes, SHA-256 816e404d2f1dee7df84d52bf4238a75d7d777878cf100b42e3f220cc1da9b127.
  - H02, 30 pages, 5,223,546 bytes, SHA-256 d385806b9a448e399dfc9f6017710561bf15bfd50ec514536303978ad07eb283.
- Immutable binary lock commit: 149311ec2993cac3bd410c10ac7feb202d582fc7; follow-up manifest reference commit: 59b68fbc902bd17b656d606246d17b19a5614acf.
- Created fresh candidate branch experiment/engine-quality-v6-4-2-heldout-locked directly from frozen production SHA 8cd5e37ee8eab3bf4b726b75af89e410ab48396e AFTER the lock commit. No code from the prior pre-registration experiment branch was copied into the engine.
- Draft PR #5: https://github.com/daegweon/financial-paper-analyzer/pull/5. Changed files are benchmark/release utilities, tests and docs only; backend/app/main.py and backend/app/worker.py are unchanged.
- Captured source SHA-256 for API/Worker/requirements/Dockerfile plus prompt, schema, extraction and sanitized model config in benchmark/baseline_lock_v6.4.2_2026-11-17.json on the candidate branch. Railway Worker logs corroborate Gemini primary gemini-3.5-flash-lite and fallback gemini-3.6-flash; no key values were read or recorded.
- Local extraction-only preflight of H01/H02 was performed with PyMuPDF 1.26.7. Production pins 1.26.3, so local timings (H01 median 249.978ms, H02 107.494ms) are explicitly NOT production Q2 evidence.
- Added repeatable benchmark/capture_engine_fingerprint.py and benchmark/extraction_preflight.py with tests. The extraction preflight refuses a PDF whose exact SHA/bytes/page count differ from the locked manifest and makes zero provider calls.
- GitHub Actions on PR #5 again ended startup_failure before creating any job (zero jobs); full repository tests have not run. Do not report test pass.
- Current Files inventory contains only H01/H02 PDFs; the original B01-B10 PDF bytes are not available here, so their SHA locks remain missing. Full Gemini baseline for H01/H02, independent human gold, full p95/cost/RSS and P0 E2E are also missing.

**Status:** Q0/Q1/Q2/P0 remain BLOCKED. Do not merge PR #5, change production branch/deployments, or tune the engine until original corpus locks and same-version full-pipeline baseline are complete. Existing Railway API/Worker remain on production SHA 8cd5e37.


## 2026-11-17 — Candidate-only Gemini attempt telemetry (newest)

- On the fresh held-out-locked candidate branch, added a telemetry-only change in backend/app/main.py. Each analysis job ID is placed in a ContextVar and reset in finally; each _generate_gemini call gets a provider_call_id.
- Logs now associate model attempts with job ID/call ID, attempt number, model, HTTP status or transport outcome, per-request elapsed_ms, finish reason, prompt/candidate/thought/total tokens, provider_attempts and total_elapsed_ms. The 1-second inter-model delay is excluded from per-attempt elapsed but included in total elapsed.
- No prompt text, PDF text or API key is logged. Analysis version remains finance-structured-v6.4.2. Prompt/schema/extract_pages SHA-256 are byte-for-byte unchanged from frozen production. Request body, model order, timeout and retry policy unchanged.
- Added two mocked Gemini tests (503 -> fallback success; 503 + 429 -> failure) and an integration assertion that job context is set/reset.
- Candidate main.py SHA-256 0886879ed41dec90450894cc14963ac7b3fd6daa7a44a631daae57ef48dbd8ed; blob SHA-1 6a6c5dc9907a7180c8a3f1cfc8515eceaa814624. Prompt SHA df0e36c9bb0ffc2e920e7d978fc4458118e7ce1ff3a4d78fe774bac49417cdcd, schema SHA 9bbfdc0cabbb27327da91232115cc1b6be55c7ed94b32cb6e65ccc1c3892ad5d, extraction function SHA b116e1b38633ee11c47f51f424f1138edae058e276fc4288f83bd63273b7a291 — unchanged.
- GitHub Actions still startup_failure before any job; tests have not run and telemetry overhead is unmeasured. Do not claim the change is accepted or non-regressing.
- Draft PR #5 now includes the telemetry patch. No production deployment or database change.


- GitHub commit metadata independently confirms lock chronology: lock commit 149311ec2993cac3bd410c10ac7feb202d582fc7 at 2026-11-16T21:11:16Z; first commit on the new candidate branch 356b4d688657fc2c55b828d2b12b3062e1c9434b at 2026-11-16T21:15:33Z. The immutable lock preceded the candidate branch's first commit by 4 minutes 17 seconds.

## 새 세션 시작 시 그대로 사용할 메시지
"PaperSignal 개발을 이어가자. GitHub `plan/engine-quality-release-handoff`의 `docs/SESSION_HANDOFF_NEXT.md`, `docs/ENGINE_QUALITY_RELEASE_PLAN_2026-11-17.md`, `docs/PROJECT_STATE.md`와 `benchmark/engine_release_gates_2026-11-17.json`을 먼저 읽어. 오픈소스 교체 검토는 종료, 기존 PyMuPDF/v6.4.2 엔진만 개선. 독립 골드·인용·전체 정확도·비용·실서비스 테스트 임계점 충족 전 배포 금지. 지금 상태 확인 후 다음 목표를 실제 구현하고 검증 결과를 GitHub에 기록해."
