"""Alembic migration environment for Цифровое Сукно API."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from app.core.config import settings
from app.models.academy_progress import AcademyProgress  # noqa: F401
from app.models.cup_session import CupSession  # noqa: F401
from app.models.cup_tournament import CupTournament  # noqa: F401
from app.models.kolkhoz_game import KolkhozGame  # noqa: F401
from app.models.kolkhoz_session import KolkhozSession  # noqa: F401
from app.models.sukno_audit_log import SuknoAuditLog  # noqa: F401
from app.models.sukno_email_verification_token import SuknoEmailVerificationToken  # noqa: F401
from app.models.sukno_password_reset_token import SuknoPasswordResetToken  # noqa: F401
from app.models.sukno_refresh_token import SuknoRefreshToken  # noqa: F401
from app.models.sukno_site_settings import SuknoSiteSettings  # noqa: F401
from app.models.sukno_user import SuknoUser  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.postgres_dsn)
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
