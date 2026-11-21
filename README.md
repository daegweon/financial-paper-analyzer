# Financial Paper Analyzer

Evidence-first financial research paper workspace.

## Product architecture

- Frontend: Next.js on Vercel
- API: Python FastAPI + PyMuPDF on Railway
- Auth, PostgreSQL, private PDF Storage: Supabase (Seoul)
- Source of truth: this private GitHub repository

## AI provider configuration

The backend supports a provider switch. No provider API key is stored in the browser or committed to this repository.

### Current default: Gemini

Set these variables on the Railway `papersignal-api` service:

- `AI_PROVIDER=gemini`
- `GEMINI_API_KEY=<secret>`
- `GEMINI_MODEL=gemini-3.5-flash-lite`
- `GEMINI_FALLBACK_MODEL=gemini-3.6-flash`

Gemini 3.5 Flash-Lite is the current primary model; Gemini 3.6 Flash is the fallback when the primary model is temporarily unavailable. The Gemini Free Tier offers free input and output tokens subject to project-specific RPM, TPM and RPD limits. Check the actual limits in Google AI Studio. The free tier may use submitted prompts and responses to improve Google products and may involve human review. Do not submit sensitive, confidential, or personal information to unpaid Gemini services. For PaperSignal, restrict free-tier use to public or synthetic papers and show the in-app data-use notice.

Official references:
- https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite
- https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/rate-limits
- https://ai.google.dev/gemini-api/terms

### Future provider: OpenAI

When an OpenAI API key and billing are available, switch providers in Railway:

- `AI_PROVIDER=openai`
- `OPENAI_API_KEY=<secret>`
- `OPENAI_MODEL=<available-model-id>`

No application data migration is required. Both providers return the same normalized analysis schema and use the same page-level evidence verification.

## Analysis engine v6.3

New analyses use `finance-structured-v6.3`. In addition to the v6.2 research-design-aware validation pipeline, v6.3 adds:
- explicit classification of balanced/unbalanced panels, repeated cross-sections, time series, cross-sections and portfolio-optimization studies;
- typed integer sample dimensions and source-level sample-count reports, preserving conflicting values across abstracts, methodology sections and tables;
- N×T checks only for evidence-backed balanced panels; unbalanced and non-panel designs are not multiplied;
- table/model/column context and separate regression-significance legend citations;
- context-aware p-value, significance-star and summary-to-findings consistency screens;
- a conditional table-first third-pass recovery for empirical papers whose first two passes return no supported findings;
- explicit findings_coverage states (supported, review_required, incomplete, not_assessable) so job completion is not confused with extraction completeness.

See [v6.2 architecture and limitations](docs/analysis-v6.2.md) and [v6.3 findings recovery](docs/analysis-v6.3.md). These checks are triage aids, not semantic proofs; table alignment, coefficient interpretation, sample definitions and claim-to-citation entailment still require researcher review.

## Analysis output

Gemini output budgets are 16,384 tokens for the primary Flash-Lite model and 24,576 tokens for the fallback Flash model. If the primary response ends with `MAX_TOKENS`, the worker automatically retries with the fallback model. Results are kept concise and evidence lists are bounded to reduce truncation. Analysis schema v6.3 normalizes PDF typography, classifies study designs and performs field-level evidence, sample-count and table-significance checks (Unicode ligatures, dash variants, and whitespace) when validating citations, then stores the matched excerpt from the original extracted page text. It also preserves individually evidenced variables when a section-level methodology citation is unavailable, and strengthens Korean output / empirical-findings instructions.

The structured financial-research report includes:

- Bibliographic metadata and executive summary
- Research question, hypotheses, and academic contributions
- Research design, sample, period, data sources, variables, equations, and identification strategy
- Empirical findings with direction, estimates, and statistical significance when explicitly reported
- Robustness checks, limitations, and finance/economic implications
- Page-level evidence excerpts

Every generated citation is checked against the extracted text of its stated PDF page. Unsupported claims without a verifiable quote are removed. This reduces fabricated citations but does not guarantee that the model's interpretation is correct.

## Security and privacy

- Supabase email/password and Google OAuth authentication
- Per-user Row Level Security for papers and analyses
- Private Storage bucket; PDF objects are not public
- Backend validates the user's JWT and uses that JWT for all Supabase reads/writes
- No service-role key or AI API key belongs in the browser or source control
- Free Gemini tier: extracted paper text and responses may be used by Google to improve products and may be reviewed by humans. Do not upload confidential or personal data.

When AI mode is enabled, extracted paper text is sent from Railway to the configured model provider. Use only documents you are permitted to process with that provider.

**Current Auth security limitation:** the Supabase organization is on the Free plan. Supabase's built-in leaked-password protection (HaveIBeenPwned check) is available on Pro and above, so it is not enabled in this project. Do not treat it as active or upgrade the project without explicit billing approval.

