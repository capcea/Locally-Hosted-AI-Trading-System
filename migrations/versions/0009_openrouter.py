"""Explicit cloud authorization, encrypted connection credentials and reserved spend.

Revision ID: 0009_openrouter
Revises: 0008_research_campaigns
"""

import sqlalchemy as sa
from alembic import op

revision = "0009_openrouter"
down_revision = "0008_research_campaigns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_cloud_authorizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("policy", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("id", "owner_id"),
        sa.UniqueConstraint("owner_id", "revision"),
    )
    op.create_index("ix_ai_cloud_authorizations_owner_id", "ai_cloud_authorizations", ["owner_id"])
    op.create_table(
        "ai_connection_secrets",
        sa.Column("connection_id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["connection_id", "owner_id"], ["ai_connections.id", "ai_connections.owner_id"]
        ),
        sa.CheckConstraint("revision>=1"),
    )
    op.create_table(
        "ai_cloud_reservations",
        sa.Column("request_id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("authorization_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["request_id", "owner_id"], ["ai_requests.id", "ai_requests.owner_id"]
        ),
        sa.ForeignKeyConstraint(
            ["authorization_id", "owner_id"],
            ["ai_cloud_authorizations.id", "ai_cloud_authorizations.owner_id"],
        ),
        sa.CheckConstraint("amount>=0"),
    )
    if op.get_bind().dialect.name == "postgresql":
        for table in ("ai_cloud_authorizations", "ai_cloud_reservations"):
            op.execute(
                f"CREATE TRIGGER cloud_immutable BEFORE UPDATE OR DELETE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION deny_execution_rewrite()"
            )
            op.execute(
                f"CREATE TRIGGER cloud_retain BEFORE TRUNCATE ON {table} "
                "FOR EACH STATEMENT EXECUTE FUNCTION deny_execution_rewrite()"
            )


def downgrade() -> None:
    for name in ("ai_cloud_reservations", "ai_connection_secrets", "ai_cloud_authorizations"):
        op.drop_table(name)
