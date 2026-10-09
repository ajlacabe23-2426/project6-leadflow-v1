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


def test_assignments_replay_same_explicit_correlation_without_duplicate(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "assignment-idempotency.db"))
    payload={
        "owner_ref": "operator.aj",
        "reason_code": "operator-reassignment",
        "correlation_id": "assignment-delivery-001",
    }
    with TestClient(app) as client:
        lead_id=client.post("/api/leads", json=LEAD).json()["id"]
        first=client.post(f"/api/leads/{lead_id}/assignments", json=payload)
        retry=client.post(f"/api/leads/{lead_id}/assignments", json=payload)
        rejected=client.post(
            f"/api/leads/{lead_id}/assignments",
            json={**payload, "owner_ref": "operator.other"},
        )
        history=client.get(f"/api/leads/{lead_id}/assignments")
        # Different explicit correlation IDs remain distinct reassignment events.
        next_assignment=client.post(
            f"/api/leads/{lead_id}/assignments",
            json={**payload,"correlation_id":"assignment-delivery-002"},
        )

    assert first.status_code==201
    assert retry.status_code==201
    assert retry.json()==first.json()
    assert rejected.status_code==409
    assert [item["id"] for item in history.json()]==[first.json()["id"]]
    assert next_assignment.status_code==201
    assert next_assignment.json()["id"]!=first.json()["id"]


def test_obligation_retries_are_idempotent_and_conflicting_payloads_rejected(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "obligation-idempotency.db"))
    due_at = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    payload = {
        "obligation_type": "first-response",
        "due_at": due_at.isoformat(),
        "reason_code": "sla.first-response",
        "correlation_id": "sla-delivery-001",
    }

    with TestClient(app) as client:
        lead_id = client.post("/api/leads", json=LEAD).json()["id"]
        path = f"/api/leads/{lead_id}/obligations"
        first = client.post(path, json=payload)
        retry = client.post(path, json={
            **payload,
            "due_at": due_at.astimezone(timezone(timedelta(hours=-5))).isoformat(),
        })
        conflict = client.post(path, json={
            **payload,
            "due_at": (due_at + timedelta(minutes=1)).isoformat(),
        })
        different_key = client.post(path, json={
            **payload, "correlation_id": "sla-delivery-002",
        })
        # Omitting the replay key preserves intentionally distinct legacy writes.
        legacy_one = client.post(path, json={key: val for key, val in payload.items()
                                             if key != "correlation_id"})
        legacy_two = client.post(path, json={key: val for key, val in payload.items()
                                             if key != "correlation_id"})
        history = client.get(path)

    assert first.status_code == 201
    assert retry.status_code == 201
    assert retry.json() == first.json()
    assert conflict.status_code == 409
    assert different_key.status_code == 201
    assert legacy_one.status_code == 201
    assert legacy_two.status_code == 201
    assert len(history.json()) == 4
    assert len({entry["id"] for entry in history.json()}) == 4

def test_cancel_obligation_is_idempotent_and_removes_overdue_work(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "cancel.db"))
    with TestClient(app) as client:
        lead_id = client.post("/api/leads", json=LEAD).json()["id"]
        created = client.post(
            f"/api/leads/{lead_id}/obligations",
            json={
                "obligation_type": "owner-review",
                "due_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "reason_code": "review.expired",
            },
        )
        obligation_id = created.json()["id"]
        assert any(
            row["id"] == obligation_id
            for row in client.get("/api/obligations/overdue").json()
        )
        first = client.patch(f"/api/obligations/{obligation_id}/cancel")
        retry = client.patch(f"/api/obligations/{obligation_id}/cancel")
        overdue = client.get("/api/obligations/overdue")
        history = client.get(f"/api/leads/{lead_id}/obligations")

    assert first.status_code == 200
    assert first.json()["status"] == "cancelled"
    assert retry.status_code == 200
    assert retry.json() == first.json()
    assert overdue.status_code == 200
    assert obligation_id not in [row["id"] for row in overdue.json()]
    assert history.json()[0]["status"] == "cancelled"


def test_cancel_obligation_rejects_completed_and_missing_records(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "cancel-completed.db"))
    with TestClient(app) as client:
        lead_id = client.post("/api/leads", json=LEAD).json()["id"]
        created = client.post(
            f"/api/leads/{lead_id}/obligations",
            json={
                "obligation_type": "first-response",
                "due_at": datetime.now(timezone.utc).isoformat(),
                "reason_code": "sla.response",
            },
        )
        obligation_id = created.json()["id"]
        completed = client.patch(f"/api/obligations/{obligation_id}/complete")
        cancelled = client.patch(f"/api/obligations/{obligation_id}/cancel")
        missing = client.patch("/api/obligations/999999/cancel")
        history = client.get(f"/api/leads/{lead_id}/obligations")

    assert completed.status_code == 200
    assert cancelled.status_code == 409
    assert missing.status_code == 404
    assert history.json()[0]["status"] == "completed"


def test_cancelled_obligation_replay_keeps_one_historical_record(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "cancel-replay.db"))
    payload = {
        "obligation_type": "first-response",
        "due_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        "reason_code": "sla.first-response",
        "correlation_id": "delivery-cancelled-001",
    }
    with TestClient(app) as client:
        lead_id = client.post("/api/leads", json=LEAD).json()["id"]
        path = f"/api/leads/{lead_id}/obligations"
        created = client.post(path, json=payload)
        cancelled = client.patch(f"/api/obligations/{created.json()['id']}/cancel")
        replay = client.post(path, json=payload)
        history = client.get(path)
        overdue = client.get("/api/obligations/overdue")

    assert created.status_code == 201
    assert cancelled.status_code == 200
    assert replay.status_code == 201
    assert replay.json() == cancelled.json()
    assert len(history.json()) == 1
    assert history.json()[0]["status"] == "cancelled"
    assert overdue.json() == []
