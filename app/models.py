from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class LeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    source: str = Field(default="website", min_length=2, max_length=80)
    service: str = Field(min_length=2, max_length=160)
    estimated_value: float | None = Field(default=None, ge=0)
    timeline_days: int | None = Field(default=None, ge=1, le=3650)
    budget_confirmed: bool = False
    decision_maker: bool = False
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("name", "source", "service", mode="before")
    @classmethod
    def normalize_required_text(cls, value: object) -> object:
        if isinstance(value, str):
            return " ".join(value.split())
        return value

    @field_validator("phone", "notes", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = " ".join(value.split())
            return normalized or None
        return value


LeadRoute = Literal["qualified", "nurture", "needs-info"]
LeadPriority = Literal["high", "medium", "low"]


class QualificationResult(BaseModel):
    score: int = Field(ge=0, le=100)
    routing: LeadRoute
    priority: LeadPriority
    next_action: str
    breakdown: dict[str, int]
    missing_information: list[str]


class LeadRecord(BaseModel):
    id: int
    created_at: str
    lead: LeadCreate
    qualification: QualificationResult
    follow_up: str
