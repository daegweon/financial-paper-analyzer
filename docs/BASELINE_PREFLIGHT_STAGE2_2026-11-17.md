# PaperSignal — Q0 단계별 실행 기록 (2단계, 2026-11-17)

## 이번 단계 목표

H01/H02 원본 PDF를 안전하게 벤치마크 실행기에 전달하고, 잠금된 B01–B10 + H01/H02 12편 전체의 동일 바이너리를 **Gemini를 호출하기 전에** 검증한다.

## 실제 실행 결과

- 격리 기준선 실행기: Railway `papersignal-table-benchmark` (재활용 실험 서비스).
- 실험 브랜치: `experiment/v642-full-pipeline-baseline-runner-2026-11-17`.
- 안전장치와 전송 경로 코드: `fc8d95ee95691750bdbe8db4708eaa79391327f3`.
- 실행 환경: Python **3.12.16**, PyMuPDF **1.26.3** (운영 의존성 고정 버전과 일치).
- Gemini 구성: `finance-structured-v6.4.2`, `gemini-3.5-flash-lite`; **Gemini 호출은 0회**.
- 원본 B01–B10: **10/10 검증 통과, 209페이지**. Supabase 비공개 `papers` 버킷에서 읽기 전용 다운로드 후 SHA-256, 파일 크기, 페이지 수를 확인.
- H01: 정확히 잠근 `816e404d2f1dee7df84d52bf4238a75d7d777878cf100b42e3f220cc1da9b127`, **40페이지**, **2,521,298 bytes**.
- H02: 정확히 잠근 `d385806b9a448e399dfc9f6017710561bf15bfd50ec514536303978ad07eb283`, **30페이지**, **5,223,546 bytes**.
- H01/H02: 출판사 인증 리디렉션 처리 후 받은 공개 PDF의 실제 바이트가 기존 사용자 첨부 원본의 고정 SHA-256과 완전히 동일함을 독립 확인. 해당 파일을 전용 `/benchmark/heldout/H01` 및 `/benchmark/heldout/H02`에 인증된 요청으로 전달. 각각 HTTP 200, `verified_in_memory`; Supabase Storage 쓰기 없음.
- `POST /benchmark/prepare`: HTTP 200, `record_type=PREFLIGHT_ONLY_NO_GEMINI_CALLS`, `all_hashes_and_page_counts_verified=true`, 전체 **12/12** 검증 통과.
- 결과 페이지 수 (B01→B10, H01, H02): **[31,20,14,19,24,22,23,21,16,19,40,30]**, **총 279페이지**.
- `GET /benchmark/diagnostics`: `status=prepared`, B01~B10/H01/H02 모두 `status=verified`, `error=null`.
- `POST /benchmark/run`: 예상대로 **HTTP 403** 및 `Dedicated non-production Supabase required`. 운영 Supabase 쓰기 차단이 실제 작동함을 확인.
- 운영 사용자 계정 / PDF / Job / 분석 결과 데이터베이스에 **쓰기 없음**.
- 고정 런타임 신규 가드 테스트는 **4 passed**, Railway Docker 테스트는 **106 passed, 1 skipped** (앞선 1단계에서 수행).

## 주의사항

- Held-out PDF 바이트는 실행기 메모리에만 존재하므로 **컨테이너 재시작이나 재배포 시 다시 입력해야 한다**. 실행 도중 정지하면 prepared 상태도 소실될 수 있다.
- 실험 서비스는 운영 Railway **환경 안**에서 분리된 서비스일 뿐, 독립 Supabase 프로젝트와 격리된 데이터베이스가 아니다. 따라서 `/benchmark/run`은 프로덕션 DB 쓰기를 강제로 거부한다.
- Q0 완전 통과 의미 아님. 실제 전체 Gemini 기반 v6.4.2 Baseline, 전체 지연·비용·메모리·정확도 평가를 수행하지 않았다.
- 테스트용 백엔드 최종 배포로 해석하거나, 운영 Worker·API가 변경됐다고 보고하면 안 된다.
- Q0/Q1/Q2/P0 모두 여전히 **BLOCKED**.

## 다음 독립 단계

1. 사용자 데이터와 격리된 Supabase **별도 비운영 프로젝트/브랜치** 준비. 벤치마크에 맞는 Auth, Storage, 테이블, RPC, 접근제어를 생성하고 기존 서비스의 비밀 키를 전용 프로젝트로 복사하지 않는다.
2. 벤치마크 서비스에 전용 프로젝트 설정 후, 잠금 원본 PDF 전송 및 12/12 검증을 다시 수행한다.
3. 12편의 v6.4.2 기준선 분석을 실제 Gemini 호출로 실행하고 상태, 토큰, 오류, p95, 최고 RSS를 기록한다. 비용은 출처가 확인된 당시 실제 과금 기준/계약 정보가 없으면 `null` 유지.
4. 후보 PR #7도 **동일 조건**으로 반복 평가해 비퇴행 기준을 점검한다. Q1 독립 인간 검토 및 P0 출시 검증은 별도 게이트로 유지.
