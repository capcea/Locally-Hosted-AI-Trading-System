"""Append-only standing inference consent; preserves legacy session and campaign gates.

Revision ID: 0010_ai_standing
Revises: 0009_openrouter
"""

import importlib

import sqlalchemy as sa
from alembic import op

revision = "0010_ai_standing"
down_revision = "0009_openrouter"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_standing_authorizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("policy", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("id", "owner_id"),
        sa.UniqueConstraint("owner_id", "revision"),
        sa.CheckConstraint("revision>0"),
    )
    op.create_index(
        "ix_ai_standing_authorizations_owner_id", "ai_standing_authorizations", ["owner_id"]
    )
    if op.get_bind().dialect.name == "postgresql":
        for action in ("UPDATE OR DELETE", "TRUNCATE"):
            name = "standing_immutable" if action != "TRUNCATE" else "standing_no_truncate"
            scope = "ROW" if action != "TRUNCATE" else "STATEMENT"
            op.execute(
                f"CREATE TRIGGER {name} BEFORE {action} ON ai_standing_authorizations "
                f"FOR EACH {scope} EXECUTE FUNCTION deny_execution_rewrite()"
            )
        # Existing sessions must remain valid: standing consent replaces only recent-MFA per job.
        # The worker can read only this boolean view, never users, sessions or authorization writes.
        op.execute("""CREATE OR REPLACE VIEW ai_request_authority WITH (security_barrier=true) AS
          SELECT r.id AS request_id, (EXISTS (
            SELECT 1 FROM users u JOIN login_sessions s ON s.user_id=u.id
            WHERE u.id=r.owner_id AND u.active AND u.role='OWNER'
            AND s.id=CAST(r.specification->>'session_id' AS uuid)
            AND s.state='FULL' AND s.revoked_at IS NULL
            AND s.expires_at>now() AND s.idle_expires_at>now()
            AND (CASE WHEN r.specification->>'standing_authorization_id' IS NOT NULL THEN EXISTS (
              SELECT 1 FROM ai_standing_authorizations a
              WHERE a.owner_id=r.owner_id AND a.active
              AND a.id::text=r.specification->>'standing_authorization_id'
              AND NOT EXISTS (SELECT 1 FROM ai_standing_authorizations newer
                              WHERE newer.owner_id=a.owner_id AND newer.revision>a.revision)
            ) ELSE s.mfa_at>now()-interval '5 minutes' END)
          ) AND NOT EXISTS (
            SELECT 1 FROM campaign_lineage l JOIN campaign_runtime c ON c.campaign_id=l.campaign_id
            WHERE l.kind='GATEWAY_REQUEST' AND l.payload->>'request_id'=r.id::text
            AND (c.owner_id<>r.owner_id OR NOT c.active OR c.cancel_requested
                 OR c.deadline IS NULL OR c.deadline<=now())
          )) AS authorized FROM ai_requests r""")
        # Add privileges without rotating existing credentials or broadening worker access.
        op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='research_app')
          THEN GRANT SELECT,INSERT ON ai_standing_authorizations TO research_app; END IF; END $$""")


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        importlib.import_module("migrations.versions.0008_research_campaigns").authority_view(True)
    op.drop_table("ai_standing_authorizations")
