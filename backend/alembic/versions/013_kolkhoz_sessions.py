"""Kolkhoz sync sessions table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_kolkhoz_sessions"
down_revision: Union[str, None] = "012_user_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kolkhozsession",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=8), nullable=False),
        sa.Column("owner_username", sa.String(), nullable=False),
        sa.Column("state_json", sa.JSON(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_kolkhozsession_code"), "kolkhozsession", ["code"], unique=True)
    op.create_index(
        op.f("ix_kolkhozsession_owner_username"),
        "kolkhozsession",
        ["owner_username"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_kolkhozsession_owner_username"), table_name="kolkhozsession")
    op.drop_index(op.f("ix_kolkhozsession_code"), table_name="kolkhozsession")
    op.drop_table("kolkhozsession")
