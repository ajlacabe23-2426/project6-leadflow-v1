from fastapi.testclient import TestClient

from app.main import app


SAMPLE_LEAD = {
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
    "communication_consent": True,
    "opted_out": False,
}


def main() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        created = client.post("/api/leads", json=SAMPLE_LEAD)
        queue = client.get("/api/leads")

    print("Health:", health.status_code, health.json())
    print("Create:", created.status_code)
    if created.is_success:
        result = created.json()
        q = result["qualification"]
        print(
            "Qualification:",
            f'{q["score"]}/100',
            q["routing"],
            q["priority"],
            q["next_action"],
        )
        print("Follow-up:", result["follow_up"])
        print("Communication:", result["communication_status"])
        print("Scheduling:", result["scheduling_status"])
        print("Audit events:", len(result["audit_history"]))

    print("Queue count:", len(queue.json()))


if __name__ == "__main__":
    main()
