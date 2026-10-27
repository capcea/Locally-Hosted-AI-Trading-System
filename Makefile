PYTHON ?= python3.12
PY := .venv/bin/python
UV := .tools/bin/uv
export UV_CACHE_DIR := $(CURDIR)/.cache/uv
export PRE_COMMIT_HOME := $(CURDIR)/.cache/pre-commit

.PHONY: setup bootstrap identity-setup market-setup dev local-api local-web stop test lint typecheck build check doctor smoke-demo seed-demo migrate contracts contracts-check integration integration-services browser-integration repository-check secret-scan
setup:
	PYTHON="$(PYTHON)" bash scripts/setup.sh
bootstrap:
	$(PY) -m scripts.bootstrap
identity-setup: bootstrap
	$(PY) -m scripts.identity_setup
market-setup: identity-setup
	$(PY) -m scripts.market_setup
dev: market-setup
	docker compose up --build -d --wait --wait-timeout 180
local-api:
	$(PY) -m uvicorn apps.api.main:create_app --factory --host 127.0.0.1 --port 18000 --no-access-log
local-web:
	npm --prefix apps/web run dev
stop:
	docker compose down
test:
	$(PY) -m pytest -m 'not infrastructure and not isolated_services'
	npm --prefix apps/web test
lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .
	npm --prefix apps/web run lint
typecheck:
	$(PY) -m mypy
	npm --prefix apps/web run typecheck
build:
	npm --prefix apps/web run build
check: lint typecheck test build
doctor:
	$(PY) -m scripts.doctor
smoke-demo:
	$(PY) -m scripts.smoke_demo
seed-demo:
	$(PY) -m scripts.seed_demo_data
migrate:
	$(PY) -m scripts.migrate_runtime
contracts:
	$(PY) -m scripts.export_openapi
	npm --prefix apps/web run generate:api
integration:
	$(PY) -m pytest -m infrastructure
	$(PY) -m scripts.integration_services
	$(PY) -m scripts.smoke_demo --require-ready
integration-services:
	$(PY) -m scripts.integration_services
browser-integration:
	$(PY) -m scripts.integration_services --browser
contracts-check:
	$(PY) -m scripts.check_contracts
repository-check:
	$(PY) -m scripts.repository_check
secret-scan:
	$(PY) -m scripts.scan_secrets

