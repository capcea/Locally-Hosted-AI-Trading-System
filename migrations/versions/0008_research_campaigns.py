"""Bounded campaigns and immutable research lineage. No changes to financial tables.

Revision ID: 0008_research_campaigns
Revises: 0007_ai_gateway
"""

import sqlalchemy as sa
from alembic import op

revision = "0008_research_campaigns"
down_revision = "0007_ai_gateway"
branch_labels = None
depends_on = None


def authority_view(campaigns: bool) -> None:
    if campaigns:
        op.execute("""CREATE OR REPLACE VIEW ai_request_authority WITH (security_barrier=true) AS
      SELECT r.id AS request_id, (EXISTS (
        SELECT 1 FROM users u JOIN login_sessions s ON s.user_id=u.id
        WHERE u.id=r.owner_id AND u.active AND u.role='OWNER'
        AND s.id=CAST(r.specification->>'session_id' AS uuid)
        AND s.state='FULL' AND s.revoked_at IS NULL AND s.expires_at>now()
        AND s.idle_expires_at>now() AND s.mfa_at>now()-interval '5 minutes'
      ) AND NOT EXISTS (
        SELECT 1 FROM campaign_lineage l JOIN campaign_runtime c ON c.campaign_id=l.campaign_id
        WHERE l.kind='GATEWAY_REQUEST' AND l.payload->>'request_id'=r.id::text
        AND (c.owner_id<>r.owner_id OR NOT c.active OR c.cancel_requested
             OR c.deadline IS NULL OR c.deadline<=now())
      )) AS authorized FROM ai_requests r""")
    else:
        op.execute("""CREATE OR REPLACE VIEW ai_request_authority WITH (security_barrier=true) AS
      SELECT r.id AS request_id, (EXISTS (
        SELECT 1 FROM users u JOIN login_sessions s ON s.user_id=u.id
        WHERE u.id=r.owner_id AND u.active AND u.role='OWNER'
        AND s.id=CAST(r.specification->>'session_id' AS uuid)
        AND s.state='FULL' AND s.revoked_at IS NULL AND s.expires_at>now()
        AND s.idle_expires_at>now() AND s.mfa_at>now()-interval '5 minutes'
      )) AS authorized FROM ai_requests r""")


def upgrade() -> None:
    op.create_table(
        "research_campaigns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(80), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("specification", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id", "owner_id"], ["trading_accounts.id", "trading_accounts.owner_id"]
        ),
        sa.UniqueConstraint("id", "owner_id"),
        sa.UniqueConstraint("owner_id", "key"),
    )
    op.create_index("ix_research_campaigns_owner_id", "research_campaigns", ["owner_id"])
    op.create_table(
        "campaign_runtime",
        sa.Column("campaign_id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("pending", sa.String(40)),
        sa.Column("reason", sa.String(100)),
        *[
            sa.Column(n, sa.Boolean(), nullable=False)
            for n in ("active", "cancel_requested", "paused")
        ],
        *[
            sa.Column(n, sa.Integer(), nullable=False)
            for n in (
                "proposals",
                "experiments",
                "iteration",
                "lineage_bytes",
                "reserved_bytes",
                "reserved_seconds",
                "sequence",
                "attempts",
            )
        ],
        sa.Column("head", sa.String(64), nullable=False),
        sa.Column("approval", sa.JSON()),
        sa.Column("deadline", sa.DateTime(timezone=True)),
        sa.Column("worker_token", sa.Uuid()),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["campaign_id", "owner_id"], ["research_campaigns.id", "research_campaigns.owner_id"]
        ),
        sa.CheckConstraint("proposals>=0 AND proposals<=8 AND experiments>=0 AND experiments<=12"),
        sa.CheckConstraint("iteration>=0 AND iteration<=2 AND attempts>=0 AND attempts<=3"),
        sa.CheckConstraint("lineage_bytes>=0 AND reserved_bytes>=0 AND reserved_seconds>=0"),
        sa.CheckConstraint("sequence>=0"),
        sa.CheckConstraint(
            "state IN ('DRAFT','AWAITING_APPROVAL','QUEUED','PLANNING','TESTING',"
            "'EVALUATING','CRITIQUING','READY_FOR_NEXT_ITERATION','COMPLETED',"
            "'STOPPED','FAILED','UNKNOWN')"
        ),
    )
    op.create_index("ix_campaign_runtime_state", "campaign_runtime", ["state"])
    op.create_table(
        "campaign_lineage",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), sa.ForeignKey("campaign_lineage.id")),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(24), nullable=False),
        sa.Column("previous_digest", sa.String(64), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["campaign_id", "owner_id"], ["research_campaigns.id", "research_campaigns.owner_id"]
        ),
        sa.UniqueConstraint("id", "owner_id"),
        sa.UniqueConstraint("campaign_id", "sequence"),
        sa.CheckConstraint("sequence>0"),
        sa.CheckConstraint("source IN ('SYNTHETIC_FIXTURE','AI_GATEWAY')"),
    )
    op.create_table(
        "campaign_experiments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["campaign_id", "owner_id"], ["research_campaigns.id", "research_campaigns.owner_id"]
        ),
        sa.ForeignKeyConstraint(
            ["plan_id", "owner_id"], ["campaign_lineage.id", "campaign_lineage.owner_id"]
        ),
        sa.ForeignKeyConstraint(
            ["run_id", "owner_id"], ["research_runs.id", "research_runs.owner_id"]
        ),
        sa.UniqueConstraint("plan_id"),
        sa.UniqueConstraint("run_id"),
        sa.UniqueConstraint("campaign_id", "ordinal"),
    )
    if op.get_bind().dialect.name == "postgresql":
        authority_view(True)
        for table in ("research_campaigns", "campaign_lineage", "campaign_experiments"):
            op.execute(
                f"CREATE TRIGGER campaign_immutable BEFORE UPDATE OR DELETE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION deny_execution_rewrite()"
            )
            op.execute(
                f"CREATE TRIGGER campaign_no_truncate BEFORE TRUNCATE ON {table} "
                "FOR EACH STATEMENT EXECUTE FUNCTION deny_execution_rewrite()"
            )
        op.execute(
            "CREATE TRIGGER campaign_retain BEFORE DELETE ON campaign_runtime "
            "FOR EACH ROW EXECUTE FUNCTION deny_execution_rewrite()"
        )
        op.execute(
            "CREATE TRIGGER campaign_retain_truncate BEFORE TRUNCATE ON campaign_runtime "
            "FOR EACH STATEMENT EXECUTE FUNCTION deny_execution_rewrite()"
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        authority_view(False)
    for table in (
        "campaign_experiments",
        "campaign_lineage",
        "campaign_runtime",
        "research_campaigns",
    ):
        op.drop_table(table)