## Environment

Frontend (Vercel):
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
- `NEXT_PUBLIC_API_URL`

Backend (Railway):
- `AI_PROVIDER` (default `gemini`)
- `GEMINI_API_KEY` (optional secret)
- `GEMINI_MODEL` (default `gemini-3.5-flash-lite`, optimized for low-latency document parsing)
- `GEMINI_FALLBACK_MODEL` (default `gemini-3.6-flash`, used on transient timeout/429/5xx or unavailable model responses)
- `OPENAI_API_KEY` (optional secret for future provider switch)
- `OPENAI_MODEL`
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `FRONTEND_ORIGIN`
- `PAPERSIGNAL_ADMIN_USER_IDS` (comma-separated approved Supabase Auth UUIDs; server-only administrator allowlist)
- `PAPERSIGNAL_ADMIN_MONTHLY_AI_BUDGET_USD` (optional initial service-wide reporting budget)
- `GEMINI_BILLING_MODE` (set to `free` or `paid_standard` only after confirming the actual Google AI Studio billing tier)

Set secrets only in Railway's service Variables UI. Never commit them to GitHub or expose them as `NEXT_PUBLIC_*` variables. Keep the administrator allowlist empty until the intended Auth UUID is explicitly confirmed. Do not guess Gemini billing mode; unknown costs are excluded from confirmed-cost totals.

## Current PDF limits

- Maximum upload size: 30 MiB
- PDF page count: 1–300
- Text analysis scans the first 50 pages
- Image-only/scanned PDFs require OCR, which is not included yet
- Analysis requests return immediately with a job ID; the frontend polls the RLS-protected analysis_jobs table.
- A separate Railway Worker consumes the durable Supabase queue with leases, heartbeat, retries, checkpoints and idempotent result persistence.

## Local development

```bash
cd frontend
npm install
npm run dev

# Separate terminal
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Tests
cd backend
pip install -r requirements-dev.txt
pytest
```

Database migrations (the reconciled production sequence):
- `20261112155952_initial_paper_analysis_schema.sql`
- `20261112160036_authenticated_analysis_writes.sql`
- `20261113021557_analysis_jobs_async_queue.sql`
- `20261113161739_worker_leases_heartbeat_and_retry_rpc.sql`
- `20261113222551_analysis_stage_checkpoints_and_idempotent_results.sql`
- `20261113222605_make_analysis_job_id_unique_for_upsert.sql`
- `20261113222644_index_analysis_job_foreign_keys.sql`
- `20261113222754_explicit_service_role_checkpoint_policy.sql`
- `20261113234956_cleanup_terminal_analysis_job_checkpoints.sql`
- `20261120102957_beta_server_owned_result_writes.sql`
- `20261120122747_server_owned_analysis_quota.sql`
- `20261120122819_ai_usage_events_ledger.sql`
- `20261120122859_index_ai_usage_ledger_foreign_keys.sql`
- `20261121032957_restrict_ai_usage_ledger_privileges.sql`

The AI usage ledger is append-only: the server role can read and insert events but cannot update, delete, truncate, or attach triggers to the ledger. The administrator settings table allows only read/insert/update for the server role.

## Production synthetic E2E

A deliberately manual workflow verifies the live authentication, private PDF Storage, real Gemini analysis, and cross-account isolation without using customer accounts.

1. Open the repository's **Actions** tab and select **PaperSignal Live E2E - Manual Approval**.
2. Select branch `main` and click **Run workflow**.
3. Set `target=papersignal-production`, `approve_mutations=true`, and `acknowledgment=RUN_SYNTHETIC_LIVE_E2E`.
4. Copy the exact current `main` commit SHA into `approved_commit`. The workflow refuses a stale or different SHA.
5. Confirm the repository Actions secrets `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `PAPERSIGNAL_API_URL` are configured.

The workflow checks the live API is in Gemini AI mode before creating any fixture. It then creates two short-lived QA Auth users, uploads a synthetic two-page PDF, runs a real Gemini-backed analysis, verifies original PDF bytes and owner-only access, and checks that the second user cannot access the paper, job, analysis, or private PDF. It deletes only the fixture records and QA users it created after the analysis reaches a terminal state. If a job is still running or cleanup fails, it deliberately retains the relevant QA resources for manual recovery rather than racing the Worker or deleting unrelated data.

## Finance paper quality benchmark

A ten-paper open-access candidate set, source-grounded expected facts, human-review template, and screening evaluator are available in [`benchmark/`](benchmark/README.md). The benchmark has not yet been run on all ten PDFs. Alias coverage is a screening signal only; factual accuracy and page citations require human review against the publisher PDF.
