# Security Policy

LeadFlow V1 is a learning and portfolio project, not a production lead-management service.

## Current safety boundaries

- No provider API credentials are required by V1.
- Runtime SQLite databases are excluded from Git.
- No real email, SMS, calendar, or CRM side effects are enabled.
- Qualification is deterministic and does not delegate business-critical routing authority to an LLM.
- High-priority leads are escalated to a human-review action.
- Example data is synthetic.

## Before production use

A production version should add, at minimum:

- authenticated operator access
- multi-tenant authorization and data isolation
- encryption and managed database storage
- secrets management
- rate limiting and abuse protection
- PII retention/deletion policy
- audit logging
- idempotent outbound actions
- durable job queue with retry/dead-letter handling
- provider webhook verification
- dependency and container scanning
- backups and recovery testing

## Reporting

Do not submit real customer PII, credentials, tokens, or production data in a public issue. Describe the affected component and reproduction at a safe level.
