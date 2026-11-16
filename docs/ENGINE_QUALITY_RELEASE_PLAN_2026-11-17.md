# PaperSignal — 운영 엔진 성능 임계값 / 종료 및 최종 배포 게이트
최종 제품 의사결정: 2026-11-17, 사용자 요청에 따른 개발 계획.
**이 문서는 '기준'이며, 기준을 충족했다는 인증서가 아닙니다. 지금은 모든 신규 인간 골드·전체 비용·배포 테스트가 미완료입니다.**

## 최적화 목적과 대상
대상은 현재 운영 Git SHA `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`의 `finance-structured-v6.4.2` PyMuPDF 기반 전체 분석 파이프라인(추출 → Gemini → 방법론·Findings 검증/보정 → 인용 검증 → 저장/재시도)입니다.
**우선순위는 독립적 사실 정확도 > 인용 및 출처 신뢰성 > 기존 기능 보존 > 실패율 > 전체 지연·비용·메모리**입니다.
개별 정규식이나 출력 건수 개선 때문에 전체 품질/운영 비용이 나빠지는 변경은 탈락합니다. 오픈소스 대체 탐색은 종료되었습니다.

## Gate Q0 — 동일 조건의 고정 기준 준비 (모든 실험의 선행 요건)
- 원래의 v6.4.2 운영 SHA, AI 모델명, 프롬프트/구조화 스키마/추출 파라미터, 코퍼스 SHA·페이지 수를 기록하고 베이스라인을 독립 저장합니다. 과거 v6.3.9 모델 출력의 숫자를 v6.4.2 신규 출력으로 잘못 표기하지 않습니다.
- 원본 B01–B10(10편, 209페이지)을 regression, **별도 신규 논문 최소 2편을 사전 잠금된 held-out**으로 사용합니다. 튜닝 후 held-out을 선택하거나 교체하지 않습니다.
- H01/H02 exact PDF bytes are locked at commit `149311ec2993cac3bd410c10ac7feb202d582fc7`. B01-B10 exact attached PDF SHA-256 values are now locked in `benchmark/legacy_regression_binary_lock_2026-11-17.json`: first manifest commit `342a2ed30b6e270c9a8f167d2a6cbc8dedeaf80c`, follow-up lock-reference commit `14ed46fd032b42813dd0ccf372447bd71bd363aa`. The candidate branch starts from that follow-up commit. The PDFs match Supabase metadata by name/size/page count, but byte identity against private Storage is not claimed. Binary corpus lock is complete; Q0 remains BLOCKED until the pinned v6.4.2 full-pipeline baseline is run.
- H01/H02 and B01-B10 PDF SHA-256 and page counts are committed and locked before candidate code. The new candidate branch is based on the lock-reference commit. Q0 remains BLOCKED because the frozen v6.4.2 end-to-end baseline (pinned PyMuPDF 1.26.3, Gemini model path, upload-to-save latency, cost and peak RSS) has not yet been executed.
- 18건의 역사적 review-required finding은 **원본 페이지·숫자 셀·변수 및 모델 열·표 주석·표준오차/표준편차 구분**을 두 명의 실제 독립 검토자에게 각각 확인받아 일치/불일치를 기록합니다. 심사 이름을 AI가 꾸며내는 것은 금지합니다.
- '스크린 통과'와 골드 정확도를 분리합니다. 기존 346/346 인용 및 54/54 현재 검증기 통과는 이전 분석에 대한 **호환성 기준**이지 독립 사실 정확도가 아닙니다.
- provider 503/429가 있으면 '알 수 없음/측정 불가'로 표시하고 비용·속도·정확도 개선을 임의로 계산하지 않습니다.

