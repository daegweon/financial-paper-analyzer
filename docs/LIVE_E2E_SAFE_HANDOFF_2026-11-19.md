# PaperSignal — real-user E2E safety checkpoint (2026-11-19)

**Current state:** Draft PR #18; core API/Worker still on previous Railway Production image, not yet proven to emit `queue_write_mode=service_role`. No Production migration and no new real E2E Auth users. Engineering progress 86%, release gates 4/10 passed (`docs/PROJECT_PROGRESS.json`).

## Safe workflow for the next execution

1. Confirm GitHub PR #18 full Checks (including new progress validator) and Vercel Preview are READY. Never merge on synthetic UI QA alone.
2. Deploy the **updated API only**, under a reviewed release/change window, while preserving existing DB grants. Verify public `/health` answers `queue_write_mode=service_role`; verify the owned-paper enqueue/unauthorized-paper 404 and Worker health from non-sensitive, dedicated QA tests.
3. Only on reviewed `main`, select GitHub Checks → Run workflow → `e2e_target=production`, `confirm_live_e2e=true`, and acknowledgment `RUN_SYNTHETIC_LIVE_E2E`. The job has no ability to run on a PR or without explicit confirmation.
4. The Python test independently requires exact origins `https://hwmtayrecsfxernhssro.supabase.co` and `https://papersignal-api-production.up.railway.app` and server-owned `/health` marker **before** creating two synthetic confirmed Auth users and a 2-page synthetic PDF.
5. Verify temporary-user login, private PDF upload, job completion, saved page evidence, and non-owner denial. Cleanup removes only test-created resources after terminal job completion; a non-terminal job retains its fixture to avoid Worker racing a deleted source.
6. After real API/E2E passes, apply *only* the reviewed `20261117215315_beta_server_owned_result_writes.sql` migration, reconciling remote migration history first. Run postgrant checks and re-run E2E. Never use blanket `supabase db push`.

## Hard blockers

- The GitHub workflow approval inputs and Python guard are new candidate code, NOT yet on main; **do not dispatch the current old main workflow** and assume it has this guard.
- Secrets are not to be pasted into chat or committed. Opt-in live-E2E can incur Gemini API calls and creates temporary Auth/PDF records, so explicit owner approval is needed.
- Testing against live account/Storage, external email SMTP, physical mobile Safari and staged Production rollback remain unverified. Do not claim full beta readiness.

## Cross-session restart

New session must read `AGENTS.md`, `docs/PROJECT_PROGRESS.json`, `docs/PROJECT_STATE.md`, `docs/PROJECT_DECISIONS.md` and `docs/PROJECT_CHANGELOG.md` and inspect live CI/deployment state. Every progress report shows **86% engineering / 4 of 10 live release gates** until verified milestones change the ledger.

## Current API-only readiness proof

- Live `/health` still returns no `queue_write_mode` (legacy), though HTTP 200 and no-auth status 401 passed. PR #18 candidate runtime, with dummy config, returns service_role; do not confuse these.
- Exact successful CI: https://github.com/daegweon/financial-paper-analyzer/actions/runs/44458536952. Two-stage isolated grant verification passed; no production migration/deploy. GitHub main-only manual workflow requires a reviewed bootstrap or trusted explicit runner before it can use unmerged candidate guard code.
- Keep 86% engineering and 4/10 passed release gates from `docs/PROJECT_PROGRESS.json` as next-session baseline.

## API live since 2026-11-19

- The live API is no longer a legacy deployment: `0b5716db-b720-49db-b15c-babf77b26e5a` SUCCESS and queue writer `service_role` confirmed by public HTTPS. Worker unchanged. This satisfies the **preflight**, not the full E2E.
- Main-only `workflow_dispatch` guard is not merged because PR #18 remains Draft. Do not dispatch old main workflow or run GitHub production E2E without approved secure execution and temporary account handling.
- Canonical progress now 86% / 4 of 10 release gates. The next verified milestone will be real two-user Auth/Storage/queue E2E; DB migration is blocked until it passes.

## Storage E2E contract fix (2026-11-19)

- Previous fixture incorrectly used POST to bulk-delete PDFs. Now uses Storage DELETE with `prefixes`, verified against current Supabase Storage API and MockTransport unit test.
- Before invoking any real analysis queue, the E2E validates owner raw PDF bytes, private access denial, authorized signed download bytes and blocked non-owner signature issuance. Signed link contents remain secret and are never printed.
- E2E security/regression checks passed in https://github.com/daegweon/financial-paper-analyzer/actions/runs/44467502056. Real E2E still NOT run on Production; current fixture counts across Auth/Storage/papers/jobs were 0 in read-only SQL checks.
- Current canonical engineering score 87%, verified release gates 4/10; next task is manually approved live E2E, then targeted grant migration only after success.

## Human execution gateway (2026-11-19)

- Full beta PR #18 remains Draft, but a minimal Draft PR #19 https://github.com/daegweon/financial-paper-analyzer/pull/19 can register a standalone manual workflow on `main` after a human merges it. Its fixed source is PR #18 SHA `431059a1116a50f39fd56d565c35a1afc081b8fc`; main is NOT asked to merge unfinished product code.
- The pinned test checks fixture cleanup recovery and original signed PDF, user A/B authorization and durable real Worker completion. GitHub PR tests pass (backend 143/1 skip, browsers 24/24); no live E2E yet.
- Exact human actions are in `docs/HUMAN_E2E_HANDOFF_2026-11-19.md`. Current canonical progress 88% engineering and 4/10 passed beta gates.
