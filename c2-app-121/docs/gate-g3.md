# Gate G3 Deliverables - Items 1 to 3

This file is the submission checklist for the first three Gate G3 requirements:

1. Deployed production URL
2. Evaluation metrics with more than one baseline number
3. Guardrails

## 1. Production deployment

Recommended deployment path for this repo:

- Backend + MCP clinical server: Railway, using the root `Dockerfile` and `railway.toml`.
- Database: Railway PostgreSQL.
- Frontend: Vercel, with root directory `c2-app-121-frontend`.

Why this path:

- The backend already has a production Dockerfile.
- Railway can build from that Dockerfile and inject `PORT`.
- The frontend already has Vercel SPA rewrites in `c2-app-121-frontend/vercel.json`.
- Cloud Run is also valid, but it adds more Google Cloud setup and IAM/build configuration.

Submission URL:

- Submit the Vercel frontend URL as the main production URL.
- Include the Railway backend `/health` and `/docs` URLs as verification evidence.

Expected evidence:

```text
Frontend: https://<your-frontend>.vercel.app
Backend health: https://<your-backend>.up.railway.app/health
Backend docs: https://<your-backend>.up.railway.app/docs
```

Use [deployment.md](deployment.md) for the exact Railway/Vercel steps.

## 2. Evaluation metrics

Implemented files:

- `eval/datasets/soap_eval_cases.json`
- `eval/run_soap_eval.py`
- `eval/results/report.md`
- `eval/results/soap_eval_latest.json`

Metrics produced:

- SOAP section coverage
- Clinical concept recall
- Unsupported content rate
- Average latency
- P95 latency
- Estimated cost per SOAP note

Offline smoke baseline:

```bash
python eval/run_soap_eval.py
```

Live LLM baseline, for final submission:

```bash
python eval/run_soap_eval.py --live --input-price-per-1m <PRICE> --output-price-per-1m <PRICE>
```

After the live run, submit/screenshot `eval/results/report.md`.

## 3. Guardrails

Implemented guardrails:

- Auth required for SOAP note generation.
- CORS allowlist for frontend origins.
- Rate limit middleware: 60 requests/min/client.
- Audio extension allowlist.
- Audio upload size limit: `MAX_AUDIO_UPLOAD_MB`.
- Transcript length limit: `MAX_TRANSCRIPT_CHARS`.
- Prompt-injection hardening by wrapping transcript as untrusted data.
- Medical safety instruction: do not invent medication, dosage, diagnosis, or direct patient advice.
- Output validation: SOAP output must contain S/O/A/P sections.

Relevant files:

- `src/core/guardrails.py`
- `src/api/clinical/service.py`
- `src/agents/tools/clinical.py`
- `src/api/middleware/rate_limit.py`
- `src/api/middleware/cors.py`

## Why not NeMo right now?

NeMo Guardrails is a good framework for a larger production hardening pass, especially for input rails, output rails, jailbreak detection, PII detection, and LangChain/LangGraph integration.

For this deadline, it is not the safest default because:

- The project already has heavy ASR dependencies: `transformers`, `torch`, and `ffmpeg`.
- Adding `nemoguardrails` increases dependency and deployment risk.
- The Gate G3 requirement says "Guardrails", not specifically "NeMo Guardrails".
- The current implementation gives concrete, testable rails inside the app boundary.

If the instructor explicitly requires NeMo, add it as a follow-up enhancement after deployment is stable.

## Remaining before submission

- Deploy backend on Railway and copy the production backend URL.
- Deploy frontend on Vercel and set `VITE_API_BASE_URL`.
- Update Railway `CORS_ORIGINS` with the Vercel URL.
- Run the live eval command once with current model pricing.
- Screenshot or submit `eval/results/report.md`.
