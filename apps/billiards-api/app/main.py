"""Цифровое Сукно backend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from app.api.v1.router import api_router
from app.core import db
from app.core.config import settings
from app.services.auth_service import ensure_initial_admin


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    db.create_db_and_tables()
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    with Session(db.engine) as session:
        ensure_initial_admin(session)
    yield


app = FastAPI(
    title=settings.app_name,
    description="API сервиса Цифровое Сукно: колхоз, турнир, академия, табло.",
    version="0.1.0",
    docs_url="/api/sukno/docs",
    openapi_url="/api/sukno/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Health check")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "sukno"}


app.include_router(api_router, prefix=settings.api_v1_prefix)

uploads_root = Path(settings.uploads_dir)
uploads_root.mkdir(parents=True, exist_ok=True)
app.mount(
    f"{settings.api_v1_prefix}/billiards/uploads",
    StaticFiles(directory=str(uploads_root)),
    name="uploads",
)
