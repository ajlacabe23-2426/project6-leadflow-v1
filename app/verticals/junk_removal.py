"""Pure, non-persistent junk-removal precheck mirroring the Project 8 vertical contract.

This does not create leads, quote work, send communications, determine service
area, or authorize handling/disposal. All customer decisions require an operator.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

JOB_TYPES = frozenset({"single_item", "multiple_items", "partial_cleanout", "full_cleanout"})
LOAD_SIZES = frozenset({"small", "medium", "large"})
ACCESS = frozenset({"curbside", "ground_floor", "stairs"})
CATEGORIES = frozenset({
    "furniture", "appliances", "electronics", "yard_debris", "construction", "general_household"
})
REVIEW_CATEGORIES = frozenset({"appliances", "electronics", "construction"})


def assess_junk_removal_intake(value: object) -> dict[str, Any]:
    """Only return internal reason codes and consent indicators, never input PII."""
    data: Mapping[str, object] = value if isinstance(value, Mapping) else {}
    missing: list[str] = []
    review_reasons: list[str] = []

    zip_code = data.get("zipCode")
    if not isinstance(zip_code, str) or re.fullmatch(r"[0-9]{5}", zip_code) is None:
        missing.append("zip_code")
    job_type = data.get("jobType")
    if not isinstance(job_type, str) or job_type not in JOB_TYPES:
        missing.append("job_type")
    size = data.get("loadSize")
    if not isinstance(size, str) or size not in LOAD_SIZES:
        missing.append("load_size")
    access = data.get("access")
    if not isinstance(access, str) or access not in ACCESS:
        missing.append("access")

    categories = data.get("categories")
    if (not isinstance(categories, list) or not 1 <= len(categories) <= 12
            or any(not isinstance(category, str) or category not in CATEGORIES for category in categories)):
        missing.append("item_categories")
    elif any(category in REVIEW_CATEGORIES for category in categories):
        review_reasons.append("SPECIAL_DISPOSAL_REQUIREMENTS_UNVERIFIED")

    if data.get("possibleRestrictedMaterials") is True:
        review_reasons.append("RESTRICTED_MATERIALS_REQUIRE_OPERATOR_REVIEW")
    elif data.get("possibleRestrictedMaterials") is not False:
        missing.append("restricted_materials_confirmation")

    if access == "stairs":
        review_reasons.append("STAIR_ACCESS_REQUIRES_MANUAL_PLANNING")

    kind = ("requires_special_handling_review" if review_reasons else
            "needs_details" if missing else "ready_for_human_estimate")
    return {
        "kind": kind,
        "missing": missing,
        "reviewReasons": review_reasons,
        "followUpPermitted": data.get("communicationConsent") is True and data.get("optedOut") is False,
        "automaticQuotePermitted": False,
    }
