# LeadFlow V1

**Project 6 — AI Lead Intake, Qualification, Follow-Up & Scheduling System**

LeadFlow V1 is a portfolio-grade automation project that turns an inbound lead into an explainable next action.

```text
Lead arrives
    ↓
Validate + normalize
    ↓
Deterministic qualification score (0–100)
    ↓
Route: qualified / nurture / needs-info
    ↓
Priority + next action
    ↓
Personalized follow-up draft
    ↓
Persist to SQLite
    ↓
Operator queue
```

## Why this project exists

Small businesses often lose leads between first contact and follow-up. LeadFlow demonstrates how an AI-assisted workflow can make that process repeatable without hiding business logic behind an opaque model.

The core qualification decision is deterministic and explainable. AI is intentionally treated as an optional communication layer, not the authority for lead scoring.

## V1 capabilities

- Browser-based lead intake form
- `POST /api/leads` lead creation API
- `GET /api/leads` operator queue API
- `GET /health` health endpoint
- Input validation and normalization
- Explainable 0–100 scoring
- Routing into `qualified`, `nurture`, or `needs-info`
- High / medium / low priority classification
- Next-action generation
- Personalized deterministic follow-up drafts
- SQLite persistence
- Operator dashboard
- Six focused regression tests
- GitHub Actions CI
- Architecture, evidence, and interview documentation

## Qualification model

| Dimension | Max points |
|---|---:|
| Estimated opportunity value | 30 |
| Purchase timeline | 25 |
| Budget confirmed | 15 |
| Decision-maker status | 15 |
| Lead completeness | 15 |
| **Total** | **100** |

Routing:

- Missing qualification-critical information → `needs-info`
- Score >= 70 → `qualified`
- Otherwise → `nurture`
- Score >= 85 + qualified → `human-priority-review`

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

Run tests:

```bash
pytest -q
```

## Example API request

```json
{
  "name": "Jordan Lee",
  "email": "jordan@example.com",
  "phone": "555-0100",
  "source": "website",
  "service": "Automation consulting",
  "estimated_value": 12000,
  "timeline_days": 7,
  "budget_confirmed": true,
  "decision_maker": true,
  "notes": "Needs intake and scheduling automation."
}
```

This sample scores **100/100**, routes to **qualified**, receives **high** priority, and triggers **human-priority-review**.

## Repository structure

```text
app/
  main.py          API + browser routes
  models.py        Request/response contracts
  scoring.py       Qualification engine
  followup.py      Follow-up draft generation
  storage.py       SQLite persistence
static/
  index.html       Intake + operator UI
tests/
  test_scoring.py
docs/
  ARCHITECTURE.md
  EVIDENCE_CHECKLIST.md
  INTERVIEW_TALKING_POINTS.md
  PROJECT_CHECKPOINT.md
.github/workflows/
  ci.yml
```

## Engineering decisions

**Deterministic scoring before AI.** A business-critical qualification decision should be inspectable, testable, and repeatable.

**Human escalation for high-value leads.** Automation accelerates triage; it does not remove judgment from consequential decisions.

**Local persistence for V1.** SQLite keeps the demo reproducible and inexpensive while preserving a clean migration path to Postgres or CRM storage.

**No fake production integrations.** Email delivery, CRM writes, and calendar booking are explicitly deferred until idempotency, retry, authorization, and provider-failure behavior are designed.

## V1 boundaries

Not implemented yet:

- Real outbound email/SMS delivery
- Real calendar booking
- CRM synchronization
- External-action idempotency/retry queue
- Production authentication/authorization
- Multi-tenant isolation
- Hosted deployment

Those are V2 integration concerns, not hidden behind demo buttons.

## What this project demonstrates

API design • validation • business-rule modeling • explainable automation • persistence • workflow orchestration • human-in-the-loop design • regression testing • CI • production-minded integration planning

See [Interview Talking Points](docs/INTERVIEW_TALKING_POINTS.md) for a concise technical explanation.

## License

MIT
