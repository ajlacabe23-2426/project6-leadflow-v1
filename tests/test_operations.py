from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app


LEAD = {
    "name": "Jordan Lee",
    "email": "jordan@example.com",
    "service": "Automation consulting",
    "estimated_value": 12000,
    "timeline_days": 7,
    "budget_confirmed": True,
    "decision_maker": True,
    "communication_consent": True,
}


def test_assignment_history_is_append_only(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "assignment.db"))
    with TestClient(app) as client:
        lead_id = client.post("/api/leads", json=LEAD).json()["id"]
        first = client.post(
            f"/api/leads/{lead_id}/assignments",
            json={
                "owner_ref": "queue.sales",
                "reason_code": "intake-routing",
                "correlation_id": "assign-1",
            },
        )
        second = client.post(
            f"/api/leads/{lead_id}/assignments",
            json={
                "owner_ref": "operator.aj",
                "reason_code": "operator-reassignment",
                "correlation_id": "assign-2",
            },
        )
        history = client.get(f"/api/leads/{lead_id}/assignments")

    assert first.status_code == 201
    assert second.status_code == 201
    assert [item["owner_ref"] for item in history.json()] == ["queue.sales", "operator.aj"]
    assert [item["correlation_id"] for item in history.json()] == ["assign-1", "assign-2"]


def test_overdue_obligation_is_visible_until_completed(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "obligations.db"))
    now = datetime.now(timezone.utc)
    with TestClient(app) as client:
        lead_id = client.post("/api/leads", json=LEAD).json()["id"]
        overdue = client.post(
            f"/api/leads/{lead_id}/obligations",
            json={
                "obligation_type": "first-response",
                "due_at": (now - timedelta(minutes=5)).isoformat(),
                "reason_code": "sla.first-response",
                "correlation_id": "sla-1",
            },
        )
        future = client.post(
            f"/api/leads/{lead_id}/obligations",
            json={
                "obligation_type": "owner-review",
                "due_at": (now + timedelta(hours=1)).isoformat(),
                "reason_code": "review.window",
                "correlation_id": "sla-2",
            },
        )
        before = client.get("/api/obligations/overdue")
        completed = client.patch(
            f"/api/obligations/{overdue.json()['id']}/complete"
        )
        after = client.get("/api/obligations/overdue")

    assert overdue.status_code == 201
    assert future.status_code == 201
    assert [item["id"] for item in before.json()] == [overdue.json()["id"]]
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert after.json() == []


def test_operations_reject_unknown_lead(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "missing.db"))
    with TestClient(app) as client:
        response = client.post(
            "/api/leads/999/assignments",
            json={"owner_ref": "operator.aj", "reason_code": "specialist-review"},
        )
    assert response.status_code == 404
