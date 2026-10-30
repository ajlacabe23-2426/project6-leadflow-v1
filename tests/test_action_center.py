"""Action Center and self-service widget acceptance, isolated to synthetic data."""
from fastapi.testclient import TestClient
from app.main import app


EXAMPLE = {
    "name": "Example Operator Lead",
    "email": "example-lead@example.com",
    "service": "Website design",
    "estimated_value": 12000,
    "timeline_days": 3,
    "budget_confirmed": True,
    "decision_maker": True,
    "communication_consent": True,
}


def test_auto_triage_is_created_once_and_persists(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "triage.db"))
    monkeypatch.setenv("LEADFLOW_ENABLE_AUTO_TRIAGE", "1")
    with TestClient(app) as client:
        created = client.post("/api/leads", json=EXAMPLE)
        assert created.status_code == 201
        lead_id = created.json()["id"]
        replay = client.post("/api/leads", json=EXAMPLE)
        assert replay.status_code == 201
        assert replay.json()["id"] == lead_id

        actions = client.get("/api/action-center")
        assert actions.status_code == 200
        assert len(actions.json()["items"]) == 1
        first = actions.json()["items"][0]
        assert first["owner"] == "queue.triage"
        assert len(first["assignment_history"]) == 1
        assert len(first["obligations"]) == 1
        obligation = first["obligations"][0]
        assert obligation["obligation_type"] == "first-response"
        assert obligation["status"] == "open"

        done = client.patch(
            "/api/obligations/" + str(obligation["id"]) + "/complete"
        )
        assert done.status_code == 200
        again = client.get("/api/action-center")
        assert again.json()["items"][0]["obligations"][0]["status"] == "completed"

        claim = client.post(
            "/api/leads/" + str(lead_id) + "/assignments",
            json={"owner_ref": "operator.test", "reason_code": "operator-reassignment"},
        )
        assert claim.status_code == 201
        assert client.get("/api/action-center").json()["items"][0]["owner"] == "operator.test"


def test_no_consent_creates_internal_review_only(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "no-consent.db"))
    monkeypatch.setenv("LEADFLOW_ENABLE_AUTO_TRIAGE", "1")
    with TestClient(app) as client:
        response = client.post(
            "/api/leads",
            json={**EXAMPLE, "communication_consent": False},
        )
        assert response.status_code == 201
        assert response.json()["communication_status"] == "suppressed-no-consent"
        action = client.get("/api/action-center").json()["items"][0]
        assert action["obligations"][0]["obligation_type"] == "owner-review"


def test_optional_operator_gate_protects_action_center(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "operator.db"))
    monkeypatch.setenv("LEADFLOW_OPERATOR_TOKEN", "x" * 48)
    monkeypatch.setenv("LEADFLOW_REQUIRE_OPERATOR_AUTH", "1")
    with TestClient(app) as client:
        assert client.post("/api/leads", json=EXAMPLE).status_code == 201
        assert client.get("/api/action-center").status_code == 401
        response = client.get(
            "/api/action-center", headers={"Authorization": "Bearer " + "x" * 48}
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1


def test_widget_and_operator_pages_are_separate_and_dont_send(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "widget.db"))
    with TestClient(app) as client:
        screen = client.get("/action-center")
        widget = client.get("/widget")
        embed = client.get("/embed.js")
        assert screen.status_code == 200
        assert "Action Center" in screen.text
        assert widget.status_code == 200
        assert "Request a callback" in widget.text
        assert "/api/leads" in widget.text
        assert "No outbound message was sent" in widget.text
        assert embed.status_code == 200
        assert "/widget" in embed.text
        assert "iframe" in embed.text
        demo = client.get("/embed-demo")
        assert demo.status_code == 200
        assert '<script src="/embed.js"' in demo.text
