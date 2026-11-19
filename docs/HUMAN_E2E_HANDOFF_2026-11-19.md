# PaperSignal — actions that require a human (2026-11-19)

**Current score:** 88% engineering; independently passed beta release gates 4/10. Real two-account live E2E NOT yet performed. This is a manual-approval procedure; do not paste secrets or passwords into chat.

## Required to unblock real E2E

1. [Review narrow Draft PR #19](https://github.com/daegweon/financial-paper-analyzer/pull/19). Check that `.github/workflows/papersignal-live-e2e.yml` is manual-only, pinned to audited source `431059a1116a50f39fd56d565c35a1afc081b8fc`, and does not include database migrations. If acceptable, mark Ready for review and merge **PR #19 only** into main. Do not merge product Draft PR #18.
2. In [GitHub Actions repository secrets](https://github.com/daegweon/financial-paper-analyzer/settings/secrets/actions), verify/create exactly four secret names: `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SERVICE_ROLE_KEY` and `PAPERSIGNAL_API_URL`. Use existing PaperSignal project and deployed API. GitHub connection used here cannot inspect or edit repository secrets; their presence has **not** been verified.
3. In GitHub → Actions → **PaperSignal Live E2E - Manual Approval** → Run workflow, select main. Set `target=papersignal-production`, `approve_mutations=true`, `approved_commit=431059a1116a50f39fd56d565c35a1afc081b8fc`, `acknowledgment=RUN_SYNTHETIC_LIVE_E2E`. Every input defaults to disabled/no authorization. The workflow can only appear after merging PR #19 into main.
4. Read the risk notice: the approved run creates 2 short-lived confirmed synthetic Supabase Auth accounts, 1 private two-page PDF, metadata and a real Railway Worker/Gemini analysis; it verifies A/B access restrictions. It may consume Gemini quota and can retain a fixture if the Worker is unfinished or cleanup needs manual recovery.
5. Share the resulting GitHub Actions run URL here (no credentials) or ask for a read-only post-run audit. The assistant can inspect CI logs, Railway health, and read-only Supabase fixture counts and advise whether it is safe to proceed to the separate client-write SQL migration.

## Optional human work for later beta gates

- Configure custom SMTP in Supabase and verify an external mailbox signup/confirmation before public invitations; built-in Free-tier email is not a complete public signup channel.
- Validate real iOS Safari/Android Chrome PDF experience, keyboard/voice-over, page jump, retry and link renewal on your devices.
- Assign a competent human reviewer to independently inspect paper citation accuracy in the outstanding 18 review-needed findings. Do not treat automatic screening as expert verification.

## What remains automatic and what is blocked

- Existing PaperSignal Railway API/Worker online; server-owned `/health` marker confirmed. Frontend Preview ready and CI regression tests green.
- Original user papers, result history and Worker's deployed code remain intact. No production DB permission migration has been executed.
- Next step after **real** live E2E PASS: reconcile Supabase remote migration history, review/apply only `supabase/migrations/20261117215315_beta_server_owned_result_writes.sql`, check postmigration grants and rerun the authorized E2E. Never blanket `db push` or roll the API back to the old browser-writer release after revocation.
