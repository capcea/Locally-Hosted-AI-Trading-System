FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir uv==0.13.5
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache
# Explicit source allowlist: no API/auth/risk/research/execution code or migration tools.
COPY packages/__init__.py packages/__init__.py
COPY packages/ai packages/ai
COPY packages/persistence/__init__.py packages/persistence/models.py packages/persistence/store.py packages/persistence/
COPY scripts/__init__.py scripts/ai_worker.py scripts/
RUN useradd --uid 10001 --no-create-home ai
USER 10001:10001
CMD ["/app/.venv/bin/python", "-m", "scripts.ai_worker"]
