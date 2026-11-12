# Financial Paper Analyzer

Evidence-first financial research paper workspace.

## MVP
- Supabase email/password authentication and private PDF upload (30 MiB max)
- Per-user RLS on documents and analyses
- Python FastAPI + PyMuPDF text extraction
- Page-grounded extractive results; optional OpenAI interpretation
- Next.js frontend on Vercel; API on Railway

## Environment
Frontend (Vercel): NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY, NEXT_PUBLIC_API_URL
Backend (Railway): SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, FRONTEND_ORIGIN, OPENAI_API_KEY (optional), OPENAI_MODEL (optional)

No service-role key or AI secret goes in the browser or source control.
Extractive analysis is NOT generative AI or verified empirical research. Read the source paper before relying on interpretations.

## Local run
Frontend: cd frontend && npm install && npm run dev
Backend: cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
Tests: cd backend && pip install -r requirements-dev.txt && pytest

Database migration: supabase/migrations/20261113000000_initial_schema.sql
