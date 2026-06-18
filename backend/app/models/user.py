"""User model."""

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """Application user."""

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str | None = Field(default=None, index=True, unique=True)
    hashed_password: str = Field(nullable=False)
    is_admin: bool = Field(default=False, nullable=False)
