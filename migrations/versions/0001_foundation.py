"""Platform schema marker, with an explicit simulation-only environment constraint."""

import sqlalchemy as sa
from alembic import op

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = op.create_table(
        "platform_metadata",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.String(255), nullable=False),
        sa.Column("environment", sa.String(16), nullable=False),
        sa.CheckConstraint("environment = 'SIMULATED'", name="ck_simulation_only"),
    )
    op.bulk_insert(
        table,
        [
            {"key": "release", "value": "0.1.0", "environment": "SIMULATED"},
        ],
    )


def downgrade() -> None:
    op.drop_table("platform_metadata")
