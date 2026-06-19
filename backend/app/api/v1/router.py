"""Versioned API router."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.oidc import router as oidc_router
from app.api.v1.projects import router as projects_router
from app.api.v1.site import router as site_router
from app.api.v1.contacts import router as contacts_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.terminal import router as terminal_router
from app.api.v1.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(integrations_router)
api_router.include_router(projects_router)
api_router.include_router(oidc_router)
api_router.include_router(site_router)
api_router.include_router(contacts_router)
api_router.include_router(feedback_router)
api_router.include_router(terminal_router)
api_router.include_router(users_router)
