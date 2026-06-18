"""OIDC API schemas."""

from pydantic import BaseModel, Field


class OAuthClientCreate(BaseModel):
    """Создание OAuth клиента."""

    client_id: str = Field(min_length=3, max_length=64)
    client_secret: str = Field(min_length=8, max_length=128)
    name: str = ""
    redirect_uris: list[str] = Field(min_length=1)
    scopes: str = "openid profile"


class OAuthClientRead(BaseModel):
    """OAuth клиент в ответе API."""

    id: int
    client_id: str
    name: str
    redirect_uris: list[str]
    scopes: str
    enabled: bool


class AuthorizeApproveRequest(BaseModel):
    """Подтверждение OIDC authorize."""

    client_id: str
    redirect_uri: str
    scope: str = "openid profile"
    state: str = ""
    nonce: str = ""
    code_challenge: str = ""
    code_challenge_method: str = ""


class AuthorizeApproveResponse(BaseModel):
    """URL для редиректа после approve."""

    redirect_to: str


class TokenRequest(BaseModel):
    """OAuth2 token endpoint (form fields)."""

    grant_type: str
    code: str | None = None
    redirect_uri: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    code_verifier: str | None = None


class OidcTokenResponse(BaseModel):
    """Ответ token endpoint."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    id_token: str
    scope: str


class UserInfoResponse(BaseModel):
    """OIDC userinfo."""

    sub: str
    preferred_username: str
    is_admin: bool = False
