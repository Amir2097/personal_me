"""Alembic migration environment."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from app.core.config import settings
from app.models.contact_channel import ContactChannel  # noqa: F401
from app.models.site_settings import SiteSettings  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.integration import Integration  # noqa: F401
from app.models.oauth_authorization_code import OAuthAuthorizationCode  # noqa: F401
from app.models.oauth_client import OAuthClient  # noqa: F401
from app.models.password_reset_token import PasswordResetToken  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.sso_code import SsoCode  # noqa: F401
from app.models.user import User  # noqa: F401

# Tables owned by apps/billiards-api (shared Postgres in full compose).
# Keep historical migrations 013–016; do not let hub autogenerate drop them.
SUKNO_OWNED_TABLES = frozenset(
    {
        "kolkhozsession",
        "kolkhozgame",
        "academyprogress",
        "cupsession",
        "cuptournament",
        "sukno_user",
        "sukno_refresh_token",
        "sukno_password_reset_token",
        "sukno_email_verification_token",
        "sukno_site_settings",
        "sukno_audit_log",
    }
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.postgres_dsn)
target_metadata = SQLModel.metadata


def include_object(object_, name, type_, reflected, compare_to):  # noqa: ANN001, ARG001
    """Skip Цифровое Сукно tables when comparing metadata."""
    if type_ == "table" and name in SUKNO_OWNED_TABLES:
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
