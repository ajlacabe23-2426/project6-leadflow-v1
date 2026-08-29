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
- **Twelve regression tests** across scoring, API behavior, consent, and deduplication
- GitHub Actions CI
- Docker packaging
- Demo smoke-test script
- Architecture, security, deployment, API, roadmap, evidence, and interview documentation

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
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

Run verification:

```bash
python -m compileall -q app tests scripts
python -m pip check
python -m pytest -q
python -m scripts.demo
```

## Docker

```bash
docker build -t leadflow-v1 .
docker run --rm -p 8000:8000 -v leadflow-data:/app/data leadflow-v1
```

Then open `http://127.0.0.1:8000`.

## Example high-priority lead

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
  "notes": "Needs intake and scheduling automation.",
  "communication_consent": true,
  "opted_out": false
}
```

This sample scores **100/100**, routes to **qualified**, receives **high** priority, and triggers **human-priority-review**.

## Repository structure

```text
app/
  main.py
  models.py
  scoring.py
  followup.py
  storage.py
static/
  index.html
scripts/
  demo.py
tests/
  test_scoring.py
  test_api.py
docs/
  ARCHITECTURE.md
  API_EXAMPLES.md
  DEVELOPMENT.md
  DEPLOYMENT.md
  EVIDENCE_CHECKLIST.md
  INTERVIEW_TALKING_POINTS.md
  PROJECT_CHECKPOINT.md
  RELEASE_CHECKLIST.md
  RESUME_BULLETS.md
  ROADMAP.md
.github/
  ISSUE_TEMPLATE/
  pull_request_template.md
  workflows/ci.yml
Dockerfile
SECURITY.md
```

## Engineering decisions

**Deterministic scoring before AI.** A business-critical qualification decision should be inspectable, testable, and repeatable.

**Human escalation for high-value leads.** Automation accelerates triage; it does not remove judgment from consequential decisions.

**Local persistence for V1.** SQLite keeps the demo reproducible while preserving a clean migration path to managed Postgres or CRM storage.

**No fake production integrations.** Email delivery, CRM writes, and calendar booking are explicitly deferred until idempotency, retry, authorization, and provider-failure behavior are designed.

## Verified V1 behavior

The application and regression suite have verified:

- **12/12 tests pass**
- health endpoint → HTTP 200
- sample lead creation → HTTP 201
- sample lead → **100/100 / qualified / high / human-priority-review**
- persisted lead appears in operator queue
- invalid email → HTTP 422
- duplicate submission within 24 hours → existing record returned; no duplicate stored
- consent/opt-out conflict → HTTP 422
- no-consent lead → follow-up retained as a draft but communication suppressed
- scheduling and communication states recorded explicitly
- four-event audit history stored with each new lead
- latest GitHub Actions repair run → **green**

The hardening workflow additionally checks Python compilation, dependency consistency, the demo path, and Docker image construction.

## V1 boundaries

Not implemented yet:

- Real outbound email/SMS delivery
- Real calendar booking
- CRM synchronization
- External-action idempotency/retry queue
- Production authentication/authorization
- Multi-tenant isolation
- Managed production persistence
- Hosted public deployment
- Operator authentication around the queue and audit records

Those are V2 concerns, not hidden behind demo buttons.

## Documentation shortcuts

- [Architecture](docs/ARCHITECTURE.md)
- [API examples](docs/API_EXAMPLES.md)
- [Development guide](docs/DEVELOPMENT.md)
- [Deployment guide](docs/DEPLOYMENT.md)
- [Security policy](SECURITY.md)
- [Roadmap](docs/ROADMAP.md)
- [Evidence checklist](docs/EVIDENCE_CHECKLIST.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)
- [Interview talking points](docs/INTERVIEW_TALKING_POINTS.md)
- [Resume bullets](docs/RESUME_BULLETS.md)

## What this project demonstrates

API design • validation • business-rule modeling • explainable automation • persistence • workflow orchestration • human-in-the-loop design • regression testing • CI • Docker • security boundaries • production-minded integration planning

## License

MIT
