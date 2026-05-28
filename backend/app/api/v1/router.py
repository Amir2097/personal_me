"""Versioned API router."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.terminal import router as terminal_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(terminal_router)
