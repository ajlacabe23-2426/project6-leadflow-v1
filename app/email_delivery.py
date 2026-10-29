"""Safe, provider-neutral email delivery worker foundation.

No production provider is bundled. This module cannot send anything unless a
caller supplies an adapter AND opts into the explicit sandbox-only mode.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Literal, Protocol

from app.models import OutboundActionResultRequest, LeadCreate
from app.outbox import claim_next_outbound_action, record_outbound_result
from app.storage import _connect


TransportStatus = Literal["accepted", "retryable-rejection", "permanent-rejection", "unknown"]
DispatchStatus = Literal["disabled", "empty", "accepted", "retry-wait", "dead-letter"]


@dataclass(frozen=True)
class EmailEnvelope:
    """Recipient data exists only in worker memory, not in logs or results."""
    to: str
    subject: str
    body: str


@dataclass(frozen=True)
class TransportOutcome:
    status: TransportStatus
    # Bounded constant identifiers only; no exception messages or user data.
    error_code: str | None = None


@dataclass(frozen=True)
class DispatchReport:
    status: DispatchStatus
    action_id: int | None = None
    error_code: str | None = None


class EmailTransport(Protocol):
    def send(self, email: EmailEnvelope, *, idempotency_key: str) -> TransportOutcome:
        """Caller MUST provide provider-side idempotency and accurate acceptance status."""
        ...


def _eligible_message(lead_id: int) -> tuple[EmailEnvelope | None, str | None]:
    """Recheck stored consent and lifecycle AFTER claim, just before adapter call."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT lead_json, follow_up, communication_status, lifecycle_state "
            "FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
    if row is None:
        return None, "policy.lead-missing"
    lead = LeadCreate.model_validate_json(row["lead_json"])
    if (
        not lead.communication_consent
        or lead.opted_out
        or row["communication_status"] != "draft-ready"
        or row["lifecycle_state"] in {"closed", "suppressed"}
    ):
        return None, "policy.communication-blocked"
    # Only previously generated draft content; no model call or invented promise.
    if not row["follow_up"].strip():
        return None, "policy.no-draft"
    return EmailEnvelope(
        to=str(lead.email),
        subject="Following up on your service inquiry",
        body=row["follow_up"],
    ), None


def dispatch_one_email(transport: EmailTransport | None = None) -> DispatchReport:
    """Run one explicit sandbox delivery attempt; never runs in a background loop.

    An ambiguous provider result is NOT automatically retried: a network timeout
    after provider acceptance could duplicate delivery. Manual reconciliation is
    required before enabling any production transport. No credentials or recipient
    contents are recorded in the durable outbox.
    """
    if os.getenv("LEADFLOW_DELIVERY_MODE") != "sandbox" or transport is None:
        return DispatchReport(status="disabled")

    action = claim_next_outbound_action(action_type="follow-up-email")
    if action is None:
        return DispatchReport(status="empty")

    email, policy_error = _eligible_message(action.lead_id)
    if policy_error:
        updated = record_outbound_result(
            action.id, OutboundActionResultRequest(
                success=False, retryable=False, error_code=policy_error
            ),
        )
        return DispatchReport(updated.status, action.id, policy_error)

    assert email is not None
    try:
        outcome = transport.send(email, idempotency_key=action.action_key)
    except Exception:
        # Unknown result: failure may occur AFTER external acceptance.
        # Permanently quarantine rather than retry blindly.
        outcome = TransportOutcome(status="unknown", error_code="provider.unknown")

    allowed_codes = {
        "provider.timeout-before-accept",
        "provider.rate-limited",
        "provider.unavailable",
        "provider.rejected",
        "provider.unknown",
    }
    if outcome.status == "accepted":
        result = OutboundActionResultRequest(success=True)
    else:
        code = outcome.error_code if outcome.error_code in allowed_codes else "provider.unknown"
        retryable = outcome.status == "retryable-rejection" and code != "provider.unknown"
        result = OutboundActionResultRequest(
            success=False, retryable=retryable, error_code=code
        )
    updated = record_outbound_result(action.id, result)
    return DispatchReport(
        status="accepted" if updated.status == "succeeded" else updated.status,
        action_id=action.id,
        error_code=updated.last_error_code,
    )
