from __future__ import annotations

from app.models import LeadCreate, LeadLifecycleState, QualificationResult


class InvalidLifecycleTransition(ValueError):
    """Requested LeadCase lifecycle transition is not allowed by policy."""


ALLOWED_TRANSITIONS: dict[LeadLifecycleState, frozenset[LeadLifecycleState]] = {
    "received": frozenset({"awaiting-information", "qualified", "nurture", "suppressed"}),
    "awaiting-information": frozenset({"ready-for-review", "closed", "suppressed"}),
    "ready-for-review": frozenset({"qualified", "nurture", "closed", "suppressed"}),
    "qualified": frozenset({"awaiting-owner-action", "ready-to-schedule", "closed", "suppressed"}),
    "nurture": frozenset({"ready-for-review", "closed", "suppressed"}),
    "awaiting-owner-action": frozenset({"ready-to-schedule", "closed", "suppressed"}),
    "ready-to-schedule": frozenset({"scheduled", "closed", "suppressed"}),
    "scheduled": frozenset({"closed"}),
    "closed": frozenset(),
    "suppressed": frozenset(),
}


def initial_state_for_intake(
    lead: LeadCreate, qualification: QualificationResult
) -> LeadLifecycleState:
    """Derive the first durable lifecycle state through deterministic policy."""
    if lead.opted_out:
        return "suppressed"
    if qualification.routing == "needs-info":
        return "awaiting-information"
    if qualification.routing == "qualified":
        return "qualified"
    return "nurture"


def transition_reason_for_intake(
    lead: LeadCreate, qualification: QualificationResult
) -> str:
    if lead.opted_out:
        return "policy.opted-out"
    return f"qualification.{qualification.routing}"


def validate_transition(
    from_state: LeadLifecycleState, to_state: LeadLifecycleState
) -> bool:
    """Validate a lifecycle transition.

    Returning False means the requested state is already current and is therefore
    an idempotent no-op. True means a real state change is permitted.
    """
    if from_state == to_state:
        return False
    if to_state not in ALLOWED_TRANSITIONS[from_state]:
        raise InvalidLifecycleTransition(
            f"Lifecycle transition {from_state!r} -> {to_state!r} is not allowed."
        )
    return True
