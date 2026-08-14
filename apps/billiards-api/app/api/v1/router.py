"""Цифровое Сукно API router."""

from fastapi import APIRouter

from app.api.v1.academy import router as academy_router
from app.api.v1.auth import router as auth_router
from app.api.v1.cup import router as cup_router
from app.api.v1.kolkhoz import router as kolkhoz_router
from app.api.v1.site import router as site_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(site_router)
api_router.include_router(kolkhoz_router)
api_router.include_router(cup_router)
api_router.include_router(academy_router)
