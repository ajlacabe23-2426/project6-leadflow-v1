# LeadFlow Roadmap

## V1 — Core workflow

Status: implemented.

- structured intake
- validation and normalization
- explainable qualification
- routing and priority
- next-action selection
- follow-up drafting
- SQLite persistence
- operator queue
- automated tests and CI

## V1.1 — Reliability

- request id / correlation id
- duplicate-submission detection — implemented with a 24-hour normalized identity window
- consent and opt-out communication controls — implemented
- explicit scheduling state — implemented
- per-lead decision/action audit history — implemented
- pagination and filtering
- structured application logging
- API-level test expansion
- accessibility/browser evidence

## V2 — External actions

Only after reliability controls exist:

- outbound email adapter
- calendar availability adapter
- appointment booking
- CRM adapter
- durable task queue
- idempotency keys
- retry / dead-letter policy
- external-action audit trail

## V3 — Multi-tenant productization

- operator authentication
- organization/tenant model
- role-based authorization
- managed Postgres
- encrypted configuration
- retention/deletion controls
- tenant analytics
- deployment and observability

## AI boundary

AI may assist with communication personalization, summarization, or extracting structured intent from free text. Deterministic policy remains the authority for scoring and routing unless an explicitly reviewed product decision changes that boundary.
