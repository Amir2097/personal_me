"""Add image fields to projects."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010_project_images"
down_revision: Union[str, None] = "009_site_legal"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "project",
        sa.Column("image_url", sa.String(), nullable=False, server_default=""),
    )
    op.add_column(
        "project",
        sa.Column("gallery_urls", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("project", "gallery_urls")
    op.drop_column("project", "image_url")
