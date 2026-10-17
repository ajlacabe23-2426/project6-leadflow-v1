# October 31 commercial demo — LeadFlow V1

**Status:** rehearsal plan, not production certification. **Candidate dependency:** [integration PR #24](https://github.com/ajlacabe23-2426/project6-leadflow-v1/pull/24) at `0be9169d58aa237acd6b2f76c6dae7ae6da0885e`; this document is on a **stacked, unmerged** branch and must be reverified at its final SHA.

## Buyer promise

“LeadFlow explains why an inquiry needs attention and helps an operator prioritize follow-up.”

In scope for demo: synthetic intake, deterministic qualification, priority, human review, operator queue, persisted records, consent suppression and repeat-safe writes. **Not in scope:** authenticated production console, multiple customer organizations, actual email/SMS, calendar bookings, CRM sync, or a public/customer-data deployment. Do not imply that a suggested draft was sent.

## Rehearsal, approximately 4 minutes

1. **Health / isolated environment:** start the service in an owner-approved local or restricted environment with an empty synthetic database; ensure it is not publicly exposed.
2. **New synthetic lead:** submit a made-up, high-value lead with confirmed budget and decision-maker status. Narrate the explicit scoring and human priority; show the queue entry.
3. **Persistence:** refresh the queue and restart the service; the same test lead should remain visible. Never claim persistence solely because an on-screen row survived a page refresh.
4. **Safety:** submit an invalid email and show validation. Submit an explicitly non-consenting second synthetic lead and show the suppressed communication state.
5. **Retry safety:** submit an identical lead, show existing identity and no duplicate queue item. Mention that outbound provider adapters remain deliberately disconnected.
6. **Business discovery:** ask how the prospect currently captures inbound inquiries, loses handoffs, handles consent, and measures speed-to-first-human-response.

## Exact no-device evidence gate

Run `python -m pytest -q tests/test_meeting_acceptance.py` on this candidate. This synthetic TestClient check specifically exercises first session → app lifespan shutdown/reopen → persisted record → idempotent retry and suppressed-consent state. CI on this branch must be green at the final commit SHA; a passing ancestor does not count.

## Meeting-ready decision

- [ ] Exact head and required CI success recorded
- [ ] Human has checked the actual screen, keyboard, mobile layout and meeting-device access
- [ ] Two synthetic examples, no real personal data or outbound side effects
- [ ] Operator queue never exposed without appropriate access controls
- [ ] Demo restart/persistence and duplicate/invalid/consent flows demonstrated
- [ ] Distinguish a private demonstration from a production customer trial
- [ ] One-page scope and prospective-customer discovery questions reviewed
- [ ] Live failure fallback: redacted pre-recorded demo with exact build/version

**Hard stop for live pilot:** operator authentication, tenant isolation where needed, secure managed storage/backup/restore, access and privacy policy, monitoring, and any side-effect provider design all require evidence and separate approval. Neither this script nor a green CI run authorizes deployment or merges.
