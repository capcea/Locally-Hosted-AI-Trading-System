"""The default executor intentionally has no implementation of order placement."""


class ExecutionDisabledError(PermissionError):
    """An operation attempted to cross an unavailable trust boundary."""


def deny_order_submission() -> None:
    raise ExecutionDisabledError("ORDER_SUBMISSION_DISABLED: simulation-only release")
