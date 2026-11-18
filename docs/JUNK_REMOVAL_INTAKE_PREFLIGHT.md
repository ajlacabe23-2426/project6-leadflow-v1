# Junk-removal intake precheck — pilot proposal

**Scope:** Project 6 only, isolated from Project 8 and any production customer intake. This change adds a reusable, side-effect-free precheck; it does not expose an API route, connect databases, send messages, or book/dispatch jobs.

## Why

Junk-removal jobs require details absent from generic consulting leads. Automatically calling a lead "qualified" cannot authorize waste handling, establish disposal rights, promise a final quote, or dispatch a vehicle.

## Input and decisions

The precheck accepts an item description, broad service area, approximate load size, access details, customer attestation of authority to remove the items, and a conservative flag for potentially regulated/uncertain contents.

- **specialist-review**: possible regulated or unknown eligibility requires an informed human assessment before proceeding.
- **information-needed**: missing service area, access, load estimate, classification, or authority to remove.
- **manual-estimate**: initial details are complete but a human must still verify lawful disposal availability, service boundaries, capacity, price and schedule.

All outcomes carry `dispatch_allowed = false` and `quote_finalized = false`. Do not infer that ordinary household items are necessarily permitted for a specific municipal route or disposal provider.

## Acceptance criteria before integration

1. Run `python -m pytest -q tests/test_junk_removal.py` and all existing tests.
2. Reconcile field names and semantics with Project 8's pending junk-removal intake PR rather than introducing two incompatible models.
3. Obtain business-specific operational rules, disposal vendor acceptance, insurer restrictions, vehicle/load limitations and local licensing.
4. Define PII minimization, retention, consent, idempotency and business-owner review; do not expose unauthenticated write routes.
5. Design a human estimate approval and audit trail. No automatic scheduling, outbound message, payment capture or dispatch.
6. Complete separate workspace/tenant boundary tests before deploying any combined Project 6+8 service.

**Not verified by this PR:** a runnable deployed unified product, real customer data, regulatory acceptance, insurance, or integrated tests with Project 8.
