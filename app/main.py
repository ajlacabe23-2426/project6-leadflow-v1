from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from app.followup import generate_follow_up
from app.lifecycle import InvalidLifecycleTransition
from app.models import (
    LeadCreate,
    LeadRecord,
    LifecycleTransitionRequest,
    OutboundAction,
    OutboundActionRequest,
    OutboundActionResultRequest,
)
from app.scoring import qualify_lead
from app.outbox import (
    InvalidOutboundActionTransition,
    OutboundActionNotFound,
    OutboundActionPolicyBlocked,
    OutboxIdempotencyConflict,
    cancel_outbound_action,
    claim_next_outbound_action,
    enqueue_outbound_action,
    list_outbound_actions,
    record_outbound_result,
)
from app.operations import (
    LeadAssignment,
    LeadAssignmentRequest,
    LeadObligation,
    LeadObligationRequest,
    ObligationNotFound,
    InvalidObligationTransition,
    assign_lead,
    cancel_obligation,
    complete_obligation,
    create_obligation,
    initialize_operations_tables,
    list_assignments,
    list_obligations,
    list_overdue_obligations,
)
from app.storage import (
    IdempotencyConflict,
    LeadNotFound,
    initialize_database,
    list_leads,
    save_lead,
    transition_lead,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    initialize_operations_tables()
    yield


app = FastAPI(
    title="LeadFlow V1",
    version="1.2.0",
    description=(
        "Lead intake, deterministic qualification, auditable lifecycle control, "
        "follow-up drafting, and operator routing."
    ),
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request, error: RequestValidationError) -> JSONResponse:
    # Never echo raw input (PII or non-finite floats) into the JSON error response.
    details = [
        {key: item[key] for key in ("loc", "msg", "type")}
        for item in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": details})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "project6-leadflow"}


@app.post("/api/leads", response_model=LeadRecord, status_code=201)
def create_lead(
    lead: LeadCreate,
    idempotency_key: Annotated[
        str | None, Header(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    ] = None,
) -> LeadRecord:
    qualification = qualify_lead(lead)
    follow_up = generate_follow_up(lead, qualification)
    try:
        return save_lead(lead, qualification, follow_up, request_key=idempotency_key)
    except IdempotencyConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/api/leads", response_model=list[LeadRecord])
def get_leads() -> list[LeadRecord]:
    return list_leads()


@app.patch("/api/leads/{lead_id}/state", response_model=LeadRecord)
def change_lead_state(
    lead_id: int, request: LifecycleTransitionRequest
) -> LeadRecord:
    try:
        return transition_lead(
            lead_id=lead_id,
            to_state=request.to_state,
            reason_code=request.reason_code,
            correlation_id=request.correlation_id,
        )
    except LeadNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidLifecycleTransition as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post("/api/leads/{lead_id}/assignments", response_model=LeadAssignment, status_code=201)
def create_lead_assignment(
    lead_id: int, request: LeadAssignmentRequest
) -> LeadAssignment:
    try:
        return assign_lead(lead_id, request)
    except LeadNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/leads/{lead_id}/assignments", response_model=list[LeadAssignment])
def get_lead_assignments(lead_id: int) -> list[LeadAssignment]:
    try:
        return list_assignments(lead_id)
    except LeadNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/api/leads/{lead_id}/obligations", response_model=LeadObligation, status_code=201)
def create_lead_obligation(
    lead_id: int, request: LeadObligationRequest
) -> LeadObligation:
    try:
        return create_obligation(lead_id, request)
    except LeadNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/leads/{lead_id}/obligations", response_model=list[LeadObligation])
def get_lead_obligations(lead_id: int) -> list[LeadObligation]:
    try:
        return list_obligations(lead_id)
    except LeadNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/obligations/overdue", response_model=list[LeadObligation])
def get_overdue_obligations() -> list[LeadObligation]:
    return list_overdue_obligations()


@app.patch("/api/obligations/{obligation_id}/complete", response_model=LeadObligation)
def mark_obligation_complete(obligation_id: int) -> LeadObligation:
    try:
        return complete_obligation(obligation_id)
    except ObligationNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.patch("/api/obligations/{obligation_id}/cancel", response_model=LeadObligation)
def mark_obligation_cancelled(obligation_id: int) -> LeadObligation:
    try:
        return cancel_obligation(obligation_id)
    except ObligationNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidObligationTransition as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post("/api/leads/{lead_id}/actions", response_model=OutboundAction, status_code=201)
def queue_outbound_action(lead_id: int, request: OutboundActionRequest) -> OutboundAction:
    """Queue an action intent only; no provider call occurs in Project 6 V1."""
    try:
        return enqueue_outbound_action(lead_id, request)
    except LeadNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (OutboundActionPolicyBlocked, OutboxIdempotencyConflict) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/api/outbox", response_model=list[OutboundAction])
def get_outbox() -> list[OutboundAction]:
    return list_outbound_actions()


@app.post("/api/outbox/claim", response_model=OutboundAction | None)
def claim_outbox_action() -> OutboundAction | None:
    """Local reliability-lab claim endpoint; it does not send email or book anything."""
    return claim_next_outbound_action()


@app.patch("/api/outbox/{action_id}/result", response_model=OutboundAction)
def complete_outbox_action(
    action_id: int, request: OutboundActionResultRequest
) -> OutboundAction:
    try:
        return record_outbound_result(action_id, request)
    except OutboundActionNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidOutboundActionTransition as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post("/api/outbox/{action_id}/cancel", response_model=OutboundAction)
def cancel_outbox_action(action_id: int) -> OutboundAction:
    try:
        return cancel_outbound_action(action_id)
    except OutboundActionNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidOutboundActionTransition as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(Path("static/index.html"))
