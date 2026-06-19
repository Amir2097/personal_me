"""Add user admin fields: is_active, created_at, last_login_at."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_user_admin_fields"
down_revision: Union[str, None] = "005_user_email"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "user",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.add_column(
        "user",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("user", "is_active", server_default=None)
    op.alter_column("user", "created_at", server_default=None)


def downgrade() -> None:
    op.drop_column("user", "last_login_at")
    op.drop_column("user", "created_at")
    op.drop_column("user", "is_active")
