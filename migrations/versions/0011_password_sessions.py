"""Password/session policy; preserve enrolled secrets, partial sessions and historical audit.

Revision ID: 0011_password_sessions
Revises: 0010_ai_standing
"""

import sqlalchemy as sa
from alembic import op

revision = "0011_password_sessions"
down_revision = "0010_ai_standing"
branch_labels = None
depends_on = None


def authority_view(password: bool) -> None:
    freshness = "s.mfa_at>now()-interval '5 minutes'"
    if password:
        # Never revive a previously unauthorized queued request during the policy migration.
        freshness = (
            "((s.auth_policy='PASSWORD' AND r.specification->>'auth_policy'='PASSWORD') OR "
            + freshness
            + ")"
        )
    sql = """CREATE OR REPLACE VIEW ai_request_authority WITH (security_barrier=true) AS
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
        ) ELSE FRESHNESS END)
      ) AND NOT EXISTS (
        SELECT 1 FROM campaign_lineage l JOIN campaign_runtime c ON c.campaign_id=l.campaign_id
        WHERE l.kind='GATEWAY_REQUEST' AND l.payload->>'request_id'=r.id::text
        AND (c.owner_id<>r.owner_id OR NOT c.active OR c.cancel_requested
             OR c.deadline IS NULL OR c.deadline<=now())
      )) AS authorized FROM ai_requests r"""
    op.execute(sql.replace("FRESHNESS", freshness))


def upgrade() -> None:
    # Existing FULL logins already passed password auth. Partial sessions are not promoted.
    # No user, enrolled secret, recovery code, audit entry or session timestamp is rewritten.
    op.add_column(
        "login_sessions",
        sa.Column("auth_policy", sa.String(16), nullable=False, server_default="PASSWORD"),
    )
    if op.get_bind().dialect.name == "postgresql":
        authority_view(True)


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        authority_view(False)
    op.drop_column("login_sessions", "auth_policy")
