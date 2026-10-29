# Operator API access boundary (review candidate, 2026-10-29)

LeadFlow remains a **local synthetic-data demo**, not production customer software. This first-stage protection adds an operator-token boundary around private API routes so private lead details cannot be accessed anonymously **when the guard is configured**. It is NOT real human identity, tenant isolation, a permission system, or a substitute for a managed auth provider.

## Endpoint policy

- `POST /api/leads`: public intake, unchanged. Anyone who can reach the server can submit a lead and receive their own intake response. **Rate limiting and abuse prevention are still required** before public exposure.
- `GET /health`, `GET /`: public, intentionally contain no persisted lead data.
- **Every other `/api/` route**: protected by `Authorization: Bearer <token>` whenever `LEADFLOW_OPERATOR_TOKEN` is set or `LEADFLOW_REQUIRE_OPERATOR_AUTH` is truthy. This includes queue reads, state changes, assignments, obligations, and outbox operations.
- If access is configured but the token is missing, incorrect, or uses the wrong authentication scheme, operator APIs respond with HTTP **401**.
- If authentication is required but the token is absent or shorter than 32 UTF-8 bytes, operator APIs fail closed with HTTP **503**. Never silently switch to anonymous access.
- API responses set `Cache-Control: no-store` to discourage caching sensitive lead records.

## Local rehearsal

Set a strong randomly generated token **outside the repository**. Examples:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
export LEADFLOW_REQUIRE_OPERATOR_AUTH=1
export LEADFLOW_OPERATOR_TOKEN='<paste generated value locally>'
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
$env:LEADFLOW_REQUIRE_OPERATOR_AUTH = "1"
$env:LEADFLOW_OPERATOR_TOKEN = "<paste generated random token locally>"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open the local page and enter the token into the **Operator access token** input, then click **Refresh**. The secret is used only in the HTTPS/loopback API request's Authorization header and kept in memory in that page; it is **not** stored in the URL, localStorage, or sessionStorage. Reloading the page requires entering it again. Do not capture credentials in demo videos or browser screenshots.

Before using Docker, pass the secret in using a properly restricted environment/secrets mechanism, never a committed file or pasted public command history. Bind Docker to `127.0.0.1:8000:8000`, not all interfaces.

## Development compatibility

Without either environment setting, the existing local demo works as before and is **unauthenticated**. Use only synthetic data in that mode. `LEADFLOW_REQUIRE_OPERATOR_AUTH=1` should be explicitly set when rehearsing the protected operator path. The token must be at least 32 UTF-8 bytes.

## Still blocking customer launch

1. A real identity provider and durable operator sessions, roles and organization-scoped authorization; bearer token here is **one shared secret**, not per-user access control.
2. Public intake abuse throttling, bot defenses and any relevant consent/legal review.
3. Managed tenant-aware storage, backups, retention/deletion and recovery drills.
4. TLS and proper secret management, security logs/monitoring, permissioned data access and logout/revocation.
5. Per-customer onboarding and audited provider integration for send/booking/CRM actions, with idempotency and provider error handling.

Do not expose this preview publicly or accept real lead PII based solely on this guard. Run the tests and browser verification at the exact candidate SHA before presenting this as a completed improvement.

## Staging/production fail-closed mode

Setting `LEADFLOW_ENV=staging` or `LEADFLOW_ENV=production` implicitly requires a configured strong operator token even if `LEADFLOW_REQUIRE_OPERATOR_AUTH` is omitted or false. Misconfiguration blocks private endpoints with 503, never falls back to anonymous operator access. This **does not** make the app safe for external customers: public intake still needs abuse controls, real user identity/authorization, tenant isolation and privacy safeguards.
