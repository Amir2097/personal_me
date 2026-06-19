"""Add site_settings singleton table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_site_settings"
down_revision: Union[str, None] = "007_contact_channels"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sitesettings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_name", sa.String(), nullable=False, server_default="personal_me"),
        sa.Column("owner_name", sa.String(), nullable=False, server_default=""),
        sa.Column("tagline", sa.String(), nullable=False, server_default=""),
        sa.Column("bio", sa.String(), nullable=False, server_default=""),
        sa.Column("experience", sa.String(), nullable=False, server_default=""),
        sa.Column("skills", sa.String(), nullable=False, server_default=""),
        sa.Column("site_url", sa.String(), nullable=False, server_default="http://localhost"),
        sa.Column("seo_title_suffix", sa.String(), nullable=False, server_default="Terminal IDE"),
        sa.Column("seo_description", sa.String(), nullable=False, server_default=""),
        sa.Column("seo_keywords", sa.String(), nullable=False, server_default=""),
        sa.Column("og_image_url", sa.String(), nullable=False, server_default=""),
        sa.Column("motd", sa.String(), nullable=False, server_default=""),
        sa.Column("resume_url", sa.String(), nullable=False, server_default=""),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("sitesettings")
