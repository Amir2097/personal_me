"""OIDC / OAuth2 provider endpoints."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.api.deps import (
    get_current_admin_user,
    get_current_username,
    get_current_username_from_token,
    get_optional_access_token,
)
from app.core.config import settings
from app.core.db import get_session
from app.core.oidc_keys import get_oidc_public_jwks
from app.models.user import User
from app.schemas.oidc import (
    AuthorizeApproveRequest,
    AuthorizeApproveResponse,
    OAuthClientCreate,
    OAuthClientRead,
    OidcTokenResponse,
    UserInfoResponse,
)
from app.services.oidc_service import (
    _redirect_uris_list,
    authenticate_client,
    build_authorize_redirect_url,
    build_discovery_document,
    create_oauth_client,
    delete_oauth_client,
    exchange_authorization_code,
    get_userinfo,
    list_oauth_clients,
)

router = APIRouter(prefix="/oidc", tags=["oidc"])


def _client_to_read(item) -> OAuthClientRead:
    return OAuthClientRead(
        id=item.id,
        client_id=item.client_id,
        name=item.name,
        redirect_uris=_redirect_uris_list(item.redirect_uris),
        scopes=item.scopes,
        enabled=item.enabled,
    )


@router.get("/.well-known/openid-configuration")
def openid_configuration() -> dict:
    """OIDC Discovery."""
    return build_discovery_document()


@router.get("/jwks")
def jwks() -> dict:
    """JSON Web Key Set."""
    return get_oidc_public_jwks()


@router.get("/authorize")
def authorize(
    request: Request,
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: str = "openid profile",
    state: str = "",
    nonce: str = "",
    code_challenge: str = "",
    code_challenge_method: str = "",
    session: Session = Depends(get_session),
    token: str | None = Depends(get_optional_access_token),
):
    """OAuth2 authorize — редирект на consent UI или login."""
    if response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживается только response_type=code.",
        )

    params = request.url.query
    if not token:
        login_url = f"{settings.oidc_frontend_base_url.rstrip('/')}/oauth/authorize?{params}"
        return RedirectResponse(login_url, status_code=302)

    if settings.oidc_auto_approve:
        username = get_current_username_from_token(token)
        redirect_to = build_authorize_redirect_url(
            session,
            username=username,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            nonce=nonce,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
        )
        return RedirectResponse(redirect_to, status_code=302)

    consent_url = f"{settings.oidc_frontend_base_url.rstrip('/')}/oauth/authorize?{params}"
    return RedirectResponse(consent_url, status_code=302)


@router.post("/authorize/approve", response_model=AuthorizeApproveResponse)
def authorize_approve(
    payload: AuthorizeApproveRequest,
    session: Session = Depends(get_session),
    username: str = Depends(get_current_username),
) -> AuthorizeApproveResponse:
    """Подтвердить доступ приложения (consent)."""
    redirect_to = build_authorize_redirect_url(
        session,
        username=username,
        client_id=payload.client_id,
        redirect_uri=payload.redirect_uri,
        scope=payload.scope,
        state=payload.state,
        nonce=payload.nonce,
        code_challenge=payload.code_challenge,
        code_challenge_method=payload.code_challenge_method,
    )
    return AuthorizeApproveResponse(redirect_to=redirect_to)


@router.post("/token", response_model=OidcTokenResponse)
def token(
    grant_type: str = Form(...),
    code: str | None = Form(None),
    redirect_uri: str | None = Form(None),
    client_id: str | None = Form(None),
    client_secret: str | None = Form(None),
    code_verifier: str | None = Form(None),
    session: Session = Depends(get_session),
) -> OidcTokenResponse:
    """OAuth2 token endpoint."""
    if grant_type != "authorization_code":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported grant_type.")
    if not code or not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="code и redirect_uri обязательны.",
        )

    client = authenticate_client(session, client_id, client_secret)
    return exchange_authorization_code(
        session,
        client=client,
        code=code,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
    )


@router.get("/userinfo", response_model=UserInfoResponse)
def userinfo(
    token: str | None = Depends(get_optional_access_token),
    session: Session = Depends(get_session),
) -> UserInfoResponse:
    """OIDC UserInfo."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return get_userinfo(session, token)


@router.get("/clients", response_model=list[OAuthClientRead])
def get_clients(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> list[OAuthClientRead]:
    """Список OAuth клиентов (admin)."""
    return [_client_to_read(item) for item in list_oauth_clients(session)]


@router.post("/clients", response_model=OAuthClientRead, status_code=201)
def post_client(
    payload: OAuthClientCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> OAuthClientRead:
    """Создать OAuth клиент."""
    return _client_to_read(create_oauth_client(session, payload))


@router.delete("/clients/{client_db_id}", status_code=204)
def remove_client(
    client_db_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> None:
    """Удалить OAuth клиент."""
    delete_oauth_client(session, client_db_id)
