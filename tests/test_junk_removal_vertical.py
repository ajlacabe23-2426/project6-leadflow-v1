"""Pure-junk-removal intake parity tests with the Project 8 TypeScript contract."""
from app.verticals.junk_removal import assess_junk_removal_intake as assess

BASE = {
    "zipCode": "61701", "jobType": "multiple_items", "loadSize": "medium",
    "access": "ground_floor", "categories": ["furniture"],
    "possibleRestrictedMaterials": False, "communicationConsent": False,
    "optedOut": False
}


def test_valid_example_returns_human_only_estimate():
    assert assess(BASE) == {
        "kind": "ready_for_human_estimate", "missing": [], "reviewReasons": [],
        "followUpPermitted": False, "automaticQuotePermitted": False
    }


def test_missing_or_malformed_info_fails_closed():
    result = assess({**BASE, "zipCode": "invalid", "access": "unknown", "categories": []})
    assert result["kind"] == "needs_details"
    assert result["missing"] == ["zip_code", "access", "item_categories"]
    assert assess(None)["kind"] == "needs_details"
    assert assess({**BASE, "possibleRestrictedMaterials": "no"})["kind"] == "needs_details"


def test_special_materials_and_stairs_trigger_manual_review():
    for category in ("appliances", "electronics", "construction"):
        result = assess({**BASE, "categories": [category]})
        assert result["kind"] == "requires_special_handling_review"
        assert "SPECIAL_DISPOSAL_REQUIREMENTS_UNVERIFIED" in result["reviewReasons"]
    flagged = assess({**BASE, "possibleRestrictedMaterials": True, "access": "stairs"})
    assert flagged["reviewReasons"] == [
        "RESTRICTED_MATERIALS_REQUIRE_OPERATOR_REVIEW",
        "STAIR_ACCESS_REQUIRES_MANUAL_PLANNING"
    ]


def test_contact_permission_requires_explicit_yes_and_explicit_no_to_opt_out():
    assert assess({**BASE, "communicationConsent": True})["followUpPermitted"] is True
    assert assess({**BASE, "communicationConsent": True, "optedOut": True})["followUpPermitted"] is False
    assert assess({**BASE, "communicationConsent": "yes"})["followUpPermitted"] is False
    incomplete = dict(BASE, communicationConsent=True)
    del incomplete["optedOut"]
    assert assess(incomplete)["followUpPermitted"] is False


def test_output_is_personal_data_minimized():
    result = assess({**BASE, "email": "fixture@example.test", "notes": "fictional private notes"})
    assert "fixture@example.test" not in str(result)
    assert "fictional private notes" not in str(result)
    assert result["automaticQuotePermitted"] is False
