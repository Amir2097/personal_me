"""OAuth2/OIDC client registration."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class OAuthClient(SQLModel, table=True):
    """Зарегистрированный OAuth2 клиент."""

    id: int | None = Field(default=None, primary_key=True)
    client_id: str = Field(index=True, unique=True, nullable=False)
    client_secret_hash: str = Field(nullable=False)
    name: str = Field(default="", nullable=False)
    redirect_uris: str = Field(default="", nullable=False)
    scopes: str = Field(default="openid profile", nullable=False)
    enabled: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
