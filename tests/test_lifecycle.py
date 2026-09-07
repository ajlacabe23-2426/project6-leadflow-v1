from fastapi.testclient import TestClient

from app.main import app


QUALIFIED_LEAD = {
    "name": "Jordan Lee",
    "email": "jordan@example.com",
    "service": "Automation consulting",
    "estimated_value": 12000,
    "timeline_days": 7,
    "budget_confirmed": True,
    "decision_maker": True,
    "communication_consent": True,
}


def test_intake_sets_explicit_lifecycle_and_transition_evidence(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "lifecycle.db"))
    with TestClient(app) as client:
        response = client.post(
            "/api/leads",
            json=QUALIFIED_LEAD,
            headers={"Idempotency-Key": "lifecycle-intake-1"},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["lifecycle_state"] == "qualified"
    transition = body["audit_history"][1]
    assert transition["from_state"] == "received"
    assert transition["to_state"] == "qualified"
    assert transition["reason_code"] == "qualification.qualified"
    assert transition["correlation_id"] == "lifecycle-intake-1"


def test_missing_information_and_opt_out_map_to_policy_states(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "policy-states.db"))
    missing = {
        "name": "Case One",
        "email": "case1@example.com",
        "service": "Automation",
    }
    suppressed = {
        **QUALIFIED_LEAD,
        "email": "case2@example.com",
        "communication_consent": False,
        "opted_out": True,
    }
    with TestClient(app) as client:
        missing_response = client.post("/api/leads", json=missing)
        suppressed_response = client.post("/api/leads", json=suppressed)

    assert missing_response.json()["lifecycle_state"] == "awaiting-information"
    assert suppressed_response.json()["lifecycle_state"] == "suppressed"
    assert suppressed_response.json()["audit_history"][1]["reason_code"] == "policy.opted-out"


def test_transition_boundary_is_atomic_audited_and_idempotent(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "transitions.db"))
    with TestClient(app) as client:
        created = client.post("/api/leads", json=QUALIFIED_LEAD).json()
        lead_id = created["id"]
        before_count = len(created["audit_history"])

        moved = client.patch(
            f"/api/leads/{lead_id}/state",
            json={
                "to_state": "awaiting-owner-action",
                "reason_code": "operator.review-required",
                "correlation_id": "case-review-1",
            },
        )
        repeated = client.patch(
            f"/api/leads/{lead_id}/state",
            json={
                "to_state": "awaiting-owner-action",
                "reason_code": "operator.review-required",
                "correlation_id": "case-review-1",
            },
        )

    assert moved.status_code == 200
    body = moved.json()
    assert body["lifecycle_state"] == "awaiting-owner-action"
    assert len(body["audit_history"]) == before_count + 1
    event = body["audit_history"][-1]
    assert event["event_type"] == "lifecycle.transition"
    assert event["from_state"] == "qualified"
    assert event["to_state"] == "awaiting-owner-action"
    assert event["reason_code"] == "operator.review-required"
    assert event["correlation_id"] == "case-review-1"
    assert len(repeated.json()["audit_history"]) == before_count + 1


def test_forbidden_and_terminal_transitions_fail_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "terminal.db"))
    with TestClient(app) as client:
        created = client.post("/api/leads", json=QUALIFIED_LEAD).json()
        lead_id = created["id"]
        forbidden = client.patch(
            f"/api/leads/{lead_id}/state",
            json={"to_state": "nurture", "reason_code": "operator.override"},
        )
        closed = client.patch(
            f"/api/leads/{lead_id}/state",
            json={"to_state": "closed", "reason_code": "operator.closed"},
        )
        reopen = client.patch(
            f"/api/leads/{lead_id}/state",
            json={"to_state": "qualified", "reason_code": "operator.reopen"},
        )

    assert forbidden.status_code == 409
    assert closed.status_code == 200
    assert closed.json()["lifecycle_state"] == "closed"
    assert reopen.status_code == 409


def test_unknown_lead_transition_returns_404(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "missing-lead.db"))
    with TestClient(app) as client:
        response = client.patch(
            "/api/leads/999/state",
            json={"to_state": "closed", "reason_code": "operator.closed"},
        )
    assert response.status_code == 404
