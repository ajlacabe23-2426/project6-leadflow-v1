from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3

from app.models import OutboundAction, OutboundActionRequest, OutboundActionResultRequest
from app.storage import LeadNotFound, _connect


class OutboxIdempotencyConflict(ValueError):
    """An action key was reused for a different logical action."""


class OutboundActionPolicyBlocked(ValueError):
    """Lead state or consent does not authorize creation of this action."""


class OutboundActionNotFound(LookupError):
    """Requested outbound action does not exist."""


class InvalidOutboundActionTransition(ValueError):
    """Requested outbox state change is not valid."""


def _row_to_action(row: sqlite3.Row) -> OutboundAction:
    return OutboundAction(
        id=row["id"],
        lead_id=row["lead_id"],
        action_key=row["action_key"],
        action_type=row["action_type"],
        status=row["status"],
        attempts=row["attempts"],
        max_attempts=row["max_attempts"],
        next_attempt_at=row["next_attempt_at"],
        last_error_code=row["last_error_code"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _utc_sql(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("outbox time must be timezone-aware")
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def enqueue_outbound_action(lead_id: int, request: OutboundActionRequest) -> OutboundAction:
    """Persist an action intent only. This function never contacts a provider."""
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        lead = connection.execute(
            "SELECT communication_status, lifecycle_state FROM leads WHERE id = ?",
            (lead_id,),
        ).fetchone()
        if lead is None:
            raise LeadNotFound(f"Lead {lead_id} was not found.")

        if request.action_type == "follow-up-email":
            if lead["communication_status"] != "draft-ready" or lead["lifecycle_state"] in {"closed", "suppressed"}:
                raise OutboundActionPolicyBlocked(
                    "Lead is not currently eligible for a follow-up communication action."
                )
        elif request.action_type == "schedule-discovery":
            if lead["lifecycle_state"] != "ready-to-schedule":
                raise OutboundActionPolicyBlocked(
                    "Lead must be in ready-to-schedule before a scheduling action is queued."
                )

        previous = connection.execute(
            "SELECT * FROM outbound_actions WHERE action_key = ?", (request.action_key,)
        ).fetchone()
        if previous is not None:
            if (
                previous["lead_id"] != lead_id
                or previous["action_type"] != request.action_type
                or previous["max_attempts"] != request.max_attempts
            ):
                raise OutboxIdempotencyConflict(
                    "Action key already belongs to a different outbound action."
                )
            return _row_to_action(previous)

        cursor = connection.execute(
            """
            INSERT INTO outbound_actions (lead_id, action_key, action_type, max_attempts)
            VALUES (?, ?, ?, ?)
            """,
            (lead_id, request.action_key, request.action_type, request.max_attempts),
        )
        row = connection.execute(
            "SELECT * FROM outbound_actions WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()

    if row is None:
        raise RuntimeError("Outbound action was not persisted.")
    return _row_to_action(row)


def list_outbound_actions() -> list[OutboundAction]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM outbound_actions ORDER BY id"
        ).fetchall()
    return [_row_to_action(row) for row in rows]


def claim_next_outbound_action(now: datetime | None = None) -> OutboundAction | None:
    """Atomically claim one due action for a future provider adapter."""
    current = now or datetime.now(timezone.utc)
    current_sql = _utc_sql(current)
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """
            SELECT * FROM outbound_actions
            WHERE status = 'queued'
               OR (status = 'retry-wait' AND next_attempt_at <= ?)
            ORDER BY id
            LIMIT 1
            """,
            (current_sql,),
        ).fetchone()
        if row is None:
            return None
        connection.execute(
            """
            UPDATE outbound_actions
            SET status = 'in-progress', attempts = attempts + 1,
                next_attempt_at = NULL, updated_at = ?
            WHERE id = ?
            """,
            (current_sql, row["id"]),
        )
        claimed = connection.execute(
            "SELECT * FROM outbound_actions WHERE id = ?", (row["id"],)
        ).fetchone()
    return _row_to_action(claimed)


def record_outbound_result(
    action_id: int,
    result: OutboundActionResultRequest,
    now: datetime | None = None,
) -> OutboundAction:
    current = now or datetime.now(timezone.utc)
    current_sql = _utc_sql(current)
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT * FROM outbound_actions WHERE id = ?", (action_id,)
        ).fetchone()
        if row is None:
            raise OutboundActionNotFound(f"Outbound action {action_id} was not found.")
        if row["status"] != "in-progress":
            raise InvalidOutboundActionTransition(
                "Only an in-progress action may record a provider result."
            )

        if result.success:
            status, next_attempt_at, error_code = "succeeded", None, None
        elif result.retryable and row["attempts"] < row["max_attempts"]:
            backoff_seconds = min(3600, 60 * (5 ** max(0, row["attempts"] - 1)))
            status = "retry-wait"
            next_attempt_at = _utc_sql(current + timedelta(seconds=backoff_seconds))
            error_code = result.error_code
        else:
            status, next_attempt_at, error_code = "dead-letter", None, result.error_code

        connection.execute(
            """
            UPDATE outbound_actions
            SET status = ?, next_attempt_at = ?, last_error_code = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, next_attempt_at, error_code, current_sql, action_id),
        )
        updated = connection.execute(
            "SELECT * FROM outbound_actions WHERE id = ?", (action_id,)
        ).fetchone()
    return _row_to_action(updated)


def cancel_outbound_action(action_id: int, now: datetime | None = None) -> OutboundAction:
    current_sql = _utc_sql(now or datetime.now(timezone.utc))
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT * FROM outbound_actions WHERE id = ?", (action_id,)
        ).fetchone()
        if row is None:
            raise OutboundActionNotFound(f"Outbound action {action_id} was not found.")
        if row["status"] not in {"queued", "retry-wait"}:
            raise InvalidOutboundActionTransition(
                "Only queued or retry-wait actions may be cancelled."
            )
        connection.execute(
            """
            UPDATE outbound_actions
            SET status = 'cancelled', next_attempt_at = NULL, updated_at = ?
            WHERE id = ?
            """,
            (current_sql, action_id),
        )
        updated = connection.execute(
            "SELECT * FROM outbound_actions WHERE id = ?", (action_id,)
        ).fetchone()
    return _row_to_action(updated)
