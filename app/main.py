from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.followup import generate_follow_up
from app.models import LeadCreate, LeadRecord
from app.scoring import qualify_lead
from app.storage import initialize_database, list_leads, save_lead


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "project6-leadflow"}


@app.post("/api/leads", response_model=LeadRecord, status_code=201)
def create_lead(lead: LeadCreate) -> LeadRecord:
    qualification = qualify_lead(lead)
    follow_up = generate_follow_up(lead, qualification)
    return save_lead(lead, qualification, follow_up)


@app.get("/api/leads", response_model=list[LeadRecord])
def get_leads() -> list[LeadRecord]:
    return list_leads()


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(Path("static/index.html"))
