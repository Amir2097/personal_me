"""Contact channel DTOs."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ContactKind = Literal["link", "email", "text"]


class ContactRead(BaseModel):
    id: int
    key: str
    label: str
    value: str
    kind: ContactKind
    enabled: bool
    sort_order: int
    href: str | None = None
    created_at: datetime


class ContactCreate(BaseModel):
    key: str = Field(min_length=1, max_length=64)
    label: str = ""
    value: str = Field(min_length=1)
    kind: ContactKind = "link"
    enabled: bool = True
    sort_order: int = 0


class ContactUpdate(BaseModel):
    label: str | None = None
    value: str | None = None
    kind: ContactKind | None = None
    enabled: bool | None = None
    sort_order: int | None = None
