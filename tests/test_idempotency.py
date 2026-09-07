from concurrent.futures import ThreadPoolExecutor
import sqlite3

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.models import LeadCreate
from app.scoring import qualify_lead
from app.storage import initialize_database, list_leads, save_lead, _legacy_fingerprint


PAYLOAD = {
    "name": "Jordan Lee", "email": "jordan@example.com", "service": "Automation",
    "estimated_value": 12000, "timeline_days": 7, "communication_consent": True,
}


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "leads.db"))
    with TestClient(app) as value:
        yield value


def test_request_key_replays_exact_record_and_rejects_changed_payload(client):
    headers = {"Idempotency-Key": "request-1"}
    first = client.post("/api/leads", json=PAYLOAD, headers=headers)
    retry = client.post("/api/leads", json=PAYLOAD, headers=headers)
    conflict = client.post("/api/leads", json={**PAYLOAD, "estimated_value": 10}, headers=headers)
    assert first.status_code == retry.status_code == 201
    assert first.json() == retry.json()
    assert conflict.status_code == 409
    assert len(client.get("/api/leads").json()) == 1


@pytest.mark.parametrize("change", [
    {"estimated_value": 10}, {"notes": "Changed scope"},
    {"communication_consent": False, "opted_out": True},
])
def test_changed_intake_is_never_discarded_as_duplicate(client, change):
    first = client.post("/api/leads", json=PAYLOAD).json()
    second = client.post("/api/leads", json={**PAYLOAD, **change}).json()
    assert first["id"] != second["id"]
    for key, value in change.items():
        assert second["lead"][key] == value
    if change.get("opted_out"):
        assert second["communication_status"] == "suppressed-opted-out"


def test_different_request_keys_represent_distinct_intakes(client):
    first = client.post("/api/leads", json=PAYLOAD, headers={"Idempotency-Key": "one"})
    second = client.post("/api/leads", json=PAYLOAD, headers={"Idempotency-Key": "two"})
    assert first.json()["id"] != second.json()["id"]


@pytest.mark.parametrize("request_key", [None, "concurrent-intake"])
def test_concurrent_retries_persist_one_record(monkeypatch, tmp_path, request_key):
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(tmp_path / "concurrent.db"))
    initialize_database()
    lead = LeadCreate(**PAYLOAD)
    qualification = qualify_lead(lead)
    with ThreadPoolExecutor(max_workers=8) as executor:
        records = list(executor.map(
            lambda _: save_lead(lead, qualification, "draft", request_key), range(24)
        ))
    assert len({record.id for record in records}) == 1
    assert len(list_leads()) == 1
    assert len(records[0].audit_history) == 4


def test_legacy_database_retries_compare_full_payload(monkeypatch, tmp_path):
    path = tmp_path / "legacy.db"
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(path))
    initialize_database()
    lead = LeadCreate(**PAYLOAD)
    original = save_lead(lead, qualify_lead(lead), "draft")
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE leads SET fingerprint = ?", (_legacy_fingerprint(lead),))
    initialize_database()
    assert save_lead(lead, qualify_lead(lead), "draft").id == original.id
    changed = lead.model_copy(update={"notes": "New requirements"})
    assert save_lead(changed, qualify_lead(changed), "draft").id != original.id


def test_key_replay_survives_24_hour_legacy_window(monkeypatch, tmp_path):
    path = tmp_path / "retained.db"
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(path))
    initialize_database()
    lead = LeadCreate(**PAYLOAD)
    first = save_lead(lead, qualify_lead(lead), "draft", "retained")
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE leads SET created_at = '2020-01-01 00:00:00'")
    assert save_lead(lead, qualify_lead(lead), "draft", "retained").id == first.id


@pytest.mark.parametrize("key", ["", "bad key", "x" * 129])
def test_invalid_request_key_is_rejected(client, key):
    assert client.post("/api/leads", json=PAYLOAD, headers={"Idempotency-Key": key}).status_code == 422


def test_nonfinite_estimated_value_is_rejected(client):
    assert client.post("/api/leads", json={**PAYLOAD, "estimated_value": "Infinity"}).status_code == 422


def test_overflow_json_returns_safe_422_without_echoing_intake(client):
    response = client.post(
        "/api/leads",
        content='{"name":"Jordan Lee","email":"jordan@example.com","service":"Automation","estimated_value":1e999}',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert all(set(item) == {"loc", "msg", "type"} for item in response.json()["detail"])
    assert "jordan@example.com" not in response.text


def test_failed_request_mapping_rolls_back_lead_and_audit(monkeypatch, tmp_path):
    path = tmp_path / "rollback.db"
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(path))
    initialize_database()
    with sqlite3.connect(path) as connection:
        connection.execute("""
            CREATE TRIGGER reject_mapping BEFORE INSERT ON intake_requests
            BEGIN SELECT RAISE(ABORT, 'simulated storage failure'); END
        """)
    lead = LeadCreate(**PAYLOAD)
    with pytest.raises(sqlite3.IntegrityError):
        save_lead(lead, qualify_lead(lead), "draft", "failed-key")
    assert list_leads() == []
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM intake_requests").fetchone()[0] == 0
        connection.execute("DROP TRIGGER reject_mapping")
    assert save_lead(lead, qualify_lead(lead), "draft", "failed-key").lead == lead


def test_concurrent_initialization_upgrades_original_schema(monkeypatch, tmp_path):
    path = tmp_path / "original.db"
    monkeypatch.setenv("LEADFLOW_DB_PATH", str(path))
    with sqlite3.connect(path) as connection:
        connection.execute("""
            CREATE TABLE leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                lead_json TEXT NOT NULL, qualification_json TEXT NOT NULL,
                follow_up TEXT NOT NULL
            )
        """)
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(lambda _: initialize_database(), range(4)))
    lead = LeadCreate(**PAYLOAD)
    first = save_lead(lead, qualify_lead(lead), "draft", "after-upgrade")
    assert save_lead(lead, qualify_lead(lead), "draft", "after-upgrade").id == first.id
