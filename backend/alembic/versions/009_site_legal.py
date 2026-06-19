"""Add legal document fields to site_settings."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_site_legal"
down_revision: Union[str, None] = "008_site_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sitesettings",
        sa.Column("privacy_policy", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "sitesettings",
        sa.Column("terms_of_use", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("sitesettings", "terms_of_use")
    op.drop_column("sitesettings", "privacy_policy")
