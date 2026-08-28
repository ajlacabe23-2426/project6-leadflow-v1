# Interview Talking Points

## 30-second explanation

"I built LeadFlow V1 to model a real business automation workflow rather than a chatbot demo. A lead comes in through a FastAPI endpoint or browser form, gets validated, receives an explainable deterministic 0–100 qualification score, is routed into qualified, nurture, or needs-info, gets a next action and personalized follow-up draft, and is persisted to SQLite for an operator queue. I kept the scoring deterministic so a model cannot silently change business-critical decisions."

## What I learned

### API design
I separated request validation from business logic and persistence so each layer can evolve independently.

### Explainable automation
The score is a sum of visible dimensions instead of an opaque AI judgment. That makes it easier to test, tune, and defend.

### Human-in-the-loop design
A high-value qualified lead is escalated to human priority review instead of triggering an irreversible external action.

### Persistence
The project uses SQLite for a reproducible V1 while keeping persistence behind a module that can later move to Postgres or a CRM.

### Production thinking
I deliberately did not fake email, calendar, or CRM integrations. Before those are enabled I would add idempotency, retries, provider authentication, audit logging, and failure recovery.

## Likely technical questions

**Why not let AI score the lead?**  
Because qualification is business-critical and should be deterministic, inspectable, and regression-testable. AI can help draft communications without controlling the score.

**How would you scale it?**  
Move persistence to Postgres, add tenant-aware auth, queue outbound work, use idempotency keys, add provider adapters, and separate API/web workers from asynchronous jobs.

**How would you prevent duplicate emails or appointments?**  
Persist an idempotency key per intended external action, enforce uniqueness, and make workers retry-safe.

**What would you monitor?**  
Lead intake volume, validation failures, routing distribution, queue age, outbound failure rate, retry count, scheduling conflicts, provider latency, and human overrides.

**What security issues matter?**  
PII minimization, authorization, tenant isolation, provider-secret handling, rate limiting, audit logs, retention policy, and avoiding sensitive data in application logs.