## Gate Q1 — **출처 사실성·정확도**: 반드시 충족
1. **치명적 오류 0건**: 독립 검토한 채택된 Findings 중 존재하지 않는 수치, 부호 반전, 틀린 변수/모델 열, fabricated p-value/별표, 잘못된 논문/페이지 인용, 허위 인과 주장을 하나라도 새로 승인하면 실패입니다. 검증되지 않으면 'review_required/incomplete'로 보류합니다.
2. 독립 검토된 **최소 50건의 실제 물질적 수치·모형·인용 주장**에서 source-supported precision **≥98%**, 그리고 no critical error. 표본 50건에서 49/50 이상이어야 하지만 치명적 오류는 별도 0건 규칙입니다. 심사 표본 50 미만이면 Q1 '미측정'입니다.
3. 기존 18개 review-required를 **모두 독립 판정 완료**하고 미해결 치명적 사례 0건. 적어도 **4건을 출처 증거로 바로잡거나 확실히 지원 가능한 사실로 복구**해야 '의미 있는 개선'으로 인정합니다. 단순 분류 변경/같은 숫자 재서술/일치하지 않는 AI 주장은 복구로 세지 않습니다.
4. 해당 개선과 별개로 **독립 골드에서 답변 가능한 주장 회수율(recall)이 고정 baseline 대비 5.0퍼센트포인트 이상 상승**하는 경우에도 의미 있는 개선을 충족할 수 있습니다. 3 또는 4 중 적어도 하나가 달성되고 나머지 검증된 정확도가 유지되어야 합니다.
5. 기존 인간이 승인한 원문 근거·사실은 **단 한 건도 사라지면 안 됩니다**. 레거시 회귀에서는 prior 346개 exact page-quote pair 및 현 버전 screen-passed 54개를 원본대로 재검증하되, 인간이 거짓이라고 판정한 기존 주장은 철회하고 근거·사유를 기록합니다. 원시 건수만 높이려고 거짓 주장을 유지하지 않습니다.
6. held-out 원본 최소 2편에서 치명적 거짓 승인 0, source-supported precision ≥98% (50건 표본에 포함 시 출처 분리 기록), 모든 페이지 인용 검증. 근거가 부족하면 표시하지 않는 절제(abstention)는 임의 생성보다 우선합니다.

## Gate Q2 — **전체 서비스 비퇴행**: 반드시 충족
- 동일 파일·모델·반복 횟수·자원 조건으로 PyMuPDF 추출 포함 **업로드부터 결과 저장까지 전체 파이프라인**을 before/after 비교합니다. 모델 변동의 영향을 보기 위해 각 전략을 최소 **2회** 실행하고 모델 경로·재시도·토큰을 기록합니다.
- 전반 처리 시간 **p95 ≤ 고정 v6.4.2 기준 p95 × 1.05**, provider 토큰/실측 또는 단가 확인된 비용 **≤ 기준 × 1.05**, 최고 작업 프로세스 메모리 **≤ 기준 × 1.10**. 기준 자체가 미측정이거나 503으로 미완료이면 해당 항목 통과를 주장하지 않습니다.
- 작업 실패율·provider quota/429/503 처리·재시도 지속성·지원되는 인용/방법론/결과 항목은 **기준보다 악화되지 않음**. 전체 비용 측정에 실패하면 Q2 실패 또는 미측정입니다. 테스트에서 실패를 숨기지 않습니다.
- 백엔드 모든 회귀 테스트 + 새 실패 사례 단위 테스트 + 프런트엔드 build 통과. 모든 중복·큐·인증 보호 기능에 퇴행 없음.
- 개선 후보가 전체 품질을 낮추거나 비용·지연 한도를 넘으면 운영 반영하지 않고 되돌립니다.

## Gate P0 — **서비스 최종 배포 선행 조건**
- 실제 일회용 두 사용자 계정으로 로그인·Google 로그인·로그아웃·재로그인·PDF 업로드·분석·이력·원본 비공개 및 타 사용자 접근 차단(RLS)을 검증하고, 2계정 이상에서 결합 인용·데이터 누수 0.
- 운영 도메인에서 외부 수신자 이메일/SMTP 가입 확인, 앱 Preview·운영 빌드, Railway API/Worker health, 배포된 정확한 Git SHA/버전/마이그레이션·롤백 경로를 모두 확인합니다.
- 실사용 수준의 모델 API 사용량·비용·유료/무료 쿼터 상한과 429/503 재시도·보존·알림 정책을 검증합니다. Free Gemini에는 공개 논문 또는 합성 데이터만, 민감 자료 금지.
- 배포 후에도 기존 분석·원본 데이터 변경/삭제 불가; 백업/롤백 준비. 사용자 제공 키·토큰을 GitHub, 브라우저, 문서, 로그에 기록하지 않습니다.

