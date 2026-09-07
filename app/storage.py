from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.lifecycle import (
    InvalidLifecycleTransition,
    initial_state_for_intake,
    transition_reason_for_intake,
    validate_transition,
)
from app.models import (
    AuditEvent,
    CommunicationStatus,
    LeadCreate,
    LeadLifecycleState,
    LeadRecord,
    QualificationResult,
    SchedulingStatus,
)


DEFAULT_DB_PATH = "data/leadflow.db"


def _db_path() -> Path:
    return Path(os.getenv("LEADFLOW_DB_PATH", DEFAULT_DB_PATH))


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                lead_json TEXT NOT NULL,
                qualification_json TEXT NOT NULL,
                follow_up TEXT NOT NULL,
                fingerprint TEXT,
                communication_status TEXT NOT NULL DEFAULT 'suppressed-no-consent',
                scheduling_status TEXT NOT NULL DEFAULT 'not-ready',
                lifecycle_state TEXT NOT NULL DEFAULT 'received',
                audit_json TEXT NOT NULL DEFAULT '[]'
            )
            """
        )
        existing_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(leads)").fetchall()
        }
        migrations = {
            "fingerprint": "ALTER TABLE leads ADD COLUMN fingerprint TEXT",
            "communication_status": (
                "ALTER TABLE leads ADD COLUMN communication_status TEXT NOT NULL "
                "DEFAULT 'suppressed-no-consent'"
            ),
            "scheduling_status": (
                "ALTER TABLE leads ADD COLUMN scheduling_status TEXT NOT NULL "
                "DEFAULT 'not-ready'"
            ),
            "lifecycle_state": (
                "ALTER TABLE leads ADD COLUMN lifecycle_state TEXT NOT NULL "
                "DEFAULT 'received'"
            ),
            "audit_json": (
                "ALTER TABLE leads ADD COLUMN audit_json TEXT NOT NULL DEFAULT '[]'"
            ),
        }
        for column, statement in migrations.items():
            if column not in existing_columns:
                connection.execute(statement)
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_leads_fingerprint ON leads(fingerprint)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_leads_lifecycle_state ON leads(lifecycle_state)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS intake_requests (
                request_key TEXT PRIMARY KEY,
                request_hash TEXT NOT NULL,
                lead_id INTEGER NOT NULL REFERENCES leads(id)
            )
            """
        )


