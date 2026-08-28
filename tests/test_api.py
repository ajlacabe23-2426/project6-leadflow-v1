from fastapi.testclient import TestClient

from app.main import app


SAMPLE_LEAD = {
    "name": "Jordan Lee",
    "email": "jordan@example.com",
    "phone": "555-0100",
    "source": "website",
    "service": "Automation consulting",
    "estimated_value": 12000,
    "timeline_days": 7,
    "budget_confirmed": True,
    "decision_maker": True,
    "notes": "Needs intake and scheduling automation.",
}


def test_health_endpoint(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "health.db"))
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "project6-leadflow",
    }


def test_create_and_list_lead(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "leads.db"))
    with TestClient(app) as client:
        created = client.post("/api/leads", json=SAMPLE_LEAD)
        listed = client.get("/api/leads")

    assert created.status_code == 201
    body = created.json()
    assert body["qualification"]["score"] == 100
    assert body["qualification"]["routing"] == "qualified"
    assert body["qualification"]["priority"] == "high"
    assert body["qualification"]["next_action"] == "human-priority-review"

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["lead"]["email"] == "jordan@example.com"


def test_invalid_email_fails_validation(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "invalid.db"))
    payload = {**SAMPLE_LEAD, "email": "not-an-email"}
    with TestClient(app) as client:
        response = client.post("/api/leads", json=payload)

    assert response.status_code == 422