## 성능 임계값 / 종료 규칙 — 무한 튜닝 금지
- **Q0 + Q1 + Q2 + P0 모두 통과하면 종료**합니다. 충분한 검증 상태에서는 사소한 추가 지표를 위해 새 휴리스틱·오픈소스 교체 시도 금지. '최대 성능'은 유한한 기준/예산에서의 품질 목표이지 이론상 전역 최대임을 주장하지 않습니다.
- 반복 단위: 문제의 원본 증거 확인 → 수정 1개 → 단위 테스트 → 전 영역 회귀/계측 → 개선 채택·폐기 → 버전/벤치마크 기록.
- **두 연속 후보에서 독립 확인 가능한 사실 품질 개선이 1퍼센트포인트 미만**이고 Q1/Q2를 충족했다면 추가 최적화 없이 출시 단계로 이동합니다. 반대로 새 critical error가 발견되면 즉시 그 후보를 철회하고 출처 정확도부터 해결합니다.
- P0가 미충족이면 **엔진 개선은 임계점에서 멈춰도 제품 배포는 금지**합니다. P0 검증 항목만 수정하고 엔진을 다시 건드리지 않습니다.
- 최종 배포는 이미 통과한 고정 커밋의 안전한 Preview/스테이징 검증 후에만 본 운영에 반영하며, 이후 헬스·사용자 분석 E2E·원본 접근 통제를 재검증합니다. 문제가 있으면 배포 SHA를 롤백합니다.

## 현재 게이트 판정 (이번 세션에 신규 측정 없음)
- Q0: **BLOCKED** (독립 사람 골드 및 현재 운영 v6.4.2 전체 비용/성능 기준 미완료)
- Q1: **BLOCKED** (18건 실제 독립 인간 검토 0건 기록, 실험 assistant visual drafts는 gold가 아님)
- Q2: **BLOCKED** (Gemini full-model A/B 503 실패; 전체 비용/지연 미계측)
- P0: **BLOCKED** (실사용 두계정 E2E·외부 SMTP·최종 릴리스 검증 미완료)
- 새 오픈소스 채택: **종료, 0건**. 최종 배포: **미실행**.

자세한 과거 파서 결과: `https://github.com/daegweon/financial-paper-analyzer/blob/experiment/ranked-pdf-parser-trial/docs/RANKED_PDF_PARSERS_2026-11-17.md`.


## 2026-11-17 — Candidate-only Gemini attempt telemetry (newest)

- On the fresh held-out-locked candidate branch, added a telemetry-only change in backend/app/main.py. Each analysis job ID is placed in a ContextVar and reset in finally; each _generate_gemini call gets a provider_call_id.
- Logs now associate model attempts with job ID/call ID, attempt number, model, HTTP status or transport outcome, per-request elapsed_ms, finish reason, prompt/candidate/thought/total tokens, provider_attempts and total_elapsed_ms. The 1-second inter-model delay is excluded from per-attempt elapsed but included in total elapsed.
- No prompt text, PDF text or API key is logged. Analysis version remains finance-structured-v6.4.2. Prompt/schema/extract_pages SHA-256 are byte-for-byte unchanged from frozen production. Request body, model order, timeout and retry policy unchanged.
- Added two mocked Gemini tests (503 -> fallback success; 503 + 429 -> failure) and an integration assertion that job context is set/reset.
- Candidate main.py SHA-256 0886879ed41dec90450894cc14963ac7b3fd6daa7a44a631daae57ef48dbd8ed; blob SHA-1 6a6c5dc9907a7180c8a3f1cfc8515eceaa814624. Prompt SHA df0e36c9bb0ffc2e920e7d978fc4458118e7ce1ff3a4d78fe774bac49417cdcd, schema SHA 9bbfdc0cabbb27327da91232115cc1b6be55c7ed94b32cb6e65ccc1c3892ad5d, extraction function SHA b116e1b38633ee11c47f51f424f1138edae058e276fc4288f83bd63273b7a291 — unchanged.
- GitHub Actions still startup_failure before any job; tests have not run and telemetry overhead is unmeasured. Do not claim the change is accepted or non-regressing.
- Draft PR #5 now includes the telemetry patch. No production deployment or database change.