def _legacy_fingerprint(lead: LeadCreate) -> str:
    identity = "|".join(
        [str(lead.email).strip().lower(), lead.service.strip().lower(), lead.source.lower()]
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _fingerprint(lead: LeadCreate) -> str:
    payload = json.dumps(
        lead.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class IdempotencyConflict(ValueError):
    """A request key was reused with different validated input."""


class LeadNotFound(LookupError):
    """A requested lead record does not exist."""


def _communication_status(lead: LeadCreate) -> CommunicationStatus:
    if lead.opted_out:
        return "suppressed-opted-out"
    if not lead.communication_consent:
        return "suppressed-no-consent"
    return "draft-ready"


def _scheduling_status(qualification: QualificationResult) -> SchedulingStatus:
    if qualification.routing == "needs-info":
        return "blocked-missing-info"
    if qualification.next_action == "human-priority-review":
        return "pending-human-review"
    if qualification.next_action == "schedule-discovery":
        return "ready-to-schedule"
    return "not-ready"


def save_lead(
    lead: LeadCreate,
    qualification: QualificationResult,
    follow_up: str,
    request_key: str | None = None,
) -> LeadRecord:
    fingerprint = _fingerprint(lead)
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        if request_key is not None:
            previous = connection.execute(
                "SELECT request_hash, lead_id FROM intake_requests WHERE request_key = ?",
                (request_key,),
            ).fetchone()
            if previous is not None:
                if previous["request_hash"] != fingerprint:
                    raise IdempotencyConflict(
                        "Idempotency key already used for different input."
                    )
                row = connection.execute(
                    "SELECT * FROM leads WHERE id = ?", (previous["lead_id"],)
                ).fetchone()
                if row is None:
                    raise RuntimeError("Idempotent intake record is unavailable.")
                return _row_to_record(row)
        else:
            candidates = connection.execute(
                """
                SELECT * FROM leads
                WHERE fingerprint IN (?, ?) AND created_at >= datetime('now', '-24 hours')
                ORDER BY id DESC
                """,
                (fingerprint, _legacy_fingerprint(lead)),
            ).fetchall()
            for candidate in candidates:
                record = _row_to_record(candidate)
                if _fingerprint(record.lead) == fingerprint:
                    return record

        communication_status = _communication_status(lead)
        scheduling_status = _scheduling_status(qualification)
        lifecycle_state = initial_state_for_intake(lead, qualification)
        validate_transition("received", lifecycle_state)
        transition_reason = transition_reason_for_intake(lead, qualification)
        correlation_id = request_key or f"intake:{fingerprint[:16]}"
        now = connection.execute("SELECT CURRENT_TIMESTAMP").fetchone()[0]
        audit_history = [
            AuditEvent(
                event_type="lead.received",
                detail="Validated intake accepted",
                occurred_at=now,
            ),
            AuditEvent(
                event_type="lead.qualified",
                detail=(
                    f"Deterministic score={qualification.score}; "
                    f"route={qualification.routing}; priority={qualification.priority}; "
                    f"lifecycle={lifecycle_state}"
                ),
                occurred_at=now,
                from_state="received",
                to_state=lifecycle_state,
                reason_code=transition_reason,
                correlation_id=correlation_id,
            ),
            AuditEvent(
                event_type="followup.drafted",
                detail=f"Communication status={communication_status}; no message sent",
                occurred_at=now,
            ),
            AuditEvent(
                event_type="scheduling.routed",
                detail=f"Scheduling status={scheduling_status}; no appointment created",
                occurred_at=now,
            ),
        ]
        cursor = connection.execute(
            """
            INSERT INTO leads (
                lead_json, qualification_json, follow_up, fingerprint,
                communication_status, scheduling_status, lifecycle_state, audit_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead.model_dump_json(),
                qualification.model_dump_json(),
                follow_up,
                fingerprint,
                communication_status,
                scheduling_status,
                lifecycle_state,
                json.dumps([event.model_dump() for event in audit_history]),
            ),
        )
        row = connection.execute(
            "SELECT * FROM leads WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        if request_key is not None:
            connection.execute(
                "INSERT INTO intake_requests (request_key, request_hash, lead_id) VALUES (?, ?, ?)",
                (request_key, fingerprint, cursor.lastrowid),
            )

    if row is None:
        raise RuntimeError("Lead was not persisted.")
    return _row_to_record(row)


def transition_lead(
    lead_id: int,
    to_state: LeadLifecycleState,
    reason_code: str,
    correlation_id: str | None = None,
) -> LeadRecord:
    """Atomically validate, persist, and audit one lifecycle transition."""
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
        if row is None:
            raise LeadNotFound(f"Lead {lead_id} was not found.")

        record = _row_to_record(row)
        from_state = record.lifecycle_state
        if not validate_transition(from_state, to_state):
            return record

        now = connection.execute("SELECT CURRENT_TIMESTAMP").fetchone()[0]
        event = AuditEvent(
            event_type="lifecycle.transition",
            detail=f"Lifecycle transition {from_state} -> {to_state}",
            occurred_at=now,
            from_state=from_state,
            to_state=to_state,
            reason_code=reason_code,
            correlation_id=correlation_id or f"transition:{lead_id}:{len(record.audit_history) + 1}",
        )
        updated_history = [*record.audit_history, event]
        connection.execute(
            "UPDATE leads SET lifecycle_state = ?, audit_json = ? WHERE id = ?",
            (
                to_state,
                json.dumps([item.model_dump() for item in updated_history]),
                lead_id,
            ),
        )
        updated = connection.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()

    if updated is None:
        raise RuntimeError("Lead transition was not persisted.")
    return _row_to_record(updated)


def list_leads() -> list[LeadRecord]:
    with _connect() as connection:
        rows = connection.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
    return [_row_to_record(row) for row in rows]


def _row_to_record(row: sqlite3.Row) -> LeadRecord:
    return LeadRecord(
        id=row["id"],
        created_at=row["created_at"],
        lead=LeadCreate.model_validate(json.loads(row["lead_json"])),
        qualification=QualificationResult.model_validate(
            json.loads(row["qualification_json"])
        ),
        follow_up=row["follow_up"],
        communication_status=row["communication_status"],
        scheduling_status=row["scheduling_status"],
        lifecycle_state=row["lifecycle_state"],
        audit_history=[
            AuditEvent.model_validate(event) for event in json.loads(row["audit_json"])
        ],
    )


__all__ = [
    "IdempotencyConflict",
    "InvalidLifecycleTransition",
    "LeadNotFound",
    "initialize_database",
    "list_leads",
    "save_lead",
    "transition_lead",
]
