# LeadFlow — consent-safe delivery adapter candidate (2026-10-29)

**Status: sandbox adapter contract, not a live email service.** No provider credentials, SMTP, network transport or automatic worker is included. Nothing sends to real recipients from this PR.

## Safety invariants

- Without both a supplied transport object and `LEADFLOW_DELIVERY_MODE=sandbox`, `dispatch_one_email()` returns `disabled` **without claiming an outbox action**.
- Only `follow-up-email` actions are claimed. The existing `schedule-discovery` queue stays untouched.
- After claiming an action, the worker re-reads the persisted lead **before each attempt** and fails permanently when consent is false, the customer is opted out, the communication status is suppressed, the lead is closed/suppressed, or the draft is empty.
- Transport receives `idempotency_key=action.action_key`; real providers must honor/reconcile that key to avoid double delivery.
- Only explicit, confirmed `accepted` outcomes become the outbox status `succeeded` and worker report `accepted`. **Provider acceptance is not inbox delivery.** A definite pre-acceptance rate limit/unavailability may retry with existing bounded backoff; ambiguous transport errors are permanently quarantined for manual review because acceptance may have occurred.
- The worker returns action id and bounded error codes, never the recipient's email address, message body, API token, raw exception or provider authentication details.
- The worker processes one action on explicit invocation. No background scheduler, process manager or public dispatch endpoint is added.

## Safe local tests

```bash
python -m pytest -q tests/test_email_delivery.py tests/test_outbox.py
```

Use only an injected deterministic fake in this branch. The existing public operator API is still local-demo only; this delivery adapter PR does **not** silently merge the separate operator-auth candidate PR #35.

## Remaining service implementation

1. Reconcile operator-auth PR #35 with durable per-user auth, tenant authorization, rate limiting and PII deletion before any public data flow.
2. Select an authorized communication provider and design signed webhook verification, verified sender identity, bounce/complaint and unsubscribe processing, consent evidence, fraud/abuse controls, quotas, opt-out updates and monitored secret storage.
3. Implement a provider-specific adapter with a documented, tested **idempotent** send protocol; do not claim at-most-once behavior when the provider cannot guarantee it.
4. Resolve in-progress actions after worker crashes through manual provider reconciliation; never blindly replay ambiguous sends.
5. Run permissioned sandbox integration tests, then separately approved restricted pilot on a production-like datastore with backups, monitored side effects and retention/consent review.
6. Define pricing/usage controls and a real customer support process before billing.

The current repository should not be publicly hosted or ingest real customer data. Do not infer revenue readiness from synthetic tests alone.