## 2026-11-17 corpus lock and extraction preflight update

The B01-B10 exact attachment bytes are SHA-256 locked (10 PDFs, 209 pages, 17,760,530 bytes). See `benchmark/legacy_regression_binary_lock_2026-11-17.json`; the first manifest commit is 342a2ed30b6e270c9a8f167d2a6cbc8dedeaf80c and the lock-reference commit is 14ed46fd032b42813dd0ccf372447bd71bd363aa. The new candidate branch descends from this commit and the earlier H01/H02 lock commit. Supabase private Storage metadata matches names/sizes/page counts, but binary identity to those private objects is not asserted.

Local exact production extraction-function reproduction on B01-B10 with PyMuPDF 1.26.7: 209/209 pages yielded text, 0 empty pages, 691,985 extracted characters. Five-run per-paper median timings are recorded in the baseline JSON. Production pins 1.26.3, so this is extraction-only preflight, not Q2 evidence. Q0 remains blocked until the frozen v6.4.2 full-pipeline baseline is executed.
# PaperSignal — 운영 엔진 성능 임계값 / 종료 및 최종 배포 게이트
최종 제품 의사결정: 2026-11-17, 사용자 요청에 따른 개발 계획.
**이 문서는 '기준'이며, 기준을 충족했다는 인증서가 아닙니다. 지금은 모든 신규 인간 골드·전체 비용·배포 테스트가 미완료입니다.**

## 최적화 목적과 대상
대상은 현재 운영 Git SHA `8cd5e37ee8eab3bf4b726b75af89e410ab48396e`의 `finance-structured-v6.4.2` PyMuPDF 기반 전체 분석 파이프라인(추출 → Gemini → 방법론·Findings 검증/보정 → 인용 검증 → 저장/재시도)입니다.
**우선순위는 독립적 사실 정확도 > 인용 및 출처 신뢰성 > 기존 기능 보존 > 실패율 > 전체 지연·비용·메모리**입니다.
개별 정규식이나 출력 건수 개선 때문에 전체 품질/운영 비용이 나빠지는 변경은 탈락합니다. 오픈소스 대체 탐색은 종료되었습니다.

## Gate Q0 — 동일 조건의 고정 기준 준비 (모든 실험의 선행 요건)
- 원래의 v6.4.2 운영 SHA, AI 모델명, 프롬프트/구조화 스키마/추출 파라미터, 코퍼스 SHA·페이지 수를 기록하고 베이스라인을 독립 저장합니다. 과거 v6.3.9 모델 출력의 숫자를 v6.4.2 신규 출력으로 잘못 표기하지 않습니다.
- 원본 B01–B10(10편, 209페이지)을 regression, **별도 신규 논문 최소 2편을 사전 잠금된 held-out**으로 사용합니다. 튜닝 후 held-out을 선택하거나 교체하지 않습니다.
- H01/H02 exact PDF bytes are locked at commit `149311ec2993cac3bd410c10ac7feb202d582fc7`. B01-B10 exact attached PDF SHA-256 values are now locked in `benchmark/legacy_regression_binary_lock_2026-11-17.json`: first manifest commit `342a2ed30b6e270c9a8f167d2a6cbc8dedeaf80c`, follow-up lock-reference commit `14ed46fd032b42813dd0ccf372447bd71bd363aa`. The candidate branch starts from that follow-up commit. The PDFs match Supabase metadata by name/size/page count, but byte identity against private Storage is not claimed. Binary corpus lock is complete; Q0 remains BLOCKED until the pinned v6.4.2 full-pipeline baseline is run.
- H01/H02 and B01-B10 PDF SHA-256 and page counts are committed and locked before candidate code. The new candidate branch is based on the lock-reference commit. Q0 remains BLOCKED because the frozen v6.4.2 end-to-end baseline (pinned PyMuPDF 1.26.3, Gemini model path, upload-to-save latency, cost and peak RSS) has not yet been executed.
- 18건의 역사적 review-required finding은 **원본 페이지·숫자 셀·변수 및 모델 열·표 주석·표준오차/표준편차 구분**을 두 명의 실제 독립 검토자에게 각각 확인받아 일치/불일치를 기록합니다. 심사 이름을 AI가 꾸며내는 것은 금지합니다.
- '스크린 통과'와 골드 정확도를 분리합니다. 기존 346/346 인용 및 54/54 현재 검증기 통과는 이전 분석에 대한 **호환성 기준**이지 독립 사실 정확도가 아닙니다.
- provider 503/429가 있으면 '알 수 없음/측정 불가'로 표시하고 비용·속도·정확도 개선을 임의로 계산하지 않습니다.

