# Gemini live analysis verification

**Verified:** 2026-11-13 (KST)  
**Paper:** PaperSignal synthetic QA test paper (2 pages)  
**Paper ID:** `a3b0a770-48e4-4fee-8a93-ae02f5abba73`  
**Analysis ID:** `2283e7d9-2e6b-445b-ab29-9347b906f358`  
**Job ID:** `f8e54998-a08c-4005-ba6a-7cfb5ac5da7b`

## Production result

| Field | Verified value |
|---|---|
| Job status | `completed` |
| Job stage | `completed` |
| Error | `null` |
| Provider | `gemini` |
| Model actually used | `gemini-3.5-flash-lite` |
| Analysis mode | `llm` |
| Analysis schema version | `finance-structured-v3` |
| Pages analyzed | 1 and 2 |
| Evidence excerpts after exact-page validation | 7 |
| Findings | 1 |
| Limitations | 1 |
| Hypotheses / contributions / robustness checks | 0 / 0 / 0 |

The job was created at 02:53:24.815 UTC and completed at 02:53:32.002 UTC (approximately 7.2 seconds). The analysis row was persisted at 02:53:31.246 UTC and is referenced by the completed job.

Railway request logs confirm:
- `POST /api/analyze/{paper_id}` returned HTTP 202.
- Authenticated status polling returned HTTP 200.
- The frontend received the completed state and displayed its success message.

## Content quality notes

The input is synthetic software QA material, not a real academic paper. Gemini correctly identified it as artificial test content and explicitly stated that it contains no real market observations, investment recommendations, or causal claims.

The one finding describes the fabricated illustrative factor correlation of 0.15, with statistical significance marked "확인 불가". The paper's stated limitations (no genuine data collection, identification strategy, out-of-sample validation, or significance calculation) were extracted.

All seven stored evidence excerpts passed the backend's exact-page substring validation before persistence. This verifies citation-to-page matching, not the scientific truth of model interpretations.

## Operational conclusion

- Gemini API key works for a real production request.
- The Flash-Lite primary model completed successfully; fallback was not needed for this run.
- The asynchronous job lifecycle, Supabase persistence, and frontend status polling worked end-to-end.
- This run validates a synthetic two-page test document only. A set of real, public finance/economics papers is still needed to evaluate analytical quality.
