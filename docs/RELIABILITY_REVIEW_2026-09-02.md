# LeadFlow intake reliability review — 2026-09-02

## Result

Implemented request-key idempotency, serialized intake persistence, full-payload
retry matching, and explicit connection cleanup. Scope follows the existing
quality-first roadmap. Outbound messages and appointments remain disabled.

## Confirmed defects

- Email/service/source matching discarded changes to notes, value, and consent.
  Reproduced on baseline: a later opt-out returned the original consenting draft.
- Duplicate lookup and insert had no shared write transaction; concurrent retries
  could both pass the lookup.
- SQLite connection context managers commit/rollback but do not close connections.
- Infinite estimated values could pass the numeric input boundary.

## Updated API contract

`POST /api/leads` accepts optional `Idempotency-Key` (1–128 ASCII letters, digits,
periods, underscores, colons, or hyphens). Reuse the same key for one logical intake.

- Same key and validated payload returns the stored record and original audit trail.
- Same key and different payload returns HTTP 409 without another write.
- A new key represents a distinct intake, even if the payload matches.
- Key retention lasts as long as the local database, beyond the 24-hour heuristic.
- Without a key, only an exact validated payload is deduplicated within 24 hours.
- Legacy fingerprints are still recognized, but their entire stored payload must match.
- Success/replay retain HTTP 201 for compatibility with the existing API.

An additive `intake_requests` table is initialized locally. The request mapping,
lead, qualification, draft and audit history commit together under `BEGIN IMMEDIATE`.
Initialization also serializes migrations; foreign-key enforcement is enabled.
No existing lead history is rewritten or removed.

## Validation

`python -m pytest -q`: 28 tests passed.
`python -m compileall -q app tests` and `git diff --check`: passed.
24 concurrent retries using 8 workers persisted exactly one record, both with and
without a key. Coverage includes conflict rollback, legacy records, changes to
consent/details, expired heuristic windows, and malformed keys.

## Remaining boundaries

This is still a local single-operator demo: API authentication, tenant isolation,
pagination, durable outbound jobs, lifecycle transitions and ownership/SLA tracking
remain unfinished. Keys are local database-wide identifiers, not credentials;
future multi-tenant use must scope them to an authenticated tenant.

Changed submissions create separate historical intake records; they do not update
all prior records for a contact. Before enabling delivery, implement a contact-level
suppression registry checked at send time so later opt-outs suppress old drafts too.
Do not treat request-level consent as global communication authorization.

## Manual check

Submit an intake twice with one key; confirm identical IDs. Change its notes while
retaining the key; expect 409. Use a new key; confirm a new record. Restart the API
using the same database and retry the original key; confirm the original record.