## Gate Q1 — **출처 사실성·정확도**: 반드시 충족
1. **치명적 오류 0건**: 독립 검토한 채택된 Findings 중 존재하지 않는 수치, 부호 반전, 틀린 변수/모델 열, fabricated p-value/별표, 잘못된 논문/페이지 인용, 허위 인과 주장을 하나라도 새로 승인하면 실패입니다. 검증되지 않으면 'review_required/incomplete'로 보류합니다.
2. 독립 검토된 **최소 50건의 실제 물질적 수치·모형·인용 주장**에서 source-supported precision **≥98%**, 그리고 no critical error. 표본 50건에서 49/50 이상이어야 하지만 치명적 오류는 별도 0건 규칙입니다. 심사 표본 50 미만이면 Q1 '미측정'입니다.
3. 기존 18개 review-required를 **모두 독립 판정 완료**하고 미해결 치명적 사례 0건. 적어도 **4건을 출처 증거로 바로잡거나 확실히 지원 가능한 사실로 복구**해야 '의미 있는 개선'으로 인정합니다. 단순 분류 변경/같은 숫자 재서술/일치하지 않는 AI 주장은 복구로 세지 않습니다.
4. 해당 개선과 별개로 **독립 골드에서 답변 가능한 주장 회수율(recall)이 고정 baseline 대비 5.0퍼센트포인트 이상 상승**하는 경우에도 의미 있는 개선을 충족할 수 있습니다. 3 또는 4 중 적어도 하나가 달성되고 나머지 검증된 정확도가 유지되어야 합니다.
5. 기존 인간이 승인한 원문 근거·사실은 **단 한 건도 사라지면 안 됩니다**. 레거시 회귀에서는 prior 346개 exact page-quote pair 및 현 버전 screen-passed 54개를 원본대로 재검증하되, 인간이 거짓이라고 판정한 기존 주장은 철회하고 근거·사유를 기록합니다. 원시 건수만 높이려고 거짓 주장을 유지하지 않습니다.
6. held-out 원본 최소 2편에서 치명적 거짓 승인 0, source-supported precision ≥98% (50건 표본에 포함 시 출처 분리 기록), 모든 페이지 인용 검증. 근거가 부족하면 표시하지 않는 절제(abstention)는 임의 생성보다 우선합니다.

## Gate Q2 — **전체 서비스 비퇴행**: 반드시 충족
- 동일 파일·모델·반복 횟수·자원 조건으로 PyMuPDF 추출 포함 **업로드부터 결과 저장까지 전체 파이프라인**을 before/after 비교합니다. 모델 변동의 영향을 보기 위해 각 전략을 최소 **2회** 실행하고 모델 경로·재시도·토큰을 기록합니다.
- 전반 처리 시간 **p95 ≤ 고정 v6.4.2 기준 p95 × 1.05**, provider 토큰/실측 또는 단가 확인된 비용 **≤ 기준 × 1.05**, 최고 작업 프로세스 메모리 **≤ 기준 × 1.10**. 기준 자체가 미측정이거나 503으로 미완료이면 해당 항목 통과를 주장하지 않습니다.
- 작업 실패율·provider quota/429/503 처리·재시도 지속성·지원되는 인용/방법론/결과 항목은 **기준보다 악화되지 않음**. 전체 비용 측정에 실패하면 Q2 실패 또는 미측정입니다. 테스트에서 실패를 숨기지 않습니다.
- 백엔드 모든 회귀 테스트 + 새 실패 사례 단위 테스트 + 프런트엔드 build 통과. 모든 중복·큐·인증 보호 기능에 퇴행 없음.
- 개선 후보가 전체 품질을 낮추거나 비용·지연 한도를 넘으면 운영 반영하지 않고 되돌립니다.

