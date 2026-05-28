"""User model."""

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Application user."""

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)
