# Project 6 — LeadFlow — Agent instructions

## Operating contract

Mission: Explainable lead workflow with deterministic qualification, reliable state transitions, outbox and operator review.

Read `README.md`, existing task and roadmap records, relevant PRs/commits and workflow configuration before edits. Preserve existing behavior and task ownership. A clear assignment authorizes scoped, reversible branch work, including implementation, tests, review, commits, pushes and draft PRs. Do not invent activity just to keep a branch busy.

## Strict stop boundaries

Do NOT merge into `main`, production-deploy, apply hosted data migrations, mutate hosted data or credentials, enable paid services, spend money, communicate with real customers, publish publicly, live-trade, delete hosted resources, or rewrite shared history without explicit action-specific human approval. A task's general autonomy instruction does not waive these stops.

## Product boundary

Preserve consent and explicit no-send semantics. Do not send customer email/SMS, write to CRM, create real bookings, or perform external lead actions without separate approval and provider/identity safeguards. Keep SQLite/demo state isolated and synthetic by default. Never claim scoring predicts conversions.

## One task, one candidate

Use `.codex/CURRENT_TASK.md` when an active task exists; otherwise read `docs/ROADMAP.md` and open issues to choose a bounded task. An active task records ID, objective, scope, tier, base SHA, acceptance criteria, non-goals and required gates. Do not overwrite another task in VERIFYING or READY_FOR_AJ. Record historical evidence in PRs/issues or `.codex/completed/`.

State machine: `NO_ACTIVE_TASK -> ACTIVE -> IMPLEMENTING -> VERIFYING -> CORRECTIONS_REQUIRED -> IMPLEMENTING -> VERIFYING -> READY_FOR_AJ -> COMPLETE`. Only the owner accepts COMPLETE. Freeze an exact commit SHA; every PASS must describe checks on that same candidate, or identify an older/stale result. A post-freeze edit invalidates affected gates. Never call an unrun check a PASS.

## Risk / verification

TIER_0: non-runtime docs; TIER_1: ordinary product UI/logic; TIER_2: user/API/persistence/provider/financial calculations; TIER_3: authorization, migration, privacy/data plane. Escalate based on real changes. Reviewer + focused checks for all tiers; security/integration for TIER_2+; ownership/negative tests, rollback and recovery assessment for TIER_3. Add UX or performance gates where relevant.

Project gates: Run automated scoring/API and retry/deduplication tests, invalid transition and concurrency negative tests, consent/no-send checks, secret/dependency review, and CI. Do not call a lead workflow complete without persisted state and replay verification.

## Review packet

Return objective, changed paths, branch, full candidate SHA, PR link, executed checks with PASS/FAIL/NOT_RUN and exact revisions, residual risks, unverified behavior, manual acceptance checklist, and the smallest explicitly authorized action requested of the owner.
