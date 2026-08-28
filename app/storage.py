from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from app.models import LeadCreate, LeadRecord, QualificationResult


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
                follow_up TEXT NOT NULL
            )
            """
        )


def save_lead(
    lead: LeadCreate,
    qualification: QualificationResult,
    follow_up: str,
) -> LeadRecord:
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO leads (lead_json, qualification_json, follow_up)
            VALUES (?, ?, ?)
            """,
            (
                lead.model_dump_json(),
                qualification.model_dump_json(),
                follow_up,
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
    )
