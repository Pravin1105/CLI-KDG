"""
cli_kdg.errors
~~~~~~~~~~~~~~

Custom exception hierarchy and error handling routines for CLI-KDG.
Ensures clean, human-readable user error output without uncontrolled tracebacks.
"""


class CLKDGError(Exception):
    """Base exception for all CLI-KDG errors."""
    pass


class CLKDGUserError(CLKDGError):
    """Raised when the user provides invalid CLI arguments or invocation syntax."""
    pass


class CLKDGExecutionError(CLKDGError):
    """Raised when target binary execution fails to start (e.g. executable missing)."""
    pass


def format_error_message(message: str) -> str:
    """Formats an operational error message into a human-readable CLI-KDG error report."""
    return f"CLI-KDG error: {message}"
