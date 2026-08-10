"""Academy progress table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015_academy_progress"
down_revision: Union[str, None] = "014_kolkhoz_games"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "academyprogress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_username", sa.String(), nullable=False),
        sa.Column("exercise_id", sa.String(length=64), nullable=False),
        sa.Column("made", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_username",
            "exercise_id",
            name="uq_academy_progress_owner_exercise",
        ),
    )
    op.create_index(
        op.f("ix_academyprogress_owner_username"),
        "academyprogress",
        ["owner_username"],
        unique=False,
    )
    op.create_index(
        op.f("ix_academyprogress_exercise_id"),
        "academyprogress",
        ["exercise_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_academyprogress_exercise_id"), table_name="academyprogress")
    op.drop_index(op.f("ix_academyprogress_owner_username"), table_name="academyprogress")
    op.drop_table("academyprogress")
