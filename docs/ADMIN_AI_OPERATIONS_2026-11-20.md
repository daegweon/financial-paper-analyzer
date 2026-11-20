# PaperSignal 관리자 AI 운영 관리

## 권한 원칙

AI 토큰·비용·예산은 관리자 운영 정보다. 일반 사용자는 논문 분석, 원문, 학습과 개인 분석 이력만 사용하며 AI 원가·토큰·전체 예산 API에 접근할 수 없다. 프런트엔드에서 링크를 숨기는 것만으로 보호하지 않고, 백엔드가 Supabase Auth로 세션을 확인한 뒤 `PAPERSIGNAL_ADMIN_USER_IDS` allowlist와 정확히 일치하는 사용자만 허용한다.

## 관리자 화면

- `/admin/ai-usage`: 서비스 전체 월간 추정 비용, 전체 예산, 이벤트 수, 미확정 비용, 모델별 호출·비용 및 관리자 전용 사용자별 내부 집계
- 월간 전체 예산 편집: `POST /api/admin/ai-usage/budget`
- 요약 조회: `GET /api/admin/ai-usage/summary?month=YYYY-MM`
- 예산은 서비스 전체에 하나만 설정한다. 사용자별·논문별 예산은 제품 기능으로 제공하지 않는다. 사용자/논문별 비용은 관리자 내부 집계로만 제공한다.

## 서버 환경변수

- `PAPERSIGNAL_ADMIN_USER_IDS`: 쉼표로 구분한 관리자 Supabase Auth user UUID 목록. 서버 API 환경에만 설정한다. 일반 사용자 ID를 추가하지 않는다.
- `PAPERSIGNAL_ADMIN_MONTHLY_AI_BUDGET_USD`: DB에 저장된 예산이 아직 없을 때 사용하는 초기 기본값. DB 설정이 존재하면 DB 값을 우선한다.
- `SUPABASE_SERVICE_ROLE_KEY`: 기존 백엔드 전용 키. 브라우저 환경변수로 절대 노출하지 않는다.
- `GEMINI_BILLING_MODE`: Google AI Studio에서 실제 결제 등급을 확인한 경우에만 `free` 또는 `paid_standard`로 설정한다. 그 외에는 미확정 비용으로 남긴다.

## 데이터베이스

`20261120120000_ai_usage_events_ledger.sql`은 `ai_usage_events`와 `ai_admin_settings`를 만든다. 두 테이블 모두 RLS/FORCE RLS를 사용하고 anon/authenticated 권한을 제거하며 service_role만 접근한다. 관리자는 서버 API를 통해서만 월간 전체 예산을 변경한다. 관리자 user UUID와 설정 변경자 UUID는 서버가 인증한 세션에서 가져오며 요청 본문에서 신뢰하지 않는다.

## 비용 해석

- 금액은 Google 공식 가격표와 이벤트 당시 가격 버전을 기준으로 한 추정치이지 청구서가 아니다.
- 미확정 billing mode, 누락 토큰, 알 수 없는 모델 또는 가격 버전은 비용 미확정으로 남긴다.
- 확인된 비용만으로 예산을 초과한 경우 초과로 표시한다. 미확정 이벤트가 있으면 예산 이내라고 표시하지 않는다.
- 이 화면은 모니터링 및 관리자 정책 설정이다. 실제 요청 차단은 별도 서버 측 quota/enforcement 기능과 승인된 운영 배포가 필요하다.

## 운영 적용 전 보류 사항

후보 코드와 disposable PostgreSQL CI만 반영했다. 운영 Supabase migration, Railway deploy, Vercel Production promotion은 수행하지 않았다. 실제 적용 전 관리자 UUID 확인, 월간 예산 합의, migration 검토, staging E2E, 접근제어 검증과 롤백 절차를 사람이 승인해야 한다.