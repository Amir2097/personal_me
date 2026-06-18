"""Database migration runner."""

from pathlib import Path

from alembic import command
from alembic.config import Config


def _backend_root() -> Path:
    """Корень backend (где лежат alembic.ini и alembic/)."""
    return Path(__file__).resolve().parents[2]


def run_migrations() -> None:
    """Apply Alembic migrations up to head."""
    root = _backend_root()
    alembic_ini = root / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("script_location", str(root / "alembic"))
    command.upgrade(alembic_cfg, "head")
