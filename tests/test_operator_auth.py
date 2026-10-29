"""Security regressions for LeadFlow's intentionally limited operator token guard."""
from fastapi.testclient import TestClient

from app.main import app
from test_api import SAMPLE_LEAD


def test_protected_queue_requires_exact_token_and_keeps_intake_public(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "secure-queue.db"))
    monkeypatch.setenv("LEADFLOW_REQUIRE_OPERATOR_AUTH", "1")
    token = "synthetic-access-token-" + "a" * 40
    monkeypatch.setenv("LEADFLOW_OPERATOR_TOKEN", token)

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/").status_code == 200
        intake = client.post("/api/leads", json=SAMPLE_LEAD)
        assert intake.status_code == 201
        assert intake.headers["cache-control"] == "no-store"
        lead_id = intake.json()["id"]

        for headers in (
            {},
            {"Authorization": "Bearer incorrect"},
            {"Authorization": "Basic " + token},
            {"Authorization": "Bearer " + token + "more"},
        ):
            private = client.get("/api/leads", headers=headers)
            assert private.status_code == 401
            assert private.json() == {"detail": "Operator authentication required"}
            assert private.headers["cache-control"] == "no-store"
            assert private.headers["www-authenticate"] == "Bearer"

        # Each operator route is guarded, including all data-changing endpoints.
        assert client.patch(
            f"/api/leads/{lead_id}/state", json={}, headers={}
        ).status_code == 401
        assert client.post("/api/outbox/claim").status_code == 401
        assert client.get("/api/obligations/overdue").status_code == 401

        authorized = client.get(
            "/api/leads", headers={"Authorization": f"Bearer {token}"}
        )
        assert authorized.status_code == 200
        assert authorized.headers["cache-control"] == "no-store"
        assert authorized.json()[0]["lead"]["email"] == SAMPLE_LEAD["email"]


def test_hosted_require_flag_fails_closed_without_token(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "missing-token.db"))
    monkeypatch.setenv("LEADFLOW_REQUIRE_OPERATOR_AUTH", "1")
    monkeypatch.delenv("LEADFLOW_OPERATOR_TOKEN", raising=False)
    with TestClient(app) as client:
        response = client.get("/api/leads")
        assert response.status_code == 503
        assert response.headers["cache-control"] == "no-store"
        assert response.json() == {"detail": "Operator access is not configured"}
        assert client.post("/api/leads", json=SAMPLE_LEAD).status_code == 201


def test_weak_configured_token_fails_closed_even_in_local_mode(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "weak-token.db"))
    monkeypatch.delenv("LEADFLOW_REQUIRE_OPERATOR_AUTH", raising=False)
    monkeypatch.setenv("LEADFLOW_OPERATOR_TOKEN", "too-short")
    with TestClient(app) as client:
        response = client.get(
            "/api/leads", headers={"Authorization": "Bearer too-short"}
        )
        assert response.status_code == 503


def test_unconfigured_local_demo_remains_synthetic_only(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "local-demo.db"))
    monkeypatch.delenv("LEADFLOW_REQUIRE_OPERATOR_AUTH", raising=False)
    monkeypatch.delenv("LEADFLOW_OPERATOR_TOKEN", raising=False)
    with TestClient(app) as client:
        assert client.get("/api/leads").status_code == 200
        # Local/demo mode is deliberately not fit for public exposure.
