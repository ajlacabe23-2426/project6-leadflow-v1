from app.followup import generate_follow_up
from app.models import LeadCreate
from app.scoring import qualify_lead


def make_lead(**overrides):
    values = {
        "name": "Jordan Lee",
        "email": "jordan@example.com",
        "phone": "555-0100",
        "source": "website",
        "service": "Automation consulting",
        "estimated_value": 12000,
        "timeline_days": 7,
        "budget_confirmed": True,
        "decision_maker": True,
        "notes": "Needs intake and scheduling automation.",
    }
    values.update(overrides)
    return LeadCreate(**values)


def test_complete_high_value_lead_scores_100_and_escalates():
    result = qualify_lead(make_lead())
    assert result.score == 100
    assert result.routing == "qualified"
    assert result.priority == "high"
    assert result.next_action == "human-priority-review"


def test_missing_critical_qualification_data_routes_to_needs_info():
    result = qualify_lead(
        make_lead(estimated_value=None, timeline_days=None)
    )
    assert result.routing == "needs-info"
    assert result.next_action == "request-missing-info"
    assert set(result.missing_information) == {
        "estimated_value",
        "timeline_days",
    }


def test_lower_intent_complete_lead_routes_to_nurture():
    result = qualify_lead(
        make_lead(
            estimated_value=500,
            timeline_days=180,
            budget_confirmed=False,
            decision_maker=False,
            phone=None,
            notes=None,
        )
    )
    assert result.routing == "nurture"
    assert result.priority == "low"
    assert result.next_action == "nurture-follow-up"


def test_qualified_follow_up_is_personalized():
    lead = make_lead(name="Taylor Morgan")
    result = qualify_lead(lead)
    message = generate_follow_up(lead, result)
    assert message.startswith("Hi Taylor")
    assert lead.service in message
    assert "discovery" in message.lower()


def test_score_is_bounded_by_100():
    result = qualify_lead(make_lead())
    assert 0 <= result.score <= 100
    assert sum(result.breakdown.values()) == result.score


def test_qualification_is_deterministic():
    lead = make_lead(estimated_value=5000, timeline_days=30)
    assert qualify_lead(lead) == qualify_lead(lead)
