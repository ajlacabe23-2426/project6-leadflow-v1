from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.models import OutboundActionRequest, OutboundActionResultRequest
from app.outbox import (
    claim_next_outbound_action,
    enqueue_outbound_action,
    record_outbound_result,
)


QUALIFIED = {
    "name": "Jordan Lee",
    "email": "jordan@example.com",
    "service": "Automation consulting",
    "estimated_value": 12000,
    "timeline_days": 7,
    "budget_confirmed": True,
    "decision_maker": True,
    "communication_consent": True,
}


def test_outbox_queue_is_idempotent_and_never_sends(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "outbox.db"))
    with TestClient(app) as client:
        lead = client.post("/api/leads", json=QUALIFIED).json()
        request = {"action_key": "followup-1", "action_type": "follow-up-email", "max_attempts": 3}
        first = client.post(f"/api/leads/{lead['id']}/actions", json=request)
        replay = client.post(f"/api/leads/{lead['id']}/actions", json=request)
        listing = client.get("/api/outbox")

    assert first.status_code == replay.status_code == 201
    assert first.json() == replay.json()
    assert first.json()["status"] == "queued"
    assert first.json()["attempts"] == 0
    assert listing.json() == [first.json()]


def test_no_consent_blocks_followup_queue(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "consent.db"))
    with TestClient(app) as client:
        lead = client.post(
            "/api/leads",
            json={**QUALIFIED, "email": "no-consent@example.com", "communication_consent": False},
        ).json()
        response = client.post(
            f"/api/leads/{lead['id']}/actions",
            json={"action_key": "blocked-1", "action_type": "follow-up-email"},
        )
    assert response.status_code == 409


def test_scheduling_action_requires_ready_to_schedule_state(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "schedule.db"))
    with TestClient(app) as client:
        lead = client.post("/api/leads", json=QUALIFIED).json()
        blocked = client.post(
            f"/api/leads/{lead['id']}/actions",
            json={"action_key": "schedule-1", "action_type": "schedule-discovery"},
        )
        moved = client.patch(
            f"/api/leads/{lead['id']}/state",
            json={"to_state": "ready-to-schedule", "reason_code": "operator.approved"},
        )
        queued = client.post(
            f"/api/leads/{lead['id']}/actions",
            json={"action_key": "schedule-1", "action_type": "schedule-discovery"},
        )
    assert blocked.status_code == 409
    assert moved.status_code == 200
    assert queued.status_code == 201
    assert queued.json()["status"] == "queued"


def test_retry_backoff_and_dead_letter_are_bounded(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "retry.db"))
    with TestClient(app) as client:
        lead = client.post("/api/leads", json=QUALIFIED).json()

    action = enqueue_outbound_action(
        lead["id"],
        OutboundActionRequest(
            action_key="retry-1", action_type="follow-up-email", max_attempts=2
        ),
    )
    now = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)
    claimed = claim_next_outbound_action(now)
    assert claimed is not None and claimed.id == action.id
    assert claimed.status == "in-progress" and claimed.attempts == 1

    retry = record_outbound_result(
        action.id,
        OutboundActionResultRequest(
            success=False, retryable=True, error_code="provider.timeout"
        ),
        now,
    )
    assert retry.status == "retry-wait"
    assert retry.next_attempt_at == "2026-09-28 12:01:00"
    assert claim_next_outbound_action(now) is None

    second = claim_next_outbound_action(now + timedelta(minutes=1))
    assert second is not None and second.attempts == 2
    dead = record_outbound_result(
        action.id,
        OutboundActionResultRequest(
            success=False, retryable=True, error_code="provider.timeout"
        ),
        now + timedelta(minutes=1),
    )
    assert dead.status == "dead-letter"
    assert dead.next_attempt_at is None
    assert claim_next_outbound_action(now + timedelta(hours=1)) is None


def test_success_and_cancel_are_terminal(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "terminal-outbox.db"))
    with TestClient(app) as client:
        lead = client.post("/api/leads", json=QUALIFIED).json()
        success = client.post(
            f"/api/leads/{lead['id']}/actions",
            json={"action_key": "success-1", "action_type": "follow-up-email"},
        ).json()
        claimed = client.post("/api/outbox/claim").json()
        completed = client.patch(
            f"/api/outbox/{claimed['id']}/result", json={"success": True}
        )
        cancelled_action = client.post(
            f"/api/leads/{lead['id']}/actions",
            json={"action_key": "cancel-1", "action_type": "follow-up-email"},
        ).json()
        cancelled = client.post(f"/api/outbox/{cancelled_action['id']}/cancel")

    assert success["id"] == claimed["id"]
    assert completed.status_code == 200
    assert completed.json()["status"] == "succeeded"
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
