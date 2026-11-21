# PaperSignal — 공개 금융논문 검색 및 PDF URL 가져오기

> **작성:** 2026-11-21 KST  
> **구현 PR:** [#36](https://github.com/daegweon/financial-paper-analyzer/pull/36)  
> **검증된 코드:** `551f6b47aaa7b65f3e5c225cee14759868eee1fe`  
> **CI:** [Checks #44884328059](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44884328059) — 백엔드 244통과/1제외, 프런트엔드 단위 82통과, Playwright 7통과, 일회용 PostgreSQL 계약 통과  
> **운영 반영 여부:** 문서 스냅샷 이후 바뀔 수 있으므로 GitHub `main` 커밋과 Vercel/Railway의 현재 Production 배포 SHA를 별도로 대조할 것.

## 목적

기존 PaperSignal은 PDF를 사용자가 장치에 다운로드한 뒤 `＋ 논문 추가`를 통해 업로드해야 했다. 본 기능으로 공개 금융·경제·증권 분야 논문을 서비스 내부에서 발견하고, 별도 수동 다운로드 없이 내 비공개 논문 라이브러리에 가져온 다음 기존 Gemini 분석을 사용할 수 있다.

추가한 경로는 두 가지다.

1. **공개 PDF URL 직접 가져오기**: PDF가 실제로 공개된 HTTPS 주소를 입력하고 **내 라이브러리에 가져오기**를 선택한다.
2. **공개 금융논문 검색 + 원클릭 가져오기**: OpenAlex 학술 API에 키워드로 검색하고, 공개 PDF 주소가 제공되는 결과에서 **PDF 가져오기**를 선택한다. 공개 PDF가 없는 항목은 원문 제공 사이트 링크만 표시한다.

기존 사용자 장치의 **파일 직접 업로드 기능은 그대로 유지**한다.

## 화면에서 사용하기

로그인 후 `나의 연구 라이브러리` 아래 `공개 금융 논문 찾아보기` 영역으로 이동한다.

### PDF 주소

1. `https://publisher.example/paper.pdf` 형식의 **직접 접근 가능한 공개 HTTPS PDF URL**을 입력한다.
2. `내 라이브러리에 가져오기`를 클릭한다.
3. 서버가 공개 다운로드 대상을 검증하고 PDF를 가져온다.
4. 브라우저가 기존 업로드 코드를 사용해 개인 비공개 Storage 경로에 저장하고 논문 메타데이터를 생성한다.
5. 논문이 라이브러리에서 열리면 기존 `분석 시작`으로 Gemini 분석을 요청한다.

로그인이 필요한 사이트, 유료 구독 전용 페이지, HTML 랜딩 페이지 URL은 PDF 파일로 취급하지 않고 명시적인 실패 메시지를 제공한다.

### 공개 논문 검색

1. `공개 학술 논문 검색 (OpenAlex)`에 `ETF arbitrage`, `asset pricing`, `portfolio risk` 등 검색어(2~200자)를 입력한다.
2. 제목, 연도, 최대 네 명의 저자, 원문 링크, 해당 위치에 기록된 라이선스 정보를 확인한다.
3. `PDF 가져오기` 버튼이 있는 결과는 한 번 클릭해 개인 라이브러리에 가져온다.
4. `공개 PDF 링크 없음` 항목은 `원문 ↗`로 제공자 페이지를 연다.
5. `이전`/`다음`으로 페이지를 이동한다(10개/페이지, 현재 보호 설정상 최대 10페이지).

**공개 열람(Open Access)은 재배포 허용을 의미하지 않는다.** OpenAlex 메타데이터에 기록된 라이선스가 누락되거나 불완전할 수 있다. 사용자는 해당 저작물의 이용 조건을 확인해야 한다. 서비스는 원문 파일을 공용 재배포하지 않고 개인용 비공개 버킷에 업로드한다.

## API 및 코드

| API | 인증 | 응답 | 역할 |
|---|---|---|---|
| `GET /api/public-papers/search?query=<text>&page=<1..10>` | 유효한 사용자 Bearer JWT | OpenAlex 메타데이터/페이지 상태(JSON) | 공개 학술논문 검색 |
| `POST /api/public-papers/download` / `{"url":"https://..." }` | 유효한 사용자 Bearer JWT | `application/pdf` 바이트, `Cache-Control: no-store` | 검증된 공개 PDF 가져오기 |

- 백엔드: [`backend/app/public_papers.py`](../backend/app/public_papers.py) (공개 검색, 안전한 다운로드), [`backend/app/main.py`](../backend/app/main.py) (Router 등록).
- 프런트엔드: [`frontend/app/page.tsx`](../frontend/app/page.tsx) (검색·가져오기 UX 및 기존 `upload(File)` 재사용), [`frontend/app/globals.css`](../frontend/app/globals.css) (반응형 UI).
- 단위/보안 테스트: [`backend/tests/test_public_papers.py`](../backend/tests/test_public_papers.py).
- 브라우저 회귀: [`frontend/tests/e2e/auth-and-workspace.spec.ts`](../frontend/tests/e2e/auth-and-workspace.spec.ts).

### OpenAlex

- API: `https://api.openalex.org/works`, `search=<query>`, `filter=is_oa:true`, `per_page=10`.
- PDF URL: 공개 위치의 `best_oa_location.pdf_url` 우선; 해당 공개 위치에 PDF가 없는 경우 `primary_location.pdf_url`을 검토한다.
- `OPENALEX_API_KEY`: **선택적 서버 전용 Railway API 환경 변수**. 2026년 11월 OpenAlex는 키 없이 기본·소량의 API 조회를 허용하나, 실제 운영 규모의 호출에는 **무료 API 키를 권장**한다. 키를 설정하면 외부 호출에서 `Authorization: Bearer <key>`로 사용하며 브라우저에는 전달하지 않는다.
- 검색량 또는 외부 제공자 한도로 429가 발생하면 사용자에게 재시도를 안내한다. 실제 제공자의 SLA·호출 한도는 변경될 수 있다.
- 공식 설명: https://help.openalex.org/api/authentication/ 및 https://help.openalex.org/data/locations/
- 현재 구현은 **OpenAlex만** 검색한다. 자체 추천 엔진, 자동 RSS 수집, 모든 출판사 PDF 추출, 비공개 논문 검색은 포함하지 않는다.

### PDF와 보안 경계

- 로그인하지 않은 검색/다운로드는 거부(HTTP 401).
- URL은 HTTPS만 허용하고 포트 443만 허용한다. 사용자정보 포함 주소, IP 직접 연결, 로컬/사설망·내부망 목적지는 차단한다.
- DNS 결과의 모든 주소를 검사하고 **실제 HTTP 연결을 검증된 공개 IP로 고정**한다. 원본 호스트명은 TLS SNI와 HTTP Host에만 사용하여 DNS rebinding과 내부망 SSRF 위험을 줄인다.
- 리디렉션은 자동으로 따라가지 않고 매번 새 목적지를 검증한다(최대 3회). 외부 출판사로 사용자 JWT 또는 서비스 전용 키를 전송하지 않는다.
- 응답의 Content-Length 및 스트리밍 바이트 수를 검사한다. 최대 **30MiB**, **1~300페이지**, `%PDF-` 시그니처와 PyMuPDF 문서 검증, 암호화 PDF 거부.
- 인증된 사용자의 브라우저가 반환된 바이트를 `File`로 구성해 기존 **개인 전용 Storage 업로드 + 사용자 소유권이 명시된 논문 INSERT** 경로를 그대로 사용한다. 외부 검색/다운로드 백엔드는 Storage에 서비스 역할로 쓰지 않는다.
- 검색 응답의 서지 메타데이터/라이선스 문자열은 검색 결과 표시용이고, 최종 분석은 업로드된 원문 PDF만 대상으로 한다.
- 원문 페이지 근거 인용과 Gemini 분석 엔진 v6.4.2는 변경하지 않았다.

## 검증과 사용 제한

검증 기준: [GitHub Actions #44884328059](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44884328059).

- 백엔드: 기존 회귀 포함 **244 passed, 1 skipped**.
- 프런트엔드: TypeScript/Next 빌드, 단위 테스트 **82 passed**.
- Playwright: **7 passed**, 신규 테스트는 검색 → PDF 가져오기 → 사용자 Bearer 인증 → 기존 비공개 업로드 및 논문 등록 → 보고서 열기 흐름을 모킹한 브라우저 E2E.
- 일회용 PostgreSQL: 기존 마이그레이션 및 권한 계약 테스트 통과.
- 공개 URL 목적지 검증, 사설 IP/혼합 DNS 차단, URL 정규화, PDF 서명·암호화·용량 검증, 인증 필수, 429 오류, 리디렉션과 크기 스트리밍 제한을 테스트했다.
- **외부 OpenAlex 실서비스 호출 및 실제 출판사별 PDF 서버와의 통합은 자동 CI에서 모킹**했다. 최종 운영 확인은 공개 논문 링크로 소규모 실사용 스모크를 수행한다.
- Google OAuth·기존 논문 분석 결과·사용자 데이터 격리 로직에는 변경 사항이 없다.

### 운영 스모크

1. 실제 Google 계정 로그인 후 기존 라이브러리와 로그아웃 정상 표시 확인.
2. `ETF arbitrage` 검색 결과·원문 링크·PDF 제공 여부 확인.
3. 재배포가 허용되는 공공/CC BY 공개 테스트 PDF 주소로 가져오기 실행.
4. 가져온 PDF가 **해당 사용자 라이브러리 안에서만** 보이는지, 원문 PDF가 열리는지 확인.
5. Gemini 분석, 원문 페이지 근거 이동, 보고서 UI 정상 확인.
6. OpenAlex 429나 공개 PDF HTTP 404/로그인 요구 시 사용자에게 설명된 오류가 표시되는지 확인.

## 향후 확장과 의도적으로 제외한 기능

- DOI 자체를 검색해 다운로드 가능한 위치로 해결하거나, arXiv 외의 여러 API를 통합하는 기능은 후속 확장.
- 검색 결과 자동 저장/추천/주기적 수집은 미구현.
- 외부에서 가져온 논문의 원본 URL, 라이선스, DOI를 구조화된 DB provenance 필드로 저장하는 기능은 미구현(현재는 파일 이름과 본문 분석 결과 중심).
- 스캔 전용 PDF OCR, 표·그림 자산 분리, 시뮬레이터는 이번 범위에서 제외.
- 무료 모델 서비스에는 비공개 회사 문서 또는 고객 정보 PDF를 업로드하지 않는다.
