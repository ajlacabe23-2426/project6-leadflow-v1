from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse

from app.followup import generate_follow_up
from app.models import LeadCreate, LeadRecord
from app.scoring import qualify_lead
from app.storage import IdempotencyConflict, initialize_database, list_leads, save_lead


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="LeadFlow V1",
    version="1.0.0",
    description=(
        "Lead intake, deterministic qualification, follow-up drafting, "
        "and operator routing."
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


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(Path("static/index.html"))
