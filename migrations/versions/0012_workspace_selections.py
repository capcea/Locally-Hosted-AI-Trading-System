"""Append-only selected research candidates for the simplified product; no execution grant.

Revision ID: 0012_workspace_selections
Revises: 0011_password_sessions
"""

import sqlalchemy as sa
from alembic import op

revision = "0012_workspace_selections"
down_revision = "0011_password_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_strategy_selections",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("decision_id", sa.Uuid(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id", "owner_id"], ["trading_accounts.id", "trading_accounts.owner_id"]
        ),
        sa.ForeignKeyConstraint(
            ["decision_id", "owner_id"], ["campaign_lineage.id", "campaign_lineage.owner_id"]
        ),
        sa.UniqueConstraint("owner_id", "account_id", "revision"),
        sa.CheckConstraint("mode='SIMULATED' AND revision>0"),
    )
    op.create_index(
        "ix_workspace_strategy_selections_owner_id", "workspace_strategy_selections", ["owner_id"]
    )
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "CREATE TRIGGER selection_immutable BEFORE UPDATE OR DELETE ON "
            "workspace_strategy_selections FOR EACH ROW EXECUTE FUNCTION deny_execution_rewrite()"
        )
        op.execute(
            "CREATE TRIGGER selection_no_truncate BEFORE TRUNCATE ON workspace_strategy_selections "
            "FOR EACH STATEMENT EXECUTE FUNCTION deny_execution_rewrite()"
        )
        op.execute(
            "DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='research_app') "
            "THEN GRANT SELECT,INSERT ON workspace_strategy_selections TO research_app; "
            "END IF; END $$"
        )


def downgrade() -> None:
    op.drop_table("workspace_strategy_selections")
