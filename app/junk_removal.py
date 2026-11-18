"""Conservative, human-reviewed precheck for junk-removal inquiries.

This is a quotation/dispatch guardrail, NOT a waste classification, legal
authorization, hazardous-materials assessment, or autonomous acceptance engine.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

ItemStatus = Literal["ordinary_household", "unknown", "potentially_regulated"]
ReviewStatus = Literal["information-needed", "specialist-review", "manual-estimate"]


class JunkRemovalInquiry(BaseModel):
    service_address_or_area: str | None = Field(default=None, max_length=200)
    item_description: str = Field(min_length=3, max_length=1200)
    item_status: ItemStatus = "unknown"
    access_details: str | None = Field(default=None, max_length=500)
    approximate_load_size: str | None = Field(default=None, max_length=100)
    customer_confirms_right_to_remove: bool = False
    restricted_item_uncertainty: bool = True

    @field_validator("item_description", "service_address_or_area", "access_details", "approximate_load_size", mode="before")
    @classmethod
    def tidy_text(cls, value: object) -> object:
        if isinstance(value, str):
            return " ".join(value.split())
        return value


class JunkRemovalPrecheck(BaseModel):
    status: ReviewStatus
    reasons: list[str]
    missing_information: list[str]
    dispatch_allowed: bool = False
    quote_finalized: bool = False


def precheck_junk_removal(inquiry: JunkRemovalInquiry) -> JunkRemovalPrecheck:
    """Determine the next *human* review step; never dispatch or finalize quotes."""
    missing: list[str] = []
    reasons: list[str] = []
    if not inquiry.service_address_or_area:
        missing.append("service_area")
    if not inquiry.approximate_load_size:
        missing.append("approximate_load_size")
    if not inquiry.access_details:
        missing.append("access_details")
    if not inquiry.customer_confirms_right_to_remove:
        missing.append("right_to_remove_confirmation")

    requires_specialist = (
        inquiry.item_status == "potentially_regulated"
        or inquiry.restricted_item_uncertainty
    )
    if requires_specialist:
        reasons.append("Item eligibility or regulatory status requires human verification")
    if inquiry.item_status == "unknown":
        missing.append("item_classification")
    if missing:
        reasons.append("Collect missing job details and verify ownership or authorization")

    if requires_specialist:
        status: ReviewStatus = "specialist-review"
    elif missing:
        status = "information-needed"
    else:
        status = "manual-estimate"
        reasons.append("Human must verify disposal route, vehicle capacity, price, and schedule")

    return JunkRemovalPrecheck(
        status=status,
        reasons=reasons,
        missing_information=missing,
        dispatch_allowed=False,
        quote_finalized=False,
    )
