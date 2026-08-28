from __future__ import annotations

from app.models import LeadCreate, QualificationResult


def _value_points(value: float | None) -> int:
    if value is None:
        return 0
    if value >= 10_000:
        return 30
    if value >= 5_000:
        return 22
    if value >= 2_000:
        return 15
    return 8


def _timeline_points(days: int | None) -> int:
    if days is None:
        return 0
    if days <= 7:
        return 25
    if days <= 30:
        return 18
    if days <= 90:
        return 10
    return 4


def _completeness_points(lead: LeadCreate) -> int:
    fields = [
        bool(lead.phone),
        bool(lead.source),
        bool(lead.service),
        lead.estimated_value is not None,
        bool(lead.notes),
    ]
    return sum(3 for present in fields if present)


def qualify_lead(lead: LeadCreate) -> QualificationResult:
    breakdown = {
        "opportunity_value": _value_points(lead.estimated_value),
        "timeline": _timeline_points(lead.timeline_days),
        "budget_confirmed": 15 if lead.budget_confirmed else 0,
        "decision_maker": 15 if lead.decision_maker else 0,
        "completeness": _completeness_points(lead),
    }

    score = sum(breakdown.values())

    missing_information: list[str] = []
    if lead.estimated_value is None:
        missing_information.append("estimated_value")
    if lead.timeline_days is None:
        missing_information.append("timeline_days")

    if missing_information:
        routing = "needs-info"
    elif score >= 70:
        routing = "qualified"
    else:
        routing = "nurture"

    if score >= 85:
        priority = "high"
    elif score >= 60:
        priority = "medium"
    else:
        priority = "low"

    if priority == "high" and routing == "qualified":
        next_action = "human-priority-review"
    elif routing == "qualified":
        next_action = "schedule-discovery"
    elif routing == "needs-info":
        next_action = "request-missing-info"
    else:
        next_action = "nurture-follow-up"

    return QualificationResult(
        score=score,
        routing=routing,
        priority=priority,
        next_action=next_action,
        breakdown=breakdown,
        missing_information=missing_information,
    )
