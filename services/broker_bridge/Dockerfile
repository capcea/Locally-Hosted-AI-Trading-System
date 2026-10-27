FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir uv==0.13.5
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache
COPY packages packages
COPY services services
RUN useradd --uid 10002 --create-home bridge
USER 10002:10002
# No credentials or configured service is enabled by this image.
# Loopback-only listener: use an owner-controlled private host network/tunnel with mTLS.
ENTRYPOINT ["/app/.venv/bin/python", "-m", "services.broker_bridge.app"]
CMD ["--help"]
