"""Guardrail tests for the standalone junk-removal intake precheck."""
from app.junk_removal import JunkRemovalInquiry, precheck_junk_removal


def inquiry(**overrides):
    data = {
        "service_address_or_area": "Bloomington, IL",
        "item_description": "Old sofa and table",
        "item_status": "ordinary_household",
        "access_details": "Ground-level garage",
        "approximate_load_size": "One pickup load",
        "customer_confirms_right_to_remove": True,
        "restricted_item_uncertainty": False,
    }
    data.update(overrides)
    return JunkRemovalInquiry(**data)


def test_complete_ordinary_job_requires_manual_estimate():
    result = precheck_junk_removal(inquiry())
    assert result.status == "manual-estimate"
    assert not result.dispatch_allowed
    assert not result.quote_finalized
    assert result.missing_information == []


def test_suspected_regulated_material_blocks_automatic_acceptance():
    result = precheck_junk_removal(inquiry(item_status="potentially_regulated"))
    assert result.status == "specialist-review"
    assert not result.dispatch_allowed
    assert not result.quote_finalized


def test_unsure_item_status_also_requires_specialist_review():
    result = precheck_junk_removal(inquiry(item_status="unknown", restricted_item_uncertainty=True))
    assert result.status == "specialist-review"
    assert "item_classification" in result.missing_information


def test_missing_area_access_and_load_information_are_flagged():
    result = precheck_junk_removal(inquiry(service_address_or_area=None, access_details=None, approximate_load_size=None))
    assert result.status == "information-needed"
    assert set(result.missing_information) == {"service_area", "access_details", "approximate_load_size"}


def test_no_customer_authorization_needs_confirmation():
    result = precheck_junk_removal(inquiry(customer_confirms_right_to_remove=False))
    assert result.status == "information-needed"
    assert "right_to_remove_confirmation" in result.missing_information


def test_precheck_does_not_return_price_or_booking_even_on_complete_lead():
    result = precheck_junk_removal(inquiry()).model_dump()
    assert result["dispatch_allowed"] is False
    assert result["quote_finalized"] is False
    assert "price" not in result
    assert "booking" not in result
