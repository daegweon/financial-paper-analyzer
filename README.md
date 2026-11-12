# Financial Paper Analyzer

Evidence-first financial research paper workspace.

## Product architecture

- Frontend: Next.js on Vercel
- API: Python FastAPI + PyMuPDF on Railway
- Auth, PostgreSQL, private PDF Storage: Supabase (Seoul)
- Source of truth: this private GitHub repository

## Analysis modes

### Extractive mode
Available without an AI provider key. Extracts text, detects finance-related keywords, and shows page-numbered source excerpts. It does not generate research findings or interpret econometric results.

### AI-assisted structured analysis
Enabled when `OPENAI_API_KEY` is configured on the Railway API service. The default model is `gpt-5.6-terra` (override with `OPENAI_MODEL`). The API uses Structured Outputs / JSON Schema and generates:

- Bibliographic metadata and executive summary
- Research question, hypotheses, and academic contributions
- Research design, sample, period, data sources, variables, equations, and identification strategy
- Empirical findings with direction, estimates, and statistical significance when explicitly reported
- Robustness checks, limitations, and finance/economic implications
- Page-level evidence excerpts

Every generated citation is checked against the extracted text of its stated PDF page. Unsupported claims without a verifiable quote are removed. This reduces fabricated citations but does not guarantee that the model's interpretation is correct.

**Privacy and cost:** When AI mode is enabled, extracted paper text is sent from Railway to the configured model provider for processing. OpenAI API usage is billed separately from ChatGPT subscriptions. Do not upload papers unless you have the right to process them with the configured provider.

## Security

- Supabase email/password authentication
- Per-user Row Level Security for papers and analyses
- Private Storage bucket; PDF objects are not public
- The backend validates the user's JWT and uses that JWT for all Supabase reads/writes
- No service-role key or AI API key belongs in the browser or source control

## Environment

Frontend (Vercel):
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
- `NEXT_PUBLIC_API_URL`

Backend (Railway):
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `FRONTEND_ORIGIN`
- `OPENAI_API_KEY` (optional secret)
- `OPENAI_MODEL` (optional; defaults to `gpt-5.6-terra`)

Set the AI secret in Railway's service Variables UI. Never commit it to GitHub or expose it as a `NEXT_PUBLIC_*` variable.

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
