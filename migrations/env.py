"""No secret-bearing SQLAlchemy URLs are stored in alembic.ini or logged."""

from alembic import context
from sqlalchemy import create_engine, pool

from apps.api.config import Settings

config = context.config
url = config.attributes.get("database_url")
if url is None:
    settings = Settings()
    migration_url = settings.migration_database_url or settings.database_url
    if migration_url is None:
        raise RuntimeError("DATABASE_URL is required; run make bootstrap")
    url = migration_url.get_secret_value()

if context.is_offline_mode():
    context.configure(url=url, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
