from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

from app.storage import LeadNotFound, _connect


AssignmentReason = Literal[
    "intake-routing",
    "operator-reassignment",
    "specialist-review",
    "sla-escalation",
]
ObligationType = Literal[
    "first-response",
    "missing-info-followup",
    "owner-review",
    "scheduling",
]
ObligationStatus = Literal["open", "completed", "cancelled"]


class LeadAssignmentRequest(BaseModel):
    owner_ref: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9._:@-]+$")
    reason_code: AssignmentReason
    correlation_id: str | None = Field(
        default=None, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$"
    )


class LeadAssignment(BaseModel):
    id: int
    lead_id: int
    owner_ref: str
    reason_code: AssignmentReason
    correlation_id: str
    assigned_at: str


class LeadObligationRequest(BaseModel):
    obligation_type: ObligationType
    due_at: AwareDatetime
    reason_code: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9._:-]+$")
    correlation_id: str | None = Field(
        default=None, min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$"
    )


class LeadObligation(BaseModel):
    id: int
    lead_id: int
    obligation_type: ObligationType
    due_at: str
    status: ObligationStatus
    reason_code: str
    correlation_id: str
    created_at: str
    completed_at: str | None = None


class ObligationNotFound(LookupError):
    pass


class InvalidObligationTransition(ValueError):
    pass


class AssignmentIdempotencyConflict(ValueError):
    pass


class ObligationIdempotencyConflict(ValueError):
    pass


def initialize_operations_tables() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS lead_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                owner_ref TEXT NOT NULL,
                reason_code TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_lead_assignments_lead "
            "ON lead_assignments(lead_id, id)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS lead_obligations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                obligation_type TEXT NOT NULL,
                due_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                reason_code TEXT NOT NULL,
                correlation_id TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_lead_obligations_due "
            "ON lead_obligations(status, due_at, lead_id)"
        )


