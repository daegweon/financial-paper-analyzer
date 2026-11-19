# PaperSignal API-only production rollout verification — 2026-11-19

Engineering 86% / 4 of 10 real beta release gates passed. **This file records a Production API service change, not a public beta release.**

### Immutable deployment evidence

| Resource | Verified value |
| --- | --- |
| Railway project/environment | `c663389c-453c-4645-a83d-299b94089864` / `0b4f06c3-504a-4610-8995-395c2f4d3d1f` |
| Modified service | `papersignal-api` (`81b678e2-7136-436d-9058-7d20647dc1b7`) only |
| Reviewed immutable source commit | `ace3fbd5dab3ea71efa3a49da8363259ea5f9732` |
| New API production deployment | `0b5716db-b720-49db-b15c-babf77b26e5a` SUCCESS |
| Prior API rollback point | `17c9134b-f49c-4358-a879-7ca77b55b936` |
| Unchanged Worker deployment | `dc501061-d434-454a-bc7d-4658b991a2f1` SUCCESS |
| Staged Railway config patch | `7cddfc33-29d7-4b33-801b-9df49ff5e940`, committed; zero staged changes remain |

### Checks actually performed

- Reviewed staged changes before commit: exactly two source fields, both on core API, destructive=false; no Worker or service variables touched.
- Railway new deployment became SUCCESS/Online, Worker remained SUCCESS/Online.
- GitHub Actions strict public API read-only HTTPS preflight validated `/health` 200, queue writer `service_role`, finance engine v6.4.2, anonymous GET job-status 401. Evidence: https://github.com/daegweon/financial-paper-analyzer/actions/runs/44462359704 .
- Railway runtime logs show Uvicorn started, repeated `/health` 200, anonymous `/api/analyze/.../status` 401.
- One-hour Railway HTTP error-rate snapshot: 10 total requests, 5 HTTP 4xx, zero HTTP 5xx. Small sample only.
- Supabase production still allows authenticated direct result/job INSERT and paper status UPDATE. **The security migration has not been applied.**

### Required next gate and rollback

- Do not run privileged live E2E from automatic PR tests; main-only GitHub dispatch safety controls are still part of unmerged PR #18.
- When explicitly authorized with secure QA secrets, provision only disposable confirmed test accounts and a synthetic public two-page PDF, test two-account Auth, real queue completion and private Storage denial. This may use Gemini quota. Cleanup only test assets after a terminal job.
- After E2E PASS, reconcile remote Supabase migration history, apply only `20261117215315_beta_server_owned_result_writes.sql`, verify read-only grants and rerun E2E.
- If API failure occurs **before DB migration**, restore previous API deployment. **After DB migration**, do NOT restore pre-service-role API, which cannot enqueue jobs once client INSERT is revoked.
- Do not automatically raise GitHub Actions $1 budget, deploy Worker, promote Vercel Production, enable broad CORS, or expose model keys.

The final deployment will not follow subsequent GitHub branch pushes because its Railway source is pinned to the immutable commit above. New work in PR #18 is not automatically live.
