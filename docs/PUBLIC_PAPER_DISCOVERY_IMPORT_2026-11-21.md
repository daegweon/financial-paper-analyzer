# PaperSignal — 공개 금융논문 검색 및 PDF URL 가져오기

> **작성:** 2026-11-21 KST  
> **기능 구현 PR:** [#36](https://github.com/daegweon/financial-paper-analyzer/pull/36) · [추천/정렬 개선 PR #37](https://github.com/daegweon/financial-paper-analyzer/pull/37)  
> **운영 반영 PR:** [#36](https://github.com/daegweon/financial-paper-analyzer/pull/36) · [#37](https://github.com/daegweon/financial-paper-analyzer/pull/37) — 모두 병합 완료  
> **운영 커밋:** `96393bf434b150106389693bffd8e35da0a42fca`  
> **최신 CI:** [Checks #44893776957](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44893776957) — 백엔드 247통과/1제외, 프런트엔드 단위 82통과, Playwright 9통과, 일회용 PostgreSQL 계약 통과  
> **Production:** Vercel READY, Railway API/Worker SUCCESS · Online 1/1.

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
5. 검색 결과는 한 번에 최대 100편을 가져오고 화면에는 10편씩 보여준다. 이미 가져온 페이지는 다시 API를 호출하지 않는다. 100편을 모두 탐색한 뒤 다음 페이지를 누르면 다음 100편을 추가로 가져온다.
6. 검색어를 입력하지 않아도 로그인 직후 분야별 추천 논문을 표시한다. 현재 추천 분야는 자산가격·금융시장, 포트폴리오·위험관리, ETF·시장 미시구조, 거시경제·금리·환율이다.
7. 검색 결과 및 추천 목록의 정렬 기준을 바꿀 수 있다: 추천/관련도순, 인용 수 높은 순, 논문 제목 가나다순, 첫 번째 저자 이름순, 최신 발표순.

**공개 열람(Open Access)은 재배포 허용을 의미하지 않는다.** OpenAlex 메타데이터에 기록된 라이선스가 누락되거나 불완전할 수 있다. 사용자는 해당 저작물의 이용 조건을 확인해야 한다. 서비스는 원문 파일을 공용 재배포하지 않고 개인용 비공개 버킷에 업로드한다.

## 추천 논문, 인용 수 및 정렬

### 검색어 없는 추천 목록

로그인한 사용자가 라이브러리에 진입하면 `GET /api/public-papers/recommendations`가 자동 호출된다. 검색창이 비어 있어도 아래 네 분야에서 공개 PDF가 확인된 논문을 추천한다.

- 자산가격·금융시장: `asset pricing financial markets`
- 포트폴리오·위험관리: `portfolio optimization investment risk`
- ETF·시장 미시구조: `exchange traded funds market microstructure`
- 거시경제·금리·환율: `interest rates exchange rates monetary policy`

각 분야에서 OpenAlex의 인용 수 높은 공개 논문을 우선 조회하고 PDF URL이 있는 항목을 최대 3편씩 선택한다. 분야 간 중복은 OpenAlex Work ID로 제거한다. 따라서 최대 12편이 표시되며, 특정 분야에서 PDF 공개본이 충분하지 않으면 그보다 적을 수 있다. 추천 목록은 API 인메모리 캐시로 15분 동안 재사용한다.

### 인용 수

- OpenAlex Work의 `cited_by_count`를 논문별 인용 수로 표시한다.
- UI에는 **OpenAlex 인용 N회**로 출처를 명시한다. Google Scholar, Scopus 등 모든 DB를 합산한 값이 아니며 각 DB의 집계는 다를 수 있다.
- OpenAlex의 인용 관계가 갱신되면 숫자도 바뀔 수 있다.
- 참고: https://help.openalex.org/data/works/attributes/ 및 https://help.openalex.org/data/common-attributes/

### 정렬

| UI 기준 | 구현 |
|---|---|
| 추천순/관련도순 | OpenAlex 검색 관련도 또는 분야별 추천 순서 보존 |
| 인용 수 높은 순 | OpenAlex `sort=cited_by_count:desc` |
| 논문 제목 가나다순 | OpenAlex `sort=display_name:asc` |
| 첫 번째 저자 이름순 | 브라우저에서 현재 불러온 결과의 첫 저자명을 한국어 로케일 기준으로 정렬 |
| 최신 발표순 | OpenAlex `sort=publication_date:desc` |

OpenAlex Works 정렬 문서: https://help.openalex.org/api/sorting/

**저자 이름순의 범위:** OpenAlex Works 목록에서 중첩된 저자 이름을 기준으로 전역 정렬하는 API 정렬 키는 사용하지 않는다. 따라서 이 기준은 현재 화면에 불러온 결과 묶음(최대 100편, 추가 페이지를 불러오면 누적된 결과) 내에서 정렬한다. 논문별 첫 번째 저자는 원문 서지정보의 제1저자와 항상 동일하다고 보장되지 않으므로, UI는 “첫 번째 저자”로 표기한다.

### 검색 결과 페이지 상태

- 검색 API는 한 번에 최대 100편을 요청하고, 화면은 10편씩 로컬 페이지로 표시한다.
- 이미 받아온 100편 내에서 이전/다음 이동은 브라우저 상태만 바꾸며 API를 다시 호출하지 않는다.
- 현재 묶음의 마지막 화면에서 다음을 누르면 다음 OpenAlex API page를 가져와 결과 배열에 추가한다.
- 검색어를 입력창에서 수정/삭제해도 이미 표시 중인 `publicSearch.query`는 바뀌지 않는다. 페이지 이동은 검색 당시의 쿼리 스냅샷과 API page를 사용한다. 새 검색어는 검색 버튼을 눌러야 적용된다.
- 정렬 기준을 변경하면 저장된 검색어 스냅샷으로 첫 API 페이지부터 다시 가져온다.

## API 및 코드

| API | 인증 | 응답 | 역할 |
|---|---|---|---|
| `GET /api/public-papers/recommendations` | 유효한 사용자 Bearer JWT | 분야별 최대 12편의 추천 공개 PDF 논문(JSON) | 검색어 없는 추천 목록 |
| `GET /api/public-papers/search?query=<text>&page=<1..100>&sort=<mode>` | 유효한 사용자 Bearer JWT | OpenAlex 메타데이터/페이지 상태(JSON, 100편/요청) | 공개 학술논문 검색 및 정렬 |
| `POST /api/public-papers/download` / `{"url":"https://..." }` | 유효한 사용자 Bearer JWT | `application/pdf` 바이트, `Cache-Control: no-store` | 검증된 공개 PDF 가져오기 |

- 백엔드: [`backend/app/public_papers.py`](../backend/app/public_papers.py) (공개 검색, 안전한 다운로드), [`backend/app/main.py`](../backend/app/main.py) (Router 등록).
- 프런트엔드: [`frontend/app/page.tsx`](../frontend/app/page.tsx) (검색·가져오기 UX 및 기존 `upload(File)` 재사용), [`frontend/app/globals.css`](../frontend/app/globals.css) (반응형 UI).
- 단위/보안 테스트: [`backend/tests/test_public_papers.py`](../backend/tests/test_public_papers.py) (추천 분야 응답/15분 캐시/인용 수/정렬 파라미터 포함).
- 브라우저 회귀: [`frontend/tests/e2e/auth-and-workspace.spec.ts`](../frontend/tests/e2e/auth-and-workspace.spec.ts) (검색어 없는 추천 목록, 인용 수/저자·인용 정렬, 검색어를 지운 뒤 저장된 검색 스냅샷으로 페이지 이동 포함).

### OpenAlex

- API: `https://api.openalex.org/works`, `search=<query>`, `filter=is_oa:true`, `per_page=100` (키워드 검색); 추천은 분야별 `per_page=25`, `sort=cited_by_count:desc`로 검색한 뒤 PDF가 있는 상위 3편을 선택한다.
- 키워드 검색의 서버 정렬 값은 `relevance`, `citations_desc`, `title_asc`, `year_desc`, `author_asc`다. 저자 이름순은 프런트엔드 정렬이다.
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

검증 기준: [GitHub Actions #44893471811](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44893471811).

- 백엔드: 기존 회귀 포함 **247 passed, 1 skipped**.
- 프런트엔드: TypeScript/Next 빌드, 단위 테스트 **82 passed**.
- Playwright: **9 passed**. 신규 테스트는 검색 → PDF 가져오기 → 사용자 Bearer 인증 → 기존 비공개 업로드, 검색어 없는 추천 목록, 인용 수 표시, 인용/저자 정렬, 검색어를 비운 뒤 기존 검색 쿼리 스냅샷으로 다음 페이지 이동을 검증한다.
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
