"""Add expires_at to sync room tables."""

import sqlalchemy as sa
from alembic import op

revision = "002_session_expires_at"
down_revision = "001_sukno_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "kolkhozsession",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cupsession",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cupsession", "expires_at")
    op.drop_column("kolkhozsession", "expires_at")