## Gate P0 — **서비스 최종 배포 선행 조건**
- 실제 일회용 두 사용자 계정으로 로그인·Google 로그인·로그아웃·재로그인·PDF 업로드·분석·이력·원본 비공개 및 타 사용자 접근 차단(RLS)을 검증하고, 2계정 이상에서 결합 인용·데이터 누수 0.
- 운영 도메인에서 외부 수신자 이메일/SMTP 가입 확인, 앱 Preview·운영 빌드, Railway API/Worker health, 배포된 정확한 Git SHA/버전/마이그레이션·롤백 경로를 모두 확인합니다.
- 실사용 수준의 모델 API 사용량·비용·유료/무료 쿼터 상한과 429/503 재시도·보존·알림 정책을 검증합니다. Free Gemini에는 공개 논문 또는 합성 데이터만, 민감 자료 금지.
- 배포 후에도 기존 분석·원본 데이터 변경/삭제 불가; 백업/롤백 준비. 사용자 제공 키·토큰을 GitHub, 브라우저, 문서, 로그에 기록하지 않습니다.

## 성능 임계값 / 종료 규칙 — 무한 튜닝 금지
- **Q0 + Q1 + Q2 + P0 모두 통과하면 종료**합니다. 충분한 검증 상태에서는 사소한 추가 지표를 위해 새 휴리스틱·오픈소스 교체 시도 금지. '최대 성능'은 유한한 기준/예산에서의 품질 목표이지 이론상 전역 최대임을 주장하지 않습니다.
- 반복 단위: 문제의 원본 증거 확인 → 수정 1개 → 단위 테스트 → 전 영역 회귀/계측 → 개선 채택·폐기 → 버전/벤치마크 기록.
- **두 연속 후보에서 독립 확인 가능한 사실 품질 개선이 1퍼센트포인트 미만**이고 Q1/Q2를 충족했다면 추가 최적화 없이 출시 단계로 이동합니다. 반대로 새 critical error가 발견되면 즉시 그 후보를 철회하고 출처 정확도부터 해결합니다.
- P0가 미충족이면 **엔진 개선은 임계점에서 멈춰도 제품 배포는 금지**합니다. P0 검증 항목만 수정하고 엔진을 다시 건드리지 않습니다.
- 최종 배포는 이미 통과한 고정 커밋의 안전한 Preview/스테이징 검증 후에만 본 운영에 반영하며, 이후 헬스·사용자 분석 E2E·원본 접근 통제를 재검증합니다. 문제가 있으면 배포 SHA를 롤백합니다.

## 현재 게이트 판정 (2026-11-17 pinned-runtime verification)
- Q0: **BLOCKED**. B01-B10 + H01/H02 바이너리 잠금 완료, 운영 소스 지문과 PyMuPDF 1.26.3 런타임 확인, 로컬 백엔드 테스트 통과. 다만 B01-B10 중 v6.4.2 과거 실행은 B10 한 편뿐이며 H01/H02 Gemini 분석은 0건. 10편 전체의 동일 버전 전체 파이프라인 기준선은 아직 없음.
- Q1: **BLOCKED**. 18건의 review-required finding과 최소 50건의 물질적 주장을 두 명의 독립 검토자가 실제 원문으로 판정해야 함.
- Q2: **BLOCKED**. B07 단일 PDF의 추출+프롬프트 A/B만 완료. Gemini 포함 전체 파이프라인 p95, 실제 비용, 최고 RSS, 재시도 및 실패율 A/B는 미측정.
- P0: **BLOCKED**. 실사용 두 계정 E2E·외부 SMTP·최종 릴리스 및 롤백 검증 미완료.
- 백엔드 테스트: 운영 코드 102 passed / 1 skipped, 후보 코드 123 passed / 1 skipped. GitHub Actions runner는 `startup_failure`로 job 생성 전 종료; 로컬 테스트 통과와 구분함.
- 새 오픈소스 채택: **종료, 0건**. 최종 배포: **미실행**.

