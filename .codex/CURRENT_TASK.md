Task ID: P6-ACTION-CENTER-WIDGET-2026-10-30
Title: Verify LeadFlow Action Center, retry-safe triage and low-friction website widget
Status: VERIFYING
Risk Tier: TIER_3
Base SHA: b41ec3f949b04dab38d9bfa8a9139e1d92b07917

## Objective
Turn lead scores into accountable internal next actions with owner, deadline, completion evidence and an embeddable inquiry form, without introducing a mandatory LLM dependency. Reuse the integrated demo operator-access boundary. Do not execute any external customer communications.

## Authorized implementation paths
- .codex/CURRENT_TASK.md
- .env.example
- app/main.py
- app/triage.py
- static/index.html
- static/action-center.html
- static/widget.html
- static/embed.js
- docs/ACTION_CENTER_WIDGET.md

## Authorized test paths
- tests/test_action_center.py

## Acceptance criteria
- Existing scoring, lifecycle, idempotency, consent, outbox and browser regression tests remain green.
- Opt-in auto-triage creates exactly one repeat-safe internal assignment and time-bound obligation for a validated lead.
- No-consent leads receive owner-review instead of automatic outreach.
- Action Center reads actual persisted owner/task state, supports assignment, review task creation, completion and reload.
- Protected Action Center API requires operator authorization when configured; public widget cannot read operator data.
- Public iframe widget posts validated intake only with an unchecked optional consent control.
- All server-side work runs without an LLM or external provider.
- GitHub exact-head CI and security monitor pass, then owner MacBook UI validation.

## Explicit non-goals
- No customer live production exposure, payment, public email/SMS, calendar booking, external CRM writes, real customer PII, hosted database migrations, secrets or automated cold outreach.
- No claim of production-ready operator identity, multitenancy, public-form bot protection or third-party integration.

## Release constraints
Pushing code to the protected main branch is distinct from public production deployment. Production NO-GO remains until tenant-aware auth, abuse controls, legal/data processing, managed storage/recovery and real-world acceptance are verified. All test cases use fictional lead data.
