# PaperSignal — Live E2E private PDF and cleanup contract (2026-11-19)

**87% engineering; release gates 4/10 passed.** Verified code only, NOT a live production-authenticated test.

## Why this fix matters

Earlier harness `POST /storage/v1/object/papers` was not the Storage batch deletion endpoint. Current Supabase Storage API requires `DELETE /storage/v1/object/{bucket}` with `{ "prefixes": ["owner-id/exact.pdf"] }`. SQL deletion of `storage.objects` is insufficient to delete the backing file.

## Strengthened authenticated E2E order

1. Explicitly authorized main-branch/manual test with secret keys in secure runner; preflight exact Supabase/Railway target and `queue_write_mode=service_role` before creating any accounts.
2. Create only two uniquely named confirmed synthetic Auth users and a two-page synthetic finance PDF. User A uploads via Storage and inserts minimal paper metadata.
3. **Before any Gemini request:** user A must retrieve original private PDF bytes, user B must be denied direct PDF access; A may issue a 60-second signed URL and that URL must return exact bytes, B must be denied creating a signed URL.
4. User A queues analysis using JWT, waits for a terminal job, confirms saved analysis+page evidence. User B must get 404 from API and no paper/job/analysis/private source via own JWT.
5. Delete test-created analyses/jobs/paper, call Storage batch **DELETE** on only the exact test object, then delete only the two test Auth users. Non-terminal jobs retain fixtures for safe Worker recovery.

## Verification without production mutation

- GitHub CI https://github.com/daegweon/financial-paper-analyzer/actions/runs/44467502056 includes HTTPX MockTransport tests of batch DELETE and Storage access/signing. 133 backend PASS, 1 live opt-in test SKIPPED, browser 24/24 PASS, DB policy and frontend PASS.
- Independent read-only Supabase counts at checkpoint: synthetic test Auth users 0, paper rows 0, Storage objects 0, active test jobs 0.

## Hard constraints

- A signed URL is an intentionally transferable bearer capability. The authorization guarantee is that user B cannot issue its own for user A's private object.
- Client grants are still permissive; the reviewed SQL migration must NOT be applied before live 2-user E2E and reconciliation of remote migrations.
- Do not disclose secrets, spawn new paid infrastructure, change the Worker, or run the live test implicitly. The consolidated Draft PR #18 is not merged; safe main-only manual trigger not yet installed on main.

## Protocol references

- https://supabase.github.io/storage/ (DELETE /object/{bucketName})
- https://supabase.com/docs/guides/storage/management/delete-objects
- https://github.com/supabase/storage-js/blob/main/src/packages/StorageFileApi.ts
