"""Isolated inference records, immutable metadata and erasable encrypted content.

Revision ID: 0007_ai_gateway
Revises: 0006_research_engine
"""

import sqlalchemy as sa
from alembic import op

revision = "0007_ai_gateway"
down_revision = "0006_research_engine"
branch_labels = None
depends_on = None

IMMUTABLE = (
    "ai_models",
    "ai_routes",
    "ai_requests",
    "ai_artifacts",
    "ai_events",
    "ai_verifications",
)


def identity_columns() -> list[sa.Column]:  # type: ignore[type-arg]
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "ai_connections",
        *identity_columns(),
        sa.Column("specification", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("id", "owner_id"),
    )
    op.create_index("ix_ai_connections_owner_id", "ai_connections", ["owner_id"])
    op.create_table(
        "ai_models",
        *identity_columns(),
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("context_ceiling", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["connection_id", "owner_id"], ["ai_connections.id", "ai_connections.owner_id"]
        ),
        sa.UniqueConstraint("id", "owner_id"),
        sa.UniqueConstraint("connection_id", "name", "context_ceiling"),
        sa.CheckConstraint("context_ceiling>=1024 AND context_ceiling<=32768"),
    )
    op.create_index("ix_ai_models_owner_id", "ai_models", ["owner_id"])
    op.create_table(
        "ai_routes",
        *identity_columns(),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("model_id", sa.Uuid(), nullable=False),
        sa.Column("fallback_ids", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["model_id", "owner_id"], ["ai_models.id", "ai_models.owner_id"]),
        sa.UniqueConstraint("owner_id", "role", "revision"),
        sa.CheckConstraint("role IN ('RESEARCH','CODING','CRITIC','LIGHTWEIGHT')"),
    )
    op.create_index("ix_ai_routes_owner_id", "ai_routes", ["owner_id"])
    op.create_table(
        "ai_requests",
        *identity_columns(),
        sa.Column("key", sa.String(80), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("specification", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retain_until", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("id", "owner_id"),
        sa.UniqueConstraint("owner_id", "key"),
        sa.CheckConstraint("kind IN ('DISCOVER','PROBE','INFER')"),
    )
    op.create_index("ix_ai_requests_owner_id", "ai_requests", ["owner_id"])
    op.create_table(
        "ai_jobs",
        sa.Column("request_id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("worker_token", sa.Uuid()),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("dispatched_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.String(80)),
        sa.Column("event_sequence", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["request_id", "owner_id"], ["ai_requests.id", "ai_requests.owner_id"]
        ),
        sa.CheckConstraint(
            "state IN ('QUEUED','RUNNING','RETRY','SUCCEEDED','FAILED','CANCELLED','UNKNOWN')"
        ),
        sa.CheckConstraint("attempts>=0 AND attempts<=3 AND event_sequence>=0"),
    )
    op.create_index("ix_ai_jobs_owner_id", "ai_jobs", ["owner_id"])
    op.create_index("ix_ai_jobs_state", "ai_jobs", ["state"])
    op.create_table(
        "ai_content",
        sa.Column("request_id", sa.Uuid(), sa.ForeignKey("ai_requests.id"), primary_key=True),
        sa.Column("input_ciphertext", sa.Text()),
        sa.Column("partial_ciphertext", sa.Text()),
        sa.Column("output_ciphertext", sa.Text()),
    )
    op.create_table(
        "ai_artifacts",
        sa.Column("request_id", sa.Uuid(), sa.ForeignKey("ai_requests.id"), primary_key=True),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("artifact_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "ai_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.Uuid(), sa.ForeignKey("ai_requests.id"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("request_id", "sequence"),
    )
    op.create_index("ix_ai_events_request_id", "ai_events", ["request_id"])
    op.create_table(
        "ai_verifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("model_id", sa.Uuid(), sa.ForeignKey("ai_models.id"), nullable=False),
        sa.Column(
            "request_id", sa.Uuid(), sa.ForeignKey("ai_requests.id"), nullable=False, unique=True
        ),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_verifications_model_id", "ai_verifications", ["model_id"])
    if op.get_bind().dialect.name == "postgresql":
        # Boolean-only authorization view: the worker never receives SELECT on identity tables.
        op.execute("""CREATE VIEW ai_request_authority WITH (security_barrier=true) AS
          SELECT r.id AS request_id, EXISTS (
            SELECT 1 FROM users u JOIN login_sessions s ON s.user_id=u.id
            WHERE u.id=r.owner_id AND u.active AND u.role='OWNER'
            AND s.id=CAST(r.specification->>'session_id' AS uuid)
            AND s.state='FULL' AND s.revoked_at IS NULL
            AND s.expires_at>now() AND s.idle_expires_at>now()
            AND s.mfa_at>now()-interval '5 minutes'
          ) AS authorized FROM ai_requests r""")
        for table in IMMUTABLE:
            op.execute(
                f"CREATE TRIGGER ai_immutable BEFORE UPDATE OR DELETE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION deny_execution_rewrite()"
            )
            op.execute(
                f"CREATE TRIGGER ai_no_truncate BEFORE TRUNCATE ON {table} "
                "FOR EACH STATEMENT EXECUTE FUNCTION deny_execution_rewrite()"
            )
        op.execute("""CREATE FUNCTION pin_ai_connection() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN IF (to_jsonb(NEW)-'enabled') IS DISTINCT FROM (to_jsonb(OLD)-'enabled') THEN
          RAISE EXCEPTION 'AI_CONNECTION_SPECIFICATION_IMMUTABLE'; END IF; RETURN NEW; END $$""")
        op.execute(
            "CREATE TRIGGER ai_connection_pin BEFORE UPDATE ON ai_connections "
            "FOR EACH ROW EXECUTE FUNCTION pin_ai_connection()"
        )
        for table in ("ai_connections", "ai_jobs"):
            op.execute(
                f"CREATE TRIGGER ai_retain BEFORE DELETE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION deny_execution_rewrite()"
            )
            op.execute(
                f"CREATE TRIGGER ai_retain_truncate BEFORE TRUNCATE ON {table} "
                "FOR EACH STATEMENT EXECUTE FUNCTION deny_execution_rewrite()"
            )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP VIEW ai_request_authority")
    for table in (
        "ai_verifications",
        "ai_events",
        "ai_artifacts",
        "ai_content",
        "ai_jobs",
        "ai_requests",
        "ai_routes",
        "ai_models",
        "ai_connections",
    ):
        op.drop_table(table)
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP FUNCTION pin_ai_connection()")
