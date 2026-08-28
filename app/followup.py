from __future__ import annotations

from app.models import LeadCreate, QualificationResult


def generate_follow_up(
    lead: LeadCreate,
    qualification: QualificationResult,
) -> str:
    first_name = lead.name.split()[0]

    if qualification.routing == "needs-info":
        missing = ", ".join(
            item.replace("_", " ")
            for item in qualification.missing_information
        )
        return (
            f"Hi {first_name}, thanks for reaching out about {lead.service}. "
            f"I have your request and just need a little more information "
            f"about {missing} before we recommend the right next step."
        )

    if qualification.routing == "qualified":
        return (
            f"Hi {first_name}, thanks for reaching out about {lead.service}. "
            "Your request looks like a strong fit for a discovery conversation. "
            "The next step is to review the details together and confirm scope, "
            "timing, and scheduling."
        )

    return (
        f"Hi {first_name}, thanks for your interest in {lead.service}. "
        "I have your information and will keep the conversation moving with "
        "a focused follow-up based on your timing and requirements."
    )
