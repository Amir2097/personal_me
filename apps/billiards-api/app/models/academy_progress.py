"""Per-user academy exercise progress."""

from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class AcademyProgress(SQLModel, table=True):
    """Результат тренировки по одному упражнению академии."""

    __table_args__ = (
        UniqueConstraint("owner_username", "exercise_id", name="uq_academy_progress_owner_exercise"),
    )

    id: int | None = Field(default=None, primary_key=True)
    owner_username: str = Field(index=True, nullable=False)
    exercise_id: str = Field(index=True, max_length=64, nullable=False)
    made: int = Field(default=0, nullable=False)
    attempts: int = Field(default=1, nullable=False)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
