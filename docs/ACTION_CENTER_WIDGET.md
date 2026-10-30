# LeadFlow — Action Center + drop-in widget (candidate)

**State:** local-test implementation candidate; public customer production is NOT authorized by CI alone.

## Positioning
LeadFlow is a lightweight lead-response reliability layer for owner-led service businesses, not a replacement CRM. Low-friction users should be able to connect a tiny inquiry widget, see every required follow-up and deadline, and enable optional advanced integrations when the value is proven. The qualification and task engine work without a large language model.

## Implemented
- Action Center page: /action-center with due/overdue metrics, owner assignment, review tasks and completion controls.
- Protected operator API: GET /api/action-center returns persisted lead qualification, owner, assignment history and obligations.
- Optional automated intake workflow: enable LEADFLOW_ENABLE_AUTO_TRIAGE=1. Every accepted lead gets a queue.triage assignment and an idempotent obligation. High priority is due in 15 minutes, medium 60 minutes, low 240 minutes, derived from the persisted creation timestamp.
- No communication consent means an INTERNAL owner-review obligation only, not outbound contact.
- Public demonstration inquiry page at /widget and drop-in launcher at /embed.js. The iframe sends to the existing intake API using an idempotency key. The consent checkbox is unchecked by default.
- No email, SMS, CRM write, calendar booking or external action is executed.

## Start local (synthetic data only)

Install from requirements.txt in a Python 3.11 environment, then use a separate demo database and enable the rules:

    export LEADFLOW_DB_PATH="$PWD/data/leadflow_action_center_demo.db"
    export LEADFLOW_ENABLE_AUTO_TRIAGE=1
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

Open:
- Intake: http://127.0.0.1:8000/
- Action Center: http://127.0.0.1:8000/action-center
- Standalone widget: http://127.0.0.1:8000/widget
- Zero-config installation preview: http://127.0.0.1:8000/embed-demo

Website install example (local test HTML only):

    <script src="http://127.0.0.1:8000/embed.js" data-label="Ask for an estimate" defer></script>

Do not install a localhost snippet on a public website. Future public installation needs a reviewed HTTPS host, abuse controls, consent disclosures and proper authorization.

## Tests
1. All pytest tests pass at the exact revision.
2. New synthetic high-value lead creates one case, triage owner and first-response task.
3. Repeat of the same submission does not duplicate its task.
4. Action Center shows assigned operator, due date, task completion and persisted state after refresh.
5. No-consent lead creates only internal review and no message is sent.
6. Operator token boundary is enforced when configured; unauthorized GET /api/action-center returns 401.
7. Local widget submit creates a case; mobile and keyboard controls are visually tested in an actual browser.
8. Restart Uvicorn and confirm data persists.

## Production NO-GO
- Real operator accounts/authorization and tenant isolation.
- Hosted persistent database, migrations, backups, restore and user-data deletion.
- Public-form anti-abuse/rate limits, origin and tenant binding, verified privacy and consent terms.
- HTTPS deployment, secret management, monitoring, incident and support process.
- Real provider integrations that respect consent and reconcile uncertain delivery outcomes.
- Exact release commit, human acceptance, and a controlled real-world pilot with authorized data.

The existing token guard is a local demonstration boundary, not user identity. SQLite is not suitable for a horizontally scaled public platform. No production deployment is claimed.

## Cost model hypothesis
Offer one installable widget, deterministic rules and a single Action Center before exploring optional AI summaries, additional channels or advanced integrations. Pricing and revenue claims must be validated with prospective buyers.
