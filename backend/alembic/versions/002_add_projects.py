"""Add project table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_projects"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False, server_default=""),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("tech_stack", sa.String(), nullable=False, server_default=""),
        sa.Column("github_url", sa.String(), nullable=False, server_default=""),
        sa.Column("demo_url", sa.String(), nullable=False, server_default=""),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_project_slug"), "project", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_project_slug"), table_name="project")
    op.drop_table("project")
