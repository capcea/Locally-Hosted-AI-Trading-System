"""Bounded context capacity envelope; runtime defaults remain4K/16K/32K.

Revision ID: 0013_ai_context_capacity
Revises: 0012_workspace_selections
"""

import sqlalchemy as sa
from alembic import op

revision = "0013_ai_context_capacity"
down_revision = "0012_workspace_selections"
branch_labels = None
depends_on = None


def change_limit(limit: int) -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        table = sa.Table("ai_models", sa.MetaData(), autoload_with=bind)
        check = next(
            c
            for c in table.constraints
            if isinstance(c, sa.CheckConstraint) and "context_ceiling" in str(c.sqltext)
        )
        check.name = "ai_model_context_range"
        with op.batch_alter_table("ai_models", copy_from=table) as batch:
            batch.drop_constraint(check.name, type_="check")
            batch.create_check_constraint(
                check.name, f"context_ceiling>=1024 AND context_ceiling<={limit}"
            )
    else:
        check = next(
            c
            for c in sa.inspect(bind).get_check_constraints("ai_models")
            if "context_ceiling" in c["sqltext"]
        )
        op.drop_constraint(check["name"], "ai_models", type_="check")
        op.create_check_constraint(
            "ai_model_context_range",
            "ai_models",
            f"context_ceiling>=1024 AND context_ceiling<={limit}",
        )


def upgrade() -> None:
    # ALTER CHECK only: no model, verification, role, credential or audit row is rewritten.
    change_limit(131072)


def downgrade() -> None:
    if (
        op.get_bind()
        .execute(sa.text("SELECT 1 FROM ai_models WHERE context_ceiling>32768 LIMIT 1"))
        .first()
    ):
        raise RuntimeError("Refuse downgrade: larger immutable model versions must be retained")
    change_limit(32768)
