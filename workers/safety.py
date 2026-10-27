"""A mandatory gate for future worker entry points, with no execution implementation."""

from apps.api.config import Settings
from packages.domain.safety import ExecutionDisabledError


def require_research_execution(settings: Settings) -> None:
    # Do not rely on environment validation alone: deny even if constructed unsafely.
    raise ExecutionDisabledError("RESEARCH_EXECUTION_DISABLED: isolated runner not implemented")
