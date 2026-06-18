"""Add optional email to users."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_user_email"
down_revision: Union[str, None] = "004_oidc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("email", sa.String(), nullable=True))
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_column("user", "email")
