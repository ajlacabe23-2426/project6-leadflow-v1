"""October 31 demo gate: a single synthetic journey must survive app restarts.

No hosted services, credentials, email adapters, or real customer leads.
"""
from fastapi.testclient import TestClient

from app.main import app


LEAD = {
    "name": "Demo Operator",
    "email": "demo-operator@example.com",
    "source": "synthetic-demo",
    "service": "Example automation consultation",
    "estimated_value": 12000,
    "timeline_days": 7,
    "budget_confirmed": True,
    "decision_maker": True,
    "communication_consent": True,
    "opted_out": False,
}


def test_client_demo_survives_restart_and_respects_consent(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "meeting-demo.db"))

    with TestClient(app) as first_session:
        assert first_session.get("/health").status_code == 200
        intake = first_session.post("/api/leads", json=LEAD)
        assert intake.status_code == 201
        original = intake.json()
        assert original["qualification"]["score"] == 100
        assert original["qualification"]["routing"] == "qualified"
        assert original["qualification"]["priority"] == "high"
        assert original["qualification"]["next_action"] == "human-priority-review"
        assert original["communication_status"] == "draft-ready"

        no_consent = first_session.post("/api/leads", json={
            **LEAD,
            "name": "No Consent Example",
            "email": "no-consent@example.com",
            "communication_consent": False,
        })
        assert no_consent.status_code == 201
        assert no_consent.json()["communication_status"] == "suppressed-no-consent"

        invalid = first_session.post("/api/leads", json={**LEAD, "email": "invalid"})
        assert invalid.status_code == 422
        assert len(first_session.get("/api/leads").json()) == 2

    # New TestClient lifetime reruns app initialization against the exact same
    # disk-backed disposable database rather than reusing in-memory entries.
    with TestClient(app) as reopened:
        listed = reopened.get("/api/leads")
        assert listed.status_code == 200
        records = listed.json()
        assert len(records) == 2
        by_email = {record["lead"]["email"]: record for record in records}
        assert original["id"] == by_email["demo-operator@example.com"]["id"]
        assert by_email["no-consent@example.com"]["communication_status"] == "suppressed-no-consent"

        retry = reopened.post("/api/leads", json=LEAD)
        assert retry.status_code == 201
        assert retry.json()["id"] == original["id"]
        assert len(reopened.get("/api/leads").json()) == 2
