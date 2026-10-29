"""Provision a least-privilege control-plane database role using a migration identity."""

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url


def provision_runtime(admin_url: str, password: str) -> str:
    url = make_url(admin_url)
    # Fixed role name lives inside the chosen cluster. Isolated tests own a separate cluster.
    role = sql.Identifier("research_app")
    with psycopg.connect(
        url.set(drivername="postgresql").render_as_string(hide_password=False), autocommit=True
    ) as connection:
        if (
            connection.execute("SELECT 1 FROM pg_roles WHERE rolname = 'research_app'").fetchone()
            is None
        ):
            connection.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT"
                ).format(role)
            )
        connection.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(role, sql.Literal(password)))
        connection.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(url.database or ""), role
            )
        )
        connection.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(role))
        connection.execute(
            sql.SQL("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {}").format(role)
        )
        connection.execute(
            sql.SQL(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {}"
            ).format(role)
        )
        for table in (
            "audit_events",
            "strategy_versions",
            "execution_events",
            "simulation_commands",
            "broker_observations",
            "risk_profile_versions",
            "risk_run_contexts",
            "risk_decisions",
            "risk_authorizations",
            "risk_authorization_uses",
            "risk_ledger",
            "risk_emergency_commands",
            "research_runs",
            "research_trials",
            "research_results",
            "research_holdout_seals",
            "research_holdout_releases",
            "research_accounts",
            "ai_models",
            "ai_cloud_authorizations",
            "ai_cloud_reservations",
            "ai_routes",
            "ai_requests",
            "ai_artifacts",
            "ai_events",
            "ai_verifications",
            "research_campaigns",
            "campaign_lineage",
            "campaign_experiments",
        ):
            connection.execute(
                sql.SQL("REVOKE UPDATE, DELETE, TRUNCATE ON {} FROM {}").format(
                    sql.Identifier(table), role
                )
            )
        connection.execute(
            sql.SQL("REVOKE INSERT ON ai_artifacts, ai_verifications FROM {}").format(role)
        )
        connection.execute(sql.SQL("REVOKE UPDATE ON ai_jobs FROM {}").format(role))
        connection.execute(
            sql.SQL("GRANT UPDATE(cancel_requested,event_sequence) ON ai_jobs TO {}").format(role)
        )
        connection.execute(
            sql.SQL(
                "REVOKE DELETE, TRUNCATE ON ai_connections, ai_jobs, ai_connection_secrets FROM {}"
            ).format(role)
        )
        connection.execute(sql.SQL("REVOKE DELETE, TRUNCATE ON firm_policies FROM {}").format(role))
        connection.execute(
            sql.SQL("REVOKE DELETE, TRUNCATE ON market_datasets FROM {}").format(role)
        )
        connection.execute(
            sql.SQL("REVOKE DELETE, TRUNCATE ON risk_policy_versions FROM {}").format(role)
        )
        connection.execute(sql.SQL("REVOKE DELETE, TRUNCATE ON research_jobs FROM {}").format(role))
        connection.execute(
            sql.SQL("REVOKE DELETE, TRUNCATE ON campaign_runtime FROM {}").format(role)
        )
        for table in ("roles", "alembic_version", "platform_metadata"):
            connection.execute(
                sql.SQL("REVOKE INSERT, UPDATE, DELETE ON {} FROM {}").format(
                    sql.Identifier(table), role
                )
            )
        connection.execute(
            sql.SQL("REVOKE INSERT, DELETE ON audit_head, security_state FROM {}").format(role)
        )
        connection.execute(
            sql.SQL("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {}").format(role)
        )
    return url.set(username="research_app", password=password).render_as_string(hide_password=False)


def main() -> None:
    from apps.api.config import Settings

    settings = Settings()
    if not settings.database_url or not settings.auth_database_password:
        raise RuntimeError("Migration database URL and runtime password required")
    provision_runtime(
        settings.database_url.get_secret_value(), settings.auth_database_password.get_secret_value()
    )
    print("Runtime database role provisioned; credentials were not printed.")


if __name__ == "__main__":
    main()