자세한 과거 파서 결과: `https://github.com/daegweon/financial-paper-analyzer/blob/experiment/ranked-pdf-parser-trial/docs/RANKED_PDF_PARSERS_2026-11-17.md`.


## 2026-11-17 — Candidate-only Gemini attempt telemetry (newest)

- On the fresh held-out-locked candidate branch, added a telemetry-only change in backend/app/main.py. Each analysis job ID is placed in a ContextVar and reset in finally; each _generate_gemini call gets a provider_call_id.
- Logs now associate model attempts with job ID/call ID, attempt number, model, HTTP status or transport outcome, per-request elapsed_ms, finish reason, prompt/candidate/thought/total tokens, provider_attempts and total_elapsed_ms. The 1-second inter-model delay is excluded from per-attempt elapsed but included in total elapsed.
- No prompt text, PDF text or API key is logged. Analysis version remains finance-structured-v6.4.2. Prompt/schema/extract_pages SHA-256 are byte-for-byte unchanged from frozen production. Request body, model order, timeout and retry policy unchanged.
- Added two mocked Gemini tests (503 -> fallback success; 503 + 429 -> failure) and an integration assertion that job context is set/reset.
- Candidate main.py SHA-256 0886879ed41dec90450894cc14963ac7b3fd6daa7a44a631daae57ef48dbd8ed; blob SHA-1 6a6c5dc9907a7180c8a3f1cfc8515eceaa814624. Prompt SHA df0e36c9bb0ffc2e920e7d978fc4458118e7ce1ff3a4d78fe774bac49417cdcd, schema SHA 9bbfdc0cabbb27327da91232115cc1b6be55c7ed94b32cb6e65ccc1c3892ad5d, extraction function SHA b116e1b38633ee11c47f51f424f1138edae058e276fc4288f83bd63273b7a291 — unchanged.
- GitHub Actions still startup_failure before any job; tests have not run and telemetry overhead is unmeasured. Do not claim the change is accepted or non-regressing.
- Draft PR #5 now includes the telemetry patch. No production deployment or database change.



## 2026-11-17 corpus lock and extraction preflight update

The B01-B10 exact attachment bytes are SHA-256 locked (10 PDFs, 209 pages, 17,760,530 bytes). See `benchmark/legacy_regression_binary_lock_2026-11-17.json`; the first manifest commit is 342a2ed30b6e270c9a8f167d2a6cbc8dedeaf80c and the lock-reference commit is 14ed46fd032b42813dd0ccf372447bd71bd363aa. The new candidate branch descends from this commit and the earlier H01/H02 lock commit. Supabase private Storage metadata matches names/sizes/page counts, but binary identity to those private objects is not asserted.

Local exact production extraction-function reproduction on B01-B10 with PyMuPDF 1.26.7: 209/209 pages yielded text, 0 empty pages, 691,985 extracted characters. Five-run per-paper median timings are recorded in the baseline JSON. Production pins 1.26.3, so this is extraction-only preflight, not Q2 evidence. Q0 remains blocked until the frozen v6.4.2 full-pipeline baseline is executed.


## 2026-11-17 — source fingerprint and pinned-runtime verification

See `benchmark/source_fingerprint_v6.4.2_2026-11-17.json` for the full frozen/candidate comparison. The candidate keeps the analysis version, prompt, schema, extraction, model config, dependencies and Dockerfile identical; only the Gemini transport/logging fingerprint changes. Both test suites pass locally on Python 3.12.16 / PyMuPDF 1.26.3 (production 102/1 skipped; candidate 123/1 skipped). B07 paired extraction+prompt A/B is p50 67.226 ms vs 68.100 ms (1.013 ratio) with identical extracted text and prompt hashes. This does not establish full-pipeline Q2. Only B10 has historical v6.4.2 production results; B01-B09 are mixed earlier versions. Q0/Q1/Q2/P0 remain blocked.
