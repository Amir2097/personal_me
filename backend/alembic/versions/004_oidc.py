"""OIDC OAuth clients and authorization codes."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_oidc"
down_revision: Union[str, None] = "003_sso"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "oauthclient",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.String(), nullable=False),
        sa.Column("client_secret_hash", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False, server_default=""),
        sa.Column("redirect_uris", sa.String(), nullable=False, server_default=""),
        sa.Column("scopes", sa.String(), nullable=False, server_default="openid profile"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_oauthclient_client_id"), "oauthclient", ["client_id"], unique=True)

    op.create_table(
        "oauthauthorizationcode",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("client_id", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("redirect_uri", sa.String(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False, server_default="openid profile"),
        sa.Column("nonce", sa.String(), nullable=False, server_default=""),
        sa.Column("code_challenge", sa.String(), nullable=False, server_default=""),
        sa.Column("code_challenge_method", sa.String(), nullable=False, server_default=""),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_oauthauthorizationcode_code"), "oauthauthorizationcode", ["code"], unique=True
    )
    op.create_index(
        op.f("ix_oauthauthorizationcode_client_id"),
        "oauthauthorizationcode",
        ["client_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_oauthauthorizationcode_username"),
        "oauthauthorizationcode",
        ["username"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_oauthauthorizationcode_username"), table_name="oauthauthorizationcode")
    op.drop_index(op.f("ix_oauthauthorizationcode_client_id"), table_name="oauthauthorizationcode")
    op.drop_index(op.f("ix_oauthauthorizationcode_code"), table_name="oauthauthorizationcode")
    op.drop_table("oauthauthorizationcode")
    op.drop_index(op.f("ix_oauthclient_client_id"), table_name="oauthclient")
    op.drop_table("oauthclient")
