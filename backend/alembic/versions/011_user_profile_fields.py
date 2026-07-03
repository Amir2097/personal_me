"""Add extended user profile fields."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011_user_profile_fields"
down_revision: Union[str, None] = "010_project_images"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("display_name", sa.String(), nullable=False, server_default=""))
    op.add_column("user", sa.Column("avatar_url", sa.String(), nullable=False, server_default=""))
    op.add_column("user", sa.Column("bio", sa.String(), nullable=False, server_default=""))
    op.add_column("user", sa.Column("location", sa.String(), nullable=False, server_default=""))
    op.add_column("user", sa.Column("website", sa.String(), nullable=False, server_default=""))
    op.add_column("user", sa.Column("telegram", sa.String(), nullable=False, server_default=""))
    op.add_column("user", sa.Column("github", sa.String(), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("user", "github")
    op.drop_column("user", "telegram")
    op.drop_column("user", "website")
    op.drop_column("user", "location")
    op.drop_column("user", "bio")
    op.drop_column("user", "avatar_url")
    op.drop_column("user", "display_name")
