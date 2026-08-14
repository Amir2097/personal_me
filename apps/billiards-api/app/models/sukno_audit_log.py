"""Audit trail rows for admin actions."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class SuknoAuditLog(SQLModel, table=True):
    __tablename__ = "sukno_audit_log"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    actor_username: str = Field(index=True, nullable=False)
    action: str = Field(index=True, nullable=False)
    target: str = Field(default="", index=True, nullable=False)
    details_json: str = Field(default="{}", nullable=False)
