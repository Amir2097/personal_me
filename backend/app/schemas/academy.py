"""Schemas for billiards academy progress API."""

from datetime import datetime

from pydantic import BaseModel, Field


class AcademyProgressItem(BaseModel):
    exercise_id: str = Field(min_length=1, max_length=64)
    made: int = Field(ge=0)
    attempts: int = Field(ge=1)
    updated_at: datetime


class AcademyProgressUpsert(BaseModel):
    made: int = Field(ge=0)
    attempts: int = Field(ge=1)
    updated_at: datetime | None = None


class AcademyProgressBulkUpsert(BaseModel):
    """Merge client logs into the server copy (newer updated_at wins per exercise)."""

    items: list[AcademyProgressItem] = Field(default_factory=list)


class AcademyProgressListResponse(BaseModel):
    items: list[AcademyProgressItem]
