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

Set secrets only in Railway's service Variables UI. Never commit them to GitHub or expose them as `NEXT_PUBLIC_*` variables.

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

Database migrations:
- `supabase/migrations/20261113000000_initial_schema.sql`
- `supabase/migrations/20261113010000_analysis_jobs.sql`
- `supabase/migrations/20261114000000_durable_analysis_worker.sql` through `20261114060000_cleanup_terminal_analysis_job_checkpoints.sql`

## Finance paper quality benchmark

A ten-paper open-access candidate set, source-grounded expected facts, human-review template, and screening evaluator are available in [`benchmark/`](benchmark/README.md). The benchmark has not yet been run on all ten PDFs. Alias coverage is a screening signal only; factual accuracy and page citations require human review against the publisher PDF.
