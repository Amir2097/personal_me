"""FastAPI application entrypoint."""

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from sqlmodel import Session

from app.api.v1.router import api_router
from app.core import db
from app.core.config import settings
from app.core.migrations import run_migrations
from app.services.auth_service import ensure_initial_admin
from app.services.integration_service import ensure_default_integrations
from app.services.oidc_service import ensure_default_oauth_client


def initialize_database(max_retries: int = 30, delay_seconds: float = 1.0) -> None:
    """Run migrations and seed data, retrying until PostgreSQL is ready."""
    for attempt in range(max_retries):
        try:
            run_migrations()
            with Session(db.engine) as session:
                ensure_initial_admin(session)
                ensure_default_integrations(session)
                ensure_default_projects(session)
                ensure_default_oauth_client(session)
            return
        except OperationalError:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize and clean up application resources."""
    initialize_database()
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
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Health check", description="Simple health check endpoint.")
def healthcheck() -> dict[str, str]:
    """Return service status."""
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.api_v1_prefix)
