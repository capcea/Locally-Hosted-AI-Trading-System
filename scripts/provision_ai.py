"""Migration-time AI-only identities; never run with the worker's restricted identity."""

import psycopg
from psycopg import sql
from redis import Redis
from sqlalchemy.engine import make_url


def provision_database(admin_url: str, password: str) -> str:
    url = make_url(admin_url)
    role = sql.Identifier("research_ai")
    with psycopg.connect(
        url.set(drivername="postgresql").render_as_string(hide_password=False), autocommit=True
    ) as db:
        if db.execute("SELECT 1 FROM pg_roles WHERE rolname='research_ai'").fetchone() is None:
            db.execute(
                "CREATE ROLE research_ai LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT"
            )
        db.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(role, sql.Literal(password)))
        db.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(url.database or ""), role
            )
        )
        db.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(role))
        db.execute(sql.SQL("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {}").format(role))
        for table in (
            "ai_connections",
            "ai_cloud_authorizations",
            "ai_connection_secrets",
            "ai_cloud_reservations",
            "ai_models",
            "ai_routes",
            "ai_requests",
            "ai_jobs",
            "ai_content",
            "ai_artifacts",
            "ai_events",
            "ai_verifications",
            "ai_request_authority",
        ):
            db.execute(sql.SQL("GRANT SELECT ON {} TO {}").format(sql.Identifier(table), role))
        for table in ("ai_artifacts", "ai_events", "ai_verifications"):
            db.execute(sql.SQL("GRANT INSERT ON {} TO {}").format(sql.Identifier(table), role))
        db.execute(
            sql.SQL(
                "GRANT UPDATE(state,attempts,worker_token,lease_until,dispatched_at,"
                "started_at,completed_at,error,event_sequence) ON ai_jobs TO {}"
            ).format(role)
        )
        db.execute(
            sql.SQL(
                "GRANT UPDATE(input_ciphertext,partial_ciphertext,output_ciphertext) "
                "ON ai_content TO {}"
            ).format(role)
        )
    return url.set(username="research_ai", password=password).render_as_string(hide_password=False)


def provision_queue(admin_url: str, username: str, password: str) -> None:
    if username not in {"ai_worker", "ai_api"}:
        raise ValueError("Only fixed AI queue identities may be provisioned")
    with Redis.from_url(admin_url, socket_connect_timeout=2, socket_timeout=2) as client:
        commands = (
            ["+ping", "+get", "+set", "+lpush", "+ltrim", "+rpop"]
            if username == "ai_worker"
            else ["+ping", "+get", "+lpush", "+ltrim"]
        )
        # No SELECT/KEYS/SCAN/CONFIG/EVAL, or access to the market/research queue keys.
        client.execute_command(
            "ACL", "SETUSER", username, "reset", "on", ">" + password, "~ai:*", *commands
        )
