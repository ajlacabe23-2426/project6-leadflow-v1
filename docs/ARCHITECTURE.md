# LeadFlow V1 Architecture

## Objective

Convert an inbound lead into a stored, explainable qualification result and next action with minimal hidden behavior.

## Request path

```text
Browser / API client
        |
        v
FastAPI request validation
        |
        v
LeadCreate normalized contract
        |
        +--> deterministic qualification engine
        |       +--> score
        |       +--> route
        |       +--> priority
        |       +--> next action
        |
        +--> follow-up generator
        |
        v
SQLite persistence
        |
        v
LeadRecord returned to caller
        |
        v
Operator queue
```

## Boundaries

### Qualification authority
`app/scoring.py` is the authority for V1 qualification. The result is deterministic and independently testable. Communication generation cannot change the score or route.

### Persistence
SQLite is intentionally local for V1. The storage layer is isolated in `app/storage.py` so the backing store can later be replaced with Postgres or a CRM adapter.

### Human-in-the-loop
High-priority qualified leads route to `human-priority-review`. The system accelerates triage but does not autonomously approve contracts, pricing, or external commitments.

## V2 integration risks to solve before real external actions

1. Idempotency keys for repeated form submissions and webhook retries.
2. Durable outbound-action queue.
3. Retry policy and dead-letter handling.
4. Provider authentication and secret management.
5. Calendar conflict handling and timezone normalization.
6. CRM object reconciliation.
7. Multi-tenant authorization.
8. Audit log for external actions.
9. Rate limits and abuse controls.
10. Human override and cancellation.

## Security posture of V1

- No API credentials required.
- No production customer data is bundled.
- No outbound side effects.
- No hidden AI authority over qualification.
- SQLite database is runtime-generated and gitignored.
