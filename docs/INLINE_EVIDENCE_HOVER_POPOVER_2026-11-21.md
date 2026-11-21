# PaperSignal — 인라인 원문 근거 마이크로 인터랙션

> **작성:** 2026-11-21 KST  
> **개선 PR:** #41 — hover / info popover evidence UX  
> **상태:** 본문 간격·글자 크기 조절·수식 기호 해설 구현 / 최신 CI 및 Preview 검증 중

## 왜 PR #38의 접기 UI를 다시 바꾸는가

실제 운영 화면 피드백에서 근거를 접어 두더라도 "원문 근거 보기" 행이 모든 주장 아래에 반복되어 시각적 잡음이 남는다는 점을 확인했다. 근거를 확인하지 않는 대부분의 독자는 인용문뿐 아니라 근거 컨트롤 자체도 거의 볼 필요가 없다.

따라서 근거를 별도 행이나 카드로 렌더링하지 않고, **해당 주장/설명 텍스트에 붙는 작은 인라인 정보 아이콘**으로 바꾼다.

## UX 결정

### 화면 기본 상태

- 근거가 있는 실제 주장/설명 텍스트 전체를 hover 대상으로 만들고, 문장 끝에 작은 원형 `i` 아이콘 하나를 붙인다. 아이콘뿐 아니라 문장 위에 포인터를 올려도 근거가 열린다.
- 여러 원문 페이지/인용문이 하나의 주장에 연결되면 여러 행이나 여러 아이콘으로 늘리지 않고, 아이콘 하나가 모든 연결 근거를 연다.
- 기본 화면에는 인용문, 페이지 배지, 초록색 박스, 별도 "원문 근거 보기" 행이 나타나지 않는다.
- 근거가 없는 내용에는 아이콘을 렌더링하지 않는다.

### 데스크톱 포인터 상호작용

- 주장/설명 텍스트에 마우스를 올리면 포인터 옆에 **비대화형 미리보기**가 열린다. 첫 번째 원문 인용의 일부(최대 180자)와 PDF 페이지, 추가 근거 개수를 간결하게 표시한다.
- 포인터가 주장 텍스트 위를 움직이면 미리보기도 포인터를 따라간다. 미리보기 자체로 포인터를 이동해도 닫히지 않으며, 포인터가 주장과 미리보기 영역을 모두 벗어나면 닫힌다.
- 작은 `i` 아이콘을 클릭하면 미리보기 대신 **상세 근거 팝오버**가 열린다. 연결된 모든 원문 인용과 PDF 페이지 이동 액션을 제공한다.
- 상세 팝오버는 바깥 클릭 또는 ESC로 닫으며, 아이콘을 다시 누르는 동작도 닫기로 처리한다.

### 키보드 및 터치

- 키보드 포커스가 아이콘에 오면 비대화형 미리보기가 열린다. Enter/Space는 전체 근거 상세 팝오버를 열고 ESC는 닫는다.
- 터치 기기에는 hover가 없으므로 아이콘 탭으로 상세 근거를 열고, 다시 탭하거나 바깥을 탭해 닫는다.
- 버튼에는 설명형 accessible name, `aria-expanded`, `aria-controls`, visible focus ring을 제공한다.
- 팝오버는 최대 높이를 제한하고 내용이 길면 내부 스크롤한다.

### 팝오버 내용

- 원문 PDF 페이지 번호
- 실제 추출된 원문 인용문
- PDF가 연결된 경우 원문 페이지 함께 보기/새 탭 확인 링크
- 한 주장에 여러 근거가 있으면 하나의 팝오버 안에서 각각 구분해 표시

### 인쇄 및 PDF 저장

화면에서는 닫혀 있는 팝오버의 원문 인용문도 브라우저 인쇄/PDF 출력에서는 모두 표시한다. 작은 `i` 아이콘은 출력하지 않는다.

## 구현

- 공통 컴포넌트: `frontend/components/EvidencePopover.tsx`
- 분석 보고서 EvidenceList: `frontend/app/page.tsx`
- 주니어 3분 가이드의 실증 결과 근거: `frontend/components/JuniorPaperGuide.tsx`
- 스타일 및 인쇄 규칙: `frontend/app/globals.css`
- 브라우저 회귀: `frontend/tests/e2e/auth-and-workspace.spec.ts`

## UI/UX 검토 원칙

- 정보 위계: 논문의 분석 주장과 결과가 1차 콘텐츠이며 출처 확인은 2차 콘텐츠다.
- Progressive disclosure: 독자가 요청할 때만 원문 인용을 표시한다.
- Low visual noise: 반복적인 full-width evidence row/card를 제거하고 inline affordance 하나로 대체한다.
- Discoverability: 작은 i 아이콘과 hover preview가 출처 확인 기능의 존재를 알려준다.
- User control: hover preview와 click-to-open 상세 근거를 분리해 사용자가 확인 깊이를 선택한다.
- Accessibility: 마우스만으로 기능을 제한하지 않고 키보드·터치·스크린리더 이름을 제공한다.
- Fidelity: 화면에서 숨겨도 인쇄/PDF에는 인용 근거를 보존한다.

## 검증 체크리스트

### 자동 검증 결과 (2026-11-21)

