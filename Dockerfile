FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_CACHE_DIR=/tmp/uv-cache
WORKDIR /app
RUN pip install --no-cache-dir uv==0.13.5
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache
COPY apps/api apps/api
COPY apps/__init__.py apps/__init__.py
COPY packages packages
COPY workers workers
COPY migrations migrations
COPY scripts/__init__.py scripts/migrate_runtime.py scripts/provision_runtime.py scripts/provision_market.py scripts/market_worker.py scripts/risk_monitor.py scripts/research_worker.py scripts/campaign_worker.py scripts/
COPY alembic.ini ./
# Exercise the packaged entrypoint without configuration, network calls or worker execution.
RUN /app/.venv/bin/python -m scripts.campaign_worker --help > /dev/null
RUN useradd --uid 10001 --create-home app
USER 10001:10001
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "apps.api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

