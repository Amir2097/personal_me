"""FastAPI application entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.api.v1.router import api_router
from app.core import db
from app.core.config import settings
from app.services.auth_service import ensure_initial_admin


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize and clean up application resources."""
    db.create_db_and_tables()
    with Session(db.engine) as session:
        ensure_initial_admin(session)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Terminal/IDE style developer hub backend API.",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Health check", description="Simple health check endpoint.")
def healthcheck() -> dict[str, str]:
    """Return service status."""
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.api_v1_prefix)