- 최초 인라인 팝오버 구현 커밋 `ec4d95ef1bd08d58330b2e3ed16c30fd4b1d6892` 기준 GitHub Actions [#44905544098](https://github.com/daegweon/financial-paper-analyzer/actions/runs/44905544098): 전체 3개 job 성공(Backend 247 passed/1 skipped, Frontend unit 82 passed, Playwright 9/9, PostgreSQL 계약 통과).
- 후속 코드 리뷰에서 주니어 가이드 중복 i 아이콘 제거, 키보드 포커스, tooltip/dialog 의미, hover 미리보기와 전체 상세 보기 분리를 보완했다. 최신 2026-11-22 변경에서는 본문 간격, 읽기 크기 조절, 수식 기호 파싱을 추가했다.
- 회귀 테스트에는 포인터 추적, 미리보기 hover 유지, Enter/ESC, 상세 팝오버 바깥 클릭, 주니어 가이드의 주장당 아이콘 1개, 인쇄 시 전체 인용문 보존을 추가했다.
- 이전 시점에는 Vercel 일일 배포 제한 오류가 있었으나, 이후 exact-head Preview 배포가 READY로 성공했다. 최신 변경은 GitHub 연동 Preview를 사용하며, 별도 수동 배포 요청으로 한도를 시험하지 않는다.


1. 인용 근거가 있는 문장 옆에 작은 i 아이콘 하나만 표시되는가.
2. 주장 텍스트 hover 시 첫 인용 일부와 페이지 번호가 작은 미리보기로 표시되는가.
3. 미리보기가 포인터를 따라가며, 미리보기 자체로 포인터를 이동해도 닫히지 않는가.
4. i 클릭 시 모든 인용문과 원문 페이지 이동을 포함한 상세 팝오버가 열리는가.
5. 상세 팝오버가 바깥 클릭/ESC로 닫히는가.
6. 키보드 포커스/Enter/Space 및 모바일 탭으로 열고 닫을 수 있는가.
7. 여러 인용이 한 아이콘의 팝오버에 모이는가.
8. 기본 화면에서 이전의 접기 행/초록색 인용 카드가 완전히 사라졌는가.
9. 인쇄/PDF 출력에는 모든 원문 인용문이 포함되는가.
10. PDF 페이지 이동, 기존 분석·라이브러리 우선 레이아웃은 유지되는가.

초기 구현 CI는 통과했지만 후속 UX 보완의 테스트 결과와 최신 Preview 검증은 남아 있다. GitHub Actions 사용량 제한을 존중해 수동 재실행하지 않는다. Vercel 일일 배포 한도 복구 후 최신 HEAD의 Preview를 확인하고, 그 전에는 Production 병합/배포하지 않는다. 외부 백엔드, 데이터베이스, 분석 엔진 변경은 없다.


## 후속 가독성 개선 — 2026-11-22

사용자 Preview 검토에서 확인된 세 가지 보완을 같은 PR #41에 추가한다.

1. 본문과 근거 i 버튼 사이에 8px 간격을 둔다.
2. 모형 및 수식 아래에 기호별 해설을 제공한다. 논문에서 추출한 변수 정의가 있으면 그것을 우선 사용하고 원문 인용이 있으면 근거 팝오버로 연결한다. 추출 정의가 없는 기호는 함수 입력, 계수, 상수항, 지수, 로그, 기댓값 등의 일반적인 수학적 역할만 설명하고 논문 내 경제적 의미를 추측하지 않는다.
3. 분석 보고서 본문, 섹션 제목, 방법론, 수식, 근거 팝오버와 주니어 학습/표·그래프/직무 가이드의 폰트 크기와 줄 간격을 확대한다.

회귀 테스트는 수식 두 개와 변수 C의 추출 정의를 포함해 기호 10개의 해설, 원문 정의, 본문 15px, 근거 아이콘 간격 8px를 검증한다.


## 2026-11-22 follow-up: inline spacing, reader controls and equation symbol coverage

The user's next Preview review showed that the paragraph-level evidence icon still looked crowded, the report needed user-controlled font sizing, and the symbol guide was not visible in the older Preview URL.

- The claim text and info button are now separated by a dedicated inline spacer (.evidence-inline-gap, 0.65em) rather than relying on button margin. The spacing is tested by measuring its rendered width.
- The sticky report toolbar now has A− / A+ / 기본 controls. The scale ranges from 80% to 140% in 10% steps, affects the analysis report and junior learning sections, and persists under papersignal-reading-scale in localStorage. It is hidden in print output.
- Equation parsing now splits the common implicit-multiplication pattern aCb into a, C, and b, while preserving case so C and c remain distinct. The exact sample L(C) = aCb + c and -EP [log(pass_rate(C))] = α*C^-k are covered by the browser fixture.
- Extracted variable definitions and their page-level source evidence are passed into the equation guide, so the guide can link back to the original PDF.
- The browser test checks all 10 symbols, the extracted definition for C, the separate c constant, the spacer width, the A+ scale change, and localStorage persistence.


## 2026-11-22 follow-up: reading default, quiz legibility, and evidence consolidation

- Reading-size default and reset are now 90%. The previous release wrote its default 100% to localStorage on first load; that legacy default is migrated to 90%, while other explicit saved sizes are preserved. The user's new A−/A+ selection remains persisted.
- Removed the equation parameter/symbol explanation block from the report. The equations themselves remain visible.
- Increased only the "논문 읽기 이해도 점검" quiz heading, question, answer options and explanations, with the same reader scale applied.
- The "주요 변수" heading now owns one parent evidence i. Identical page+quote citations shared by multiple variables are de-duplicated into one citation and list all related variable names in the same popover. Individual variable cards no longer repeat their own i.
- User explicitly requested no GitHub Actions. The changes are prepared as an unreferenced Git commit object and have not been pushed to the PR branch; no Actions were triggered and no deployment was created.
