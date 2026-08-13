"""Cup sessions + tournament history tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016_cup_tournaments"
down_revision: Union[str, None] = "015_academy_progress"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cupsession",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=8), nullable=False),
        sa.Column("owner_username", sa.String(), nullable=False),
        sa.Column("state_json", sa.JSON(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_cupsession_code"), "cupsession", ["code"], unique=False)
    op.create_index(op.f("ix_cupsession_owner_username"), "cupsession", ["owner_username"], unique=False)

    op.create_table(
        "cuptournament",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_username", sa.String(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("player_count", sa.Integer(), nullable=False),
        sa.Column("winner_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("state_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_cuptournament_owner_username"),
        "cuptournament",
        ["owner_username"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_cuptournament_owner_username"), table_name="cuptournament")
    op.drop_table("cuptournament")
    op.drop_index(op.f("ix_cupsession_owner_username"), table_name="cupsession")
    op.drop_index(op.f("ix_cupsession_code"), table_name="cupsession")
    op.drop_table("cupsession")
