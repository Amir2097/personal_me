"""Kolkhoz saved games history."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_kolkhoz_games"
down_revision: Union[str, None] = "013_kolkhoz_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kolkhozgame",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_username", sa.String(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("tournament_kind", sa.String(length=32), nullable=False),
        sa.Column("player_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bank_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("state_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_kolkhozgame_owner_username"),
        "kolkhozgame",
        ["owner_username"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_kolkhozgame_owner_username"), table_name="kolkhozgame")
    op.drop_table("kolkhozgame")
