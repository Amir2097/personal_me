"""SSO codes and integration.use_sso."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_sso"
down_revision: Union[str, None] = "002_projects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "integration",
        sa.Column("use_sso", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "ssocode",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("service_key", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ssocode_code"), "ssocode", ["code"], unique=True)
    op.create_index(op.f("ix_ssocode_username"), "ssocode", ["username"], unique=False)
    op.create_index(op.f("ix_ssocode_service_key"), "ssocode", ["service_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ssocode_service_key"), table_name="ssocode")
    op.drop_index(op.f("ix_ssocode_username"), table_name="ssocode")
    op.drop_index(op.f("ix_ssocode_code"), table_name="ssocode")
    op.drop_table("ssocode")
    op.drop_column("integration", "use_sso")
