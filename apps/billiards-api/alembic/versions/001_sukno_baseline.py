"""Sukno baseline schema from SQLModel metadata."""

from alembic import op

revision = "001_sukno_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlmodel import SQLModel

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

    SQLModel.metadata.create_all(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    pass
