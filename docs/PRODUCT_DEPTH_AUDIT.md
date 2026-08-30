# Project 6 — Product Depth Audit

## Quality-first standard

Project 6 is no longer optimized around monetization, feature count, or copying CRM functionality. The goal is to build the strongest lead-handling system we can, with emphasis on correctness, reliability, security, explainability, and operational usefulness.

## Audit conclusion

The current foundation is technically disciplined but the core product behavior is still generic.

### Commodity / copied patterns

- web lead capture
- fixed 0–100 lead score
- qualified / nurture / needs-info routing
- follow-up drafting
- scheduling handoff
- CRM-style queue
- simple dashboard behavior

These are useful building blocks, but established CRMs and revenue-operations products already perform them at much greater scale.

### Actual technical difficulty

The hard problem is not scoring a form. It is preserving a correct, auditable lead lifecycle while data arrives late, twice, out of order, from multiple channels, under authorization and consent constraints, while external systems fail.

The difficult system problems are:

1. identity resolution without incorrectly merging different people
2. idempotency across webhook retries and repeated submissions
3. lifecycle state correctness and forbidden transitions
4. ownership and SLA tracking
5. missing/contradictory information
6. consent and communication-policy enforcement
7. external action reliability, retry, cancellation, and reconciliation
8. tenant isolation and role authorization
9. evidence-based explanation of every automated decision
10. detecting leads that are being operationally lost even when the CRM record exists

## Product pivot: Lead Handling Reliability Engine

Project 6 should become a system that answers:

**Is every lead being handled correctly, by the right person, within the right time window, with a complete and trustworthy record—and can we prove it?**

Qualification remains one module, not the product center.

## New core model

LeadFlow should evolve toward these first-class concepts:

- LeadIdentity — normalized identities plus source-specific identifiers
- LeadCase — canonical lifecycle record
- Evidence — source and timestamp for facts used in a decision
- PolicyDecision — rule/version/reason codes used to route a case
- WorkflowState — explicit lifecycle state
- Ownership — responsible operator/team and assignment history
- Obligation — something that must happen by a deadline
- ActionAttempt — requested external side effect
- ActionResult — provider response and reconciliation state
- AuditEvent — immutable event history
- Exception — contradiction, failure, stale case, or unresolved risk

## Quality gates

A future production-like version is not considered strong merely because its happy path works. It should prove:

- duplicate delivery does not create duplicate side effects
- invalid state transitions are rejected
- stale or contradictory facts are surfaced
- concurrent updates do not silently overwrite each other
- unauthorized users cannot read or mutate another tenant's cases
- opted-out contacts cannot be sent automated outreach
- provider timeouts cannot produce unknown duplicate sends/bookings
- every decision cites policy version + evidence
- every external action can be reconciled
- abandoned/stalled lead cases are detectable

## What to stop optimizing

- number of integrations
- number of dashboard cards
- generic AI copy generation
- arbitrary scoring sophistication
- feature parity with HubSpot/Salesforce-style CRMs
- premature customer-acquisition work

## What makes this project worth building

The durable learning value is in distributed workflow correctness, state machines, event history, idempotency, authorization, data integrity, observability, policy design, and failure recovery.

That is the new center of Project 6.
