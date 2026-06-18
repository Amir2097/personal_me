"""OAuth2 authorization code."""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class OAuthAuthorizationCode(SQLModel, table=True):
    """Одноразовый authorization code (OIDC code flow)."""

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True, nullable=False)
    client_id: str = Field(index=True, nullable=False)
    username: str = Field(index=True, nullable=False)
    redirect_uri: str = Field(nullable=False)
    scope: str = Field(default="openid profile", nullable=False)
    nonce: str = Field(default="", nullable=False)
    code_challenge: str = Field(default="", nullable=False)
    code_challenge_method: str = Field(default="", nullable=False)
    expires_at: datetime = Field(nullable=False)
    used: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