def _ensure_lead(connection, lead_id: int) -> None:
    row = connection.execute("SELECT id FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if row is None:
        raise LeadNotFound(f"Lead {lead_id} was not found.")


def _assignment(row) -> LeadAssignment:
    return LeadAssignment(**dict(row))


def _obligation(row) -> LeadObligation:
    return LeadObligation(**dict(row))


def assign_lead(lead_id: int, request: LeadAssignmentRequest) -> LeadAssignment:
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _ensure_lead(connection, lead_id)
        # Caller-provided correlation IDs represent one logical assignment.
        # The immediate transaction serializes concurrent retries in local SQLite.
        if request.correlation_id is not None:
            previous = connection.execute(
                """
                SELECT * FROM lead_assignments
                WHERE lead_id = ? AND correlation_id = ?
                ORDER BY id LIMIT 1
                """,
                (lead_id, request.correlation_id),
            ).fetchone()
            if previous is not None:
                if (previous["owner_ref"], previous["reason_code"]) != (
                    request.owner_ref, request.reason_code
                ):
                    raise AssignmentIdempotencyConflict(
                        "Assignment correlation ID was reused with different contents."
                    )
                return _assignment(previous)
        correlation_id = request.correlation_id or f"assignment:{lead_id}"
        cursor = connection.execute(
            """
            INSERT INTO lead_assignments(lead_id, owner_ref, reason_code, correlation_id)
            VALUES (?, ?, ?, ?)
            """,
            (lead_id, request.owner_ref, request.reason_code, correlation_id),
        )
        row = connection.execute(
            "SELECT * FROM lead_assignments WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    if row is None:
        raise RuntimeError("Lead assignment was not persisted.")
    return _assignment(row)


def list_assignments(lead_id: int) -> list[LeadAssignment]:
    with _connect() as connection:
        _ensure_lead(connection, lead_id)
        rows = connection.execute(
            "SELECT * FROM lead_assignments WHERE lead_id = ? ORDER BY id",
            (lead_id,),
        ).fetchall()
    return [_assignment(row) for row in rows]


def create_obligation(lead_id: int, request: LeadObligationRequest) -> LeadObligation:
    due_at = request.due_at.astimezone(timezone.utc).isoformat()
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _ensure_lead(connection, lead_id)
        # Only explicitly supplied IDs are replay keys. Legacy requests without
        # one continue to create distinct obligations for each operator action.
        if request.correlation_id is not None:
            previous = connection.execute(
                """
                SELECT * FROM lead_obligations
                WHERE lead_id = ? AND correlation_id = ?
                ORDER BY id LIMIT 1
                """,
                (lead_id, request.correlation_id),
            ).fetchone()
            if previous is not None:
                if (
                    previous["obligation_type"] != request.obligation_type
                    or previous["due_at"] != due_at
                    or previous["reason_code"] != request.reason_code
                ):
                    raise ObligationIdempotencyConflict(
                        "Obligation correlation ID was reused with different contents."
                    )
                return _obligation(previous)
        correlation_id = request.correlation_id or f"obligation:{lead_id}:{request.obligation_type}"
        cursor = connection.execute(
            """
            INSERT INTO lead_obligations(
                lead_id, obligation_type, due_at, reason_code, correlation_id
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                lead_id,
                request.obligation_type,
                due_at,
                request.reason_code,
                correlation_id,
            ),
        )
        row = connection.execute(
            "SELECT * FROM lead_obligations WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    if row is None:
        raise RuntimeError("Lead obligation was not persisted.")
    return _obligation(row)


def list_obligations(lead_id: int) -> list[LeadObligation]:
    with _connect() as connection:
        _ensure_lead(connection, lead_id)
        rows = connection.execute(
            "SELECT * FROM lead_obligations WHERE lead_id = ? ORDER BY due_at, id",
            (lead_id,),
        ).fetchall()
    return [_obligation(row) for row in rows]


def list_overdue_obligations(*, as_of: datetime | None = None) -> list[LeadObligation]:
    current = (as_of or datetime.now(timezone.utc))
    if current.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    cutoff = current.astimezone(timezone.utc).isoformat()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT * FROM lead_obligations
            WHERE status = 'open' AND due_at < ?
            ORDER BY due_at, id
            """,
            (cutoff,),
        ).fetchall()
    return [_obligation(row) for row in rows]


def complete_obligation(obligation_id: int) -> LeadObligation:
    completed_at = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT * FROM lead_obligations WHERE id = ?", (obligation_id,)
        ).fetchone()
        if row is None:
            raise ObligationNotFound(f"Obligation {obligation_id} was not found.")
        if row["status"] == "cancelled":
            raise InvalidObligationTransition("Cancelled obligations cannot be completed.")
        if row["status"] == "open":
            connection.execute(
                """
                UPDATE lead_obligations
                SET status = 'completed', completed_at = ?
                WHERE id = ?
                """,
                (completed_at, obligation_id),
            )
        updated = connection.execute(
            "SELECT * FROM lead_obligations WHERE id = ?", (obligation_id,)
        ).fetchone()
    if updated is None:
        raise RuntimeError("Lead obligation update was not persisted.")
    return _obligation(updated)

def cancel_obligation(obligation_id: int) -> LeadObligation:
    """Idempotently cancel an open obligation without rewriting its history."""
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT * FROM lead_obligations WHERE id = ?", (obligation_id,)
        ).fetchone()
        if row is None:
            raise ObligationNotFound(f"Obligation {obligation_id} was not found.")
        if row["status"] == "completed":
            raise InvalidObligationTransition("Completed obligations cannot be cancelled.")
        if row["status"] == "open":
            connection.execute(
                "UPDATE lead_obligations SET status = 'cancelled' WHERE id = ?",
                (obligation_id,),
            )
        updated = connection.execute(
            "SELECT * FROM lead_obligations WHERE id = ?", (obligation_id,)
        ).fetchone()
    if updated is None:
        raise RuntimeError("Lead obligation cancellation was not persisted.")
    return _obligation(updated)
