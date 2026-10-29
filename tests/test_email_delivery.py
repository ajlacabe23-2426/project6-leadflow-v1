from fastapi.testclient import TestClient

from app.email_delivery import (
    DispatchReport, EmailEnvelope, TransportOutcome, dispatch_one_email,
)
from app.main import app
from app.models import OutboundActionRequest
from app.outbox import enqueue_outbound_action, list_outbound_actions
from app.storage import _connect


LEAD = {
    "name":"Synthetic Buyer",
    "email":"test-buyer@example.com",
    "service":"Example Service",
    "source":"test",
    "estimated_value":1000,
    "timeline_days":7,
    "budget_confirmed":True,
    "decision_maker":True,
    "communication_consent":True,
    "opted_out":False,
}


class FakeTransport:
    def __init__(self, outcome: TransportOutcome | None = None, fail: bool = False):
        self.messages: list[tuple[EmailEnvelope, str]] = []
        self.outcome = outcome or TransportOutcome("accepted")
        self.fail = fail

    def send(self, email: EmailEnvelope, *, idempotency_key: str) -> TransportOutcome:
        self.messages.append((email, idempotency_key))
        if self.fail:
            raise TimeoutError("Synthetic ambiguous provider response")
        return self.outcome


def create_action(client: TestClient, key: str = "send-once") -> int:
    lead_id = client.post("/api/leads",json=LEAD).json()["id"]
    enqueue_outbound_action(lead_id, OutboundActionRequest(
        action_key=key,action_type="follow-up-email",max_attempts=2
    ))
    return lead_id


def test_disabled_by_default_does_not_claim_or_send(monkeypatch,tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH",str(tmp_path/"disabled.db"))
    monkeypatch.delenv("LEADFLOW_DELIVERY_MODE",raising=False)
    with TestClient(app) as client:
        create_action(client)
        fake=FakeTransport()
        report=dispatch_one_email(fake)
    assert report.status=="disabled"
    assert fake.messages==[]
    assert list_outbound_actions()[0].status=="queued"


def test_sandbox_send_only_once_and_preserves_provider_idempotency(monkeypatch,tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH",str(tmp_path/"success.db"))
    monkeypatch.setenv("LEADFLOW_DELIVERY_MODE","sandbox")
    with TestClient(app) as client:
        create_action(client)
        fake=FakeTransport()
        first=dispatch_one_email(fake)
        second=dispatch_one_email(fake)
    assert first.status=="sent"
    assert second.status=="empty"
    assert len(fake.messages)==1
    envelope,key=fake.messages[0]
    assert envelope.to==LEAD["email"]
    assert key=="send-once"
    assert "Synthetic Buyer" in envelope.body
    assert len(list_outbound_actions())==1
    assert list_outbound_actions()[0].status=="succeeded"
    # The redacted report does not expose a recipient or draft content.
    assert LEAD["email"] not in repr(first)


def test_revoked_consent_after_queue_blocks_adapter(monkeypatch,tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH",str(tmp_path/"revoked.db"))
    monkeypatch.setenv("LEADFLOW_DELIVERY_MODE","sandbox")
    with TestClient(app) as client:
        lead_id=create_action(client)
    with _connect() as conn:
        conn.execute(
            "UPDATE leads SET communication_status='suppressed-opted-out' WHERE id=?",
            (lead_id,)
        )
    fake=FakeTransport()
    report=dispatch_one_email(fake)
    assert fake.messages==[]
    assert report.status=="dead-letter"
    assert report.error_code=="policy.communication-blocked"


def test_known_preaccept_rejection_retries_and_unknown_quarantines(monkeypatch,tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH",str(tmp_path/"failures.db"))
    monkeypatch.setenv("LEADFLOW_DELIVERY_MODE","sandbox")
    with TestClient(app) as client:
        create_action(client,key="retry-1")
        # A separate calendar intent must not be consumed by the email worker.
        lead_id=client.get("/api/leads").json()[0]["id"]
        client.patch(f"/api/leads/{lead_id}/state",json={
            "to_state":"ready-to-schedule","reason_code":"operator.approved"
        })
        enqueue_outbound_action(lead_id,OutboundActionRequest(
            action_key="calendar-1",action_type="schedule-discovery"
        ))
    retry=FakeTransport(TransportOutcome(
        "retryable-rejection","provider.rate-limited"
    ))
    result=dispatch_one_email(retry)
    assert result.status=="retry-wait"
    assert len(retry.messages)==1
    actions=list_outbound_actions()
    assert any(a.action_type=="schedule-discovery" and a.status=="queued" for a in actions)
    assert dispatch_one_email(FakeTransport()).status=="empty"

    # New action with ambiguous result must never auto retry.
    with TestClient(app) as client:
        lead_id=client.get("/api/leads").json()[0]["id"]
    enqueue_outbound_action(lead_id,OutboundActionRequest(
        action_key="unknown-1",action_type="follow-up-email"
    ))
    fake=FakeTransport(fail=True)
    result=dispatch_one_email(fake)
    assert result.status=="dead-letter"
    assert result.error_code=="provider.unknown"
    assert dispatch_one_email(FakeTransport()).status=="empty"
    assert len(fake.messages)==1


def test_no_adapter_even_in_sandbox_cannot_consume_queue(monkeypatch,tmp_path):
    monkeypatch.setenv("LEADFLOW_DB_PATH",str(tmp_path/"missing-adapter.db"))
    monkeypatch.setenv("LEADFLOW_DELIVERY_MODE","sandbox")
    with TestClient(app) as client:
        create_action(client)
    assert dispatch_one_email().status=="disabled"
    assert list_outbound_actions()[0].status=="queued"
