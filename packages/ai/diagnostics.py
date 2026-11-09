"""Allowlisted transport facts only; never provider bodies, URLs, headers or credentials."""

from typing import Any

OPERATIONS = frozenset({"MODEL_CATALOG", "MODEL_METADATA", "COMPLETION", "PROVIDER_REQUEST"})


def safe_provider_diagnostic(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    status, operation = value.get("http_status"), value.get("operation")
    if type(status) is not int or not 100 <= status <= 599:
        return None
    if not isinstance(operation, str) or operation not in OPERATIONS:
        return None
    return {"http_status": status, "operation": operation}
