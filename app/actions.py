from __future__ import annotations

from app.models import ExternalActionStatus, ExternalActionType, LeadRecord


class ExternalActionNotAllowed(ValueError):
    """A requested external-action intent violates LeadFlow policy."""


def validate_external_action(
    lead: LeadRecord, action_type: ExternalActionType
) -> ExternalActionStatus:
    """Authorize planning only. This function never dispatches a provider action."""
    if lead.lifecycle_state in {"closed", "suppressed"}:
        raise ExternalActionNotAllowed(
            f"External actions are blocked while lead is {lead.lifecycle_state}."
        )

    if action_type == "email-follow-up":
        if lead.communication_status != "draft-ready":
            raise ExternalActionNotAllowed(
                "Email follow-up requires explicit communication consent and no opt-out."
            )
        return "pending-human-review"

    if action_type == "schedule-request":
        if (
            lead.lifecycle_state != "ready-to-schedule"
            or lead.scheduling_status != "ready-to-schedule"
        ):
            raise ExternalActionNotAllowed(
                "Scheduling intent requires the lead to be explicitly ready-to-schedule."
            )
        return "pending-human-review"

    raise ExternalActionNotAllowed("Unsupported external action type.")
