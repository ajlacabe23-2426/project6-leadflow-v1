"""Deterministic, retry-safe local workflow activation. Never sends outbound messages."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models import LeadRecord
from app.operations import (
    LeadAssignmentRequest,
    LeadObligationRequest,
    assign_lead,
    create_obligation,
)


def ensure_initial_triage(record: LeadRecord) -> None:
    """Create one queue ownership event and one time-bound internal task.

    Replaying the same accepted lead preserves the same correlation identifiers
    and the same due time derived from its immutable creation timestamp.
    """
    created = datetime.fromisoformat(record.created_at.replace("Z", "+00:00"))
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    created = created.astimezone(timezone.utc)
    urgency = record.qualification.priority
    minutes = {"high": 15, "medium": 60, "low": 240}[urgency]

    assign_lead(
        record.id,
        LeadAssignmentRequest(
            owner_ref="queue.triage",
            reason_code="intake-routing",
            correlation_id=f"auto-assignment-{record.id}",
        ),
    )
    task_type = (
        "owner-review"
        if not record.lead.communication_consent or record.lead.opted_out
        else "missing-info-followup"
        if record.qualification.routing == "needs-info"
        else "first-response"
    )
    create_obligation(
        record.id,
        LeadObligationRequest(
            obligation_type=task_type,
            due_at=created + timedelta(minutes=minutes),
            reason_code="auto.initial-triage",
            correlation_id=f"auto-triage-{record.id}",
        ),
    )
