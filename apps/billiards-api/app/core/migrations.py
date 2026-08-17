"""Database migration runner for Цифровое Сукно API."""

from pathlib import Path

from alembic import command
from alembic.config import Config


def _api_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_migrations() -> None:
    """Apply Alembic migrations up to head."""
    root = _api_root()
    alembic_ini = root / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("script_location", str(root / "alembic"))
    command.upgrade(alembic_cfg, "head")
