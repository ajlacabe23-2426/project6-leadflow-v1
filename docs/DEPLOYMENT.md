# Deployment Guide

LeadFlow V1 is intentionally provider-neutral. The application is a standard FastAPI service with local SQLite persistence.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Docker

Build:

```bash
docker build -t leadflow-v1 .
```

Run:

```bash
docker run --rm -p 8000:8000 -v leadflow-data:/app/data leadflow-v1
```

Then open `http://127.0.0.1:8000`.

## Hosting considerations

For a public demo, choose a platform that can run a persistent Python web service/container. SQLite is acceptable for a single-instance demo, but not the recommended persistence layer for a horizontally scaled production service.

Before production deployment:

1. Move persistence to managed Postgres.
2. Add authenticated operator access.
3. Add tenant-aware authorization if serving multiple organizations.
4. Add secrets management.
5. Add rate limiting and abuse protection.
6. Add structured logs and monitoring.
7. Define data retention/deletion rules for lead PII.
8. Add backups and recovery validation.
9. Add idempotency/retry controls before enabling real email, calendar, or CRM actions.

## Vercel note

LeadFlow is not being treated like AtlasIQ's Next.js deployment. Its backend is a persistent Python/FastAPI service, so deployment should be selected around Python service/container support and persistence requirements rather than forcing the project onto a frontend-oriented hosting pattern.
