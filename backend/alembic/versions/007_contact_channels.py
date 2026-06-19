"""Add contact channels table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_contact_channels"
down_revision: Union[str, None] = "006_user_admin_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contactchannel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False, server_default=""),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False, server_default="link"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_contactchannel_key"), "contactchannel", ["key"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_contactchannel_key"), table_name="contactchannel")
    op.drop_table("contactchannel")
