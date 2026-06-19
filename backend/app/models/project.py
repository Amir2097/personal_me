"""Portfolio project model."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    """Проект в портфолио."""

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True, nullable=False)
    title: str = Field(nullable=False)
    summary: str = Field(default="", nullable=False)
    description: str = Field(default="", nullable=False)
    tech_stack: str = Field(default="", nullable=False)
    github_url: str = Field(default="", nullable=False)
    demo_url: str = Field(default="", nullable=False)
    image_url: str = Field(default="", nullable=False)
    gallery_urls: str = Field(default="", nullable=False)
    is_public: bool = Field(default=True, nullable=False)
    featured: bool = Field(default=False, nullable=False)
    sort_order: int = Field(default=0, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
