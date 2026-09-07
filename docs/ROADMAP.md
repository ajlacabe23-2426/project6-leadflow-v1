# LeadFlow Quality-First Roadmap

## Direction

LeadFlow is being developed as a **lead-handling reliability engine**, not as a lightweight CRM clone and not around monetization.

The existing intake/scoring/follow-up workflow remains a useful V1 foundation, but qualification is now one subsystem inside a larger correctness problem.

## NOW — Workflow correctness

1. Define an explicit lead lifecycle state machine.
2. Reject invalid state transitions.
3. Add stable request/idempotency identifiers.
4. Replace 24-hour fingerprint dedupe as the sole duplicate-control mechanism.
5. Add ownership + assignment history.
6. Model obligations/deadlines such as response SLA and missing-info follow-up.
7. Represent contradictions and unresolved exceptions explicitly.
8. Version qualification/routing policy and store reason codes with decisions.
9. Expand tests around retries, repeated delivery, invalid transitions, and concurrent update behavior.
10. Add structured logs with correlation IDs.

## NEXT — Reliable side effects

Only after workflow correctness is proven:

- durable outbox/action queue
- email provider adapter
- calendar availability/booking adapter
- retry with bounded backoff
- dead-letter handling
- cancellation
- reconciliation after ambiguous provider failures
- external-action audit events
- provider-specific idempotency protection

## NEXT — Security boundary

Before real multi-user data:

- authenticated operators
- organization/tenant identity
- role-based authorization
- deny-by-default access rules
- cross-tenant negative tests
- managed Postgres
- encrypted secrets
- retention/deletion rules
- rate limits and abuse protection

## LATER — Intelligence

Intelligence should help detect operational failure, not merely generate copy:

- stalled lead detection
- missed-SLA detection
- contradictory evidence detection
- incomplete-handoff detection
- repeated retry/failure patterns
- policy effectiveness analysis
- optional natural-language synthesis of verified case facts

## DELETE / DE-EMPHASIZE

- feature-count competition with established CRMs
- generic dashboard expansion
- arbitrary additions to the 0–100 score
- AI-generated outreach as the primary differentiator
- random integrations without a lifecycle requirement
- monetization-driven scope decisions

## Definition of a strong Project 6

A strong Project 6 can replay a lead case from evidence and audit events, explain why each decision occurred, survive retries and provider failures without corrupting state, enforce authorization boundaries, and surface cases that are falling through the cracks.
