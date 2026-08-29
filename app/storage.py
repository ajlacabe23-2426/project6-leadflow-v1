from __future__ import annotations

import json
import hashlib
import os
import sqlite3
from pathlib import Path

from app.models import (
    AuditEvent,
    CommunicationStatus,
    LeadCreate,
    LeadRecord,
    QualificationResult,
    SchedulingStatus,
)


DEFAULT_DB_PATH = "data/leadflow.db"


def _db_path() -> Path:
    return Path(os.getenv("LEADFLOW_DB_PATH", DEFAULT_DB_PATH))


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with _connect() as connection:
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


def _fingerprint(lead: LeadCreate) -> str:
    identity = "|".join(
        [str(lead.email).strip().lower(), lead.service.strip().lower(), lead.source.lower()]
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


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
) -> LeadRecord:
    fingerprint = _fingerprint(lead)
    with _connect() as connection:
        duplicate = connection.execute(
            """
            SELECT * FROM leads
            WHERE fingerprint = ? AND created_at >= datetime('now', '-24 hours')
            ORDER BY id DESC LIMIT 1
            """,
            (fingerprint,),
        ).fetchone()
        if duplicate is not None:
            return _row_to_record(duplicate)

        communication_status = _communication_status(lead)
        scheduling_status = _scheduling_status(qualification)
        now = connection.execute("SELECT CURRENT_TIMESTAMP").fetchone()[0]
        audit_history = [
            AuditEvent(event_type="lead.received", detail="Validated intake accepted", occurred_at=now),
            AuditEvent(
                event_type="lead.qualified",
                detail=(
                    f"Deterministic score={qualification.score}; "
                    f"route={qualification.routing}; priority={qualification.priority}"
                ),
                occurred_at=now,
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
                communication_status, scheduling_status, audit_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead.model_dump_json(),
                qualification.model_dump_json(),
                follow_up,
                fingerprint,
                communication_status,
                scheduling_status,
                json.dumps([event.model_dump() for event in audit_history]),
            ),
        )
        row = connection.execute(
            "SELECT * FROM leads WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    if row is None:
        raise RuntimeError("Lead was not persisted.")

    return _row_to_record(row)


def list_leads() -> list[LeadRecord]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM leads ORDER BY id DESC"
        ).fetchall()
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
        audit_history=[
            AuditEvent.model_validate(event)
            for event in json.loads(row["audit_json"])
        ],
    )
