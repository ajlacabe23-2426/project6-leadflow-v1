# Security Policy

LeadFlow V1 is a learning and portfolio project, not a production lead-management service.

## Reporting a vulnerability

Do not publish credentials, customer PII, exploit payloads, provider tokens, database contents, or other sensitive evidence in a public issue. If GitHub private vulnerability reporting is available, use it; otherwise contact the repository owner privately with the minimum non-destructive reproduction information needed.

## Current safety boundaries

- No provider API credentials are required by V1.
- Runtime SQLite databases and local environment files are excluded from Git.
- No real email, SMS, calendar, or CRM side effects are enabled on main.
- Qualification is deterministic and does not delegate business-critical routing authority to an LLM.
- High-priority leads remain human-review actions.
- Example data is synthetic.
- CI and the scheduled security monitor scan reachable Git history, repository workflow posture, and Python dependency advisories.

## Before production use

A production version still requires authenticated operator access, multi-tenant authorization and data isolation, managed persistence and backups, network-level rate limiting/abuse protection, PII retention/deletion controls, audit logging, idempotent outbound actions, durable retry/dead-letter handling, provider webhook verification, and recovery testing.

Security testing does not authorize access to systems or data you do not own.
