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
- `GEMINI_MODEL=gemini-3.8-flash`

Gemini 3.8 Flash is the current default. The Gemini Free Tier offers free input and output tokens subject to project-specific RPM, TPM and RPD limits. Check the actual limits in Google AI Studio. The free tier may use submitted prompts and responses to improve Google products and may involve human review. Do not submit sensitive, confidential, or personal information to unpaid Gemini services. For PaperSignal, restrict free-tier use to public or synthetic papers and show the in-app data-use notice.

Official references:
- https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/rate-limits
- https://ai.google.dev/gemini-api/terms

### Future provider: OpenAI

When an OpenAI API key and billing are available, switch providers in Railway:

- `AI_PROVIDER=openai`
- `OPENAI_API_KEY=<secret>`
- `OPENAI_MODEL=<available-model-id>`

No application data migration is required. Both providers return the same normalized analysis schema and use the same page-level evidence verification.

## Analysis output

The structured financial-research report includes:

- Bibliographic metadata and executive summary
- Research question, hypotheses, and academic contributions
- Research design, sample, period, data sources, variables, equations, and identification strategy
- Empirical findings with direction, estimates, and statistical significance when explicitly reported
- Robustness checks, limitations, and finance/economic implications
- Page-level evidence excerpts

Every generated citation is checked against the extracted text of its stated PDF page. Unsupported claims without a verifiable quote are removed. This reduces fabricated citations but does not guarantee that the model's interpretation is correct.

## Security and privacy

- Supabase email/password authentication
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
- `GEMINI_MODEL` (default `gemini-3.8-flash`)
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
- Analysis currently runs synchronously in the API

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

Database migration: `supabase/migrations/20261113000000_initial_schema.sql`
