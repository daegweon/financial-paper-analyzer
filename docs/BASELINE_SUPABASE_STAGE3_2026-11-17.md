# PaperSignal — Q0 3단계: 독립 Supabase QA 환경 구축 (2026-11-17)

## 상태
- **신규 비운영 Supabase 프로젝트 생성 완료**: `papersignal-benchmark` (`cstaglfqviojdxisckjm`).
- 조직: `eevee` (`ftusrgbzvrjrypvbkvgz`).
- 리전: `ap-northeast-2` (서울).
- 프로젝트 생성 견적: **월 $0**; 사용자 승인 후 생성.
- 프로젝트 상태: `ACTIVE_HEALTHY`. 운영 프로젝트 `hwmtayrecsfxernhssro`는 변경하지 않음.

## 배포된 데이터베이스 스키마

기존 운영 저장소의 SQL을 그대로 사용해 다음 **9개 재현 마이그레이션**을 새 프로젝트에만 적용했다.

1. `20261113000000_initial_schema.sql`
2. `20261113010000_analysis_jobs.sql`
3. `20261114000000_durable_analysis_worker.sql`
4. `20261114010000_worker_leases_heartbeat_and_retry_rpc.sql`
5. `20261114020000_prevent_duplicate_active_analysis_jobs.sql`
6. `20261114030000_analysis_stage_checkpoints_and_idempotent_results.sql`
7. `20261114040000_index_analysis_job_foreign_keys.sql`
8. `20261114050000_explicit_service_role_checkpoint_policy.sql`
9. `20261114060000_cleanup_terminal_analysis_job_checkpoints.sql`

추가로 `paper_benchmark_private_artifact_bucket` 마이그레이션을 적용해 분석 결과 전용 비공개 JSON 버킷을 구성했다.

| 대상 | 검증 |
|---|---|
| `public.papers` | 생성, RLS 활성화, 0행 |
| `public.analyses` | 생성, RLS 활성화, 0행 |
| `public.analysis_jobs` | 생성, RLS 활성화, 0행 |
| `public.analysis_job_checkpoints` | 생성, RLS 활성화, 0행 |
| `auth.users` | 0건 |
| `storage.buckets.papers` | 비공개, PDF 30 MiB 제한 |
| `storage.buckets.papersignal-benchmark-artifacts` | 비공개, JSON 10 MiB 제한 |
| 4개 public 작업/보조 RPC | `anon` 및 `authenticated` EXECUTE 금지, `service_role`만 허용 |
| Supabase Security Advisor | lint 0건 |
| Supabase Performance Advisor | 빈 DB에서 아직 호출되지 않은 인덱스 11개 INFO; 성능 장애나 삭제 대상으로 판단하지 않음 |

운영 Auth, Storage, 논문 및 분석 데이터는 **복사하지 않았으며 변경하지 않았다**. 각 정책은 원래 저장소의 `auth.uid()=user_id` 기반 소유권 제한을 유지한다.

## Railway 테스트 서비스 설정

- 재사용 전용 서비스: `papersignal-table-benchmark` (`c279046d-aedc-43bf-9e25-c09ab59fe38b`).
- Railway 환경은 기존 프로젝트 `production`이지만 서비스는 **운영 API/Worker와 분리**되어 있다.
- `SUPABASE_URL`: `https://cstaglfqviojdxisckjm.supabase.co`.
- `SUPABASE_PUBLISHABLE_KEY`: 신규 프로젝트의 공개형 키로 설정.
- `SUPABASE_SERVICE_ROLE_KEY`: 이전 운영 프로젝트 키를 더 이상 사용하지 않도록 **안전한 무효 플레이스홀더**로 교체했다.
- `BENCHMARK_ALLOWED_SUPABASE_HOST`: `cstaglfqviojdxisckjm.supabase.co`.
- `BENCHMARK_ENABLE_ISOLATED_WRITES`: `false` — 실제 Gemini QA/DB 쓰기는 여전히 비활성화.
- 운영 `papersignal-api`, `papersignal-worker` 환경변수나 배포는 변경하지 않음.

**남은 연결 의존성**: Supabase 플러그인은 신규 프로젝트의 발급된 `sb_secret_` 키를 반환하지 않는다. 사용자가 Supabase 대시보드의 **Project Settings → API Keys → Secret keys**에서 새 프로젝트의 서비스용 Secret Key를 확인해 Railway의 **papersignal-table-benchmark → Variables → SUPABASE_SERVICE_ROLE_KEY**에 직접 넣어야 한다. 이 키를 ChatGPT 대화, GitHub, 로그 또는 응답 본문에 복사하면 안 된다. 기존 운영 키를 넣으면 안 된다.

## 4단계 실행 조건

1. 신규 프로젝트 전용 비밀 키가 Railway에 안전하게 설정됐음을 확인한다.
2. 벤치마크 서비스만 재배포하고 `/health` 정상 여부 확인한다.
3. B01–B10과 H01/H02 고정 PDF 12편의 SHA-256 사전 검증을 새 데이터베이스 대상 조건에서 다시 진행한다. Runner의 메모리 속 PDF는 재배포 후 소실될 수 있으므로 H01/H02를 다시 전달한다.
4. 전용 프로젝트로의 DB 분리·키 일치가 검증된 뒤에만 `BENCHMARK_ENABLE_ISOLATED_WRITES=true`를 설정하고, 우선 1편의 완료·저장 E2E 및 롤백 검증 후 12편 기준선을 수행한다.
5. Q0~P0 모두 계속 **BLOCKED**; 별도의 Gemini 실행 결과나 성능 수치가 없는 상태다.

## 주의

프로젝트 추가비용의 확인 견적이 월 $0이라는 뜻이며, Gemini 호출에 따른 사용량 또는 다른 서비스 추가요금까지 $0이라고 주장하는 것은 아니다. Secret Key는 운영 DB와 신규 QA DB 사이에서 절대 재사용하지 않는다.
