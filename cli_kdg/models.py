"""
cli_kdg.models
~~~~~~~~~~~~~~

Data models and execution result state constants for CLI-KDG.
Designed strictly with Python standard library primitives.
"""

from typing import Optional, List


class TerminationType:
    """
    Enumeration of process termination classifications.
    
    Attributes:
        EXITED: Process completed execution normally (exit status 0 or non-zero).
        SIGNALED: Process was terminated prematurely by a POSIX signal (e.g., SIGTERM, SIGKILL).
        TIMED_OUT: Process exceeded the specified execution deadline and was killed by CLI-KDG.
        START_FAILED: Process could not be executed (e.g., command not found, permission denied).
        CLI_ERROR: CLI-KDG invocation syntax or internal execution error.
    """
    EXITED = "EXITED"
    SIGNALED = "SIGNALED"
    TIMED_OUT = "TIMED_OUT"
    START_FAILED = "START_FAILED"
    CLI_ERROR = "CLI_ERROR"


class ExecutionResult:
    """
    Represents the observed execution outcome of a target process.
    
    Attributes:
        command (str): The executable target command.
        arguments (List[str]): List of arguments passed to the target command.
        exit_code (Optional[int]): Process exit status code (None if signal-terminated or start failed).
        stdout (str): Complete captured standard output string.
        stderr (str): Complete captured standard error string.
        runtime_ms (float): Elapsed execution duration measured in milliseconds.
        termination_type (str): Classification of termination (from TerminationType).
        error (Optional[str]): Human-readable error message if execution failed or timed out.
    """
    def __init__(
        self,
        command: str,
        arguments: List[str],
        exit_code: Optional[int],
        stdout: str,
        stderr: str,
        runtime_ms: float,
        termination_type: str,
        error: Optional[str] = None
    ) -> None:
        self.command = command
        self.arguments = arguments
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.runtime_ms = runtime_ms
        self.termination_type = termination_type
        self.error = error

    def is_success(self) -> bool:
        """Returns True if process exited cleanly with code 0."""
        return self.termination_type == TerminationType.EXITED and self.exit_code == 0

    def __repr__(self) -> str:
        return (
            f"<ExecutionResult command='{self.command}' exit_code={self.exit_code} "
            f"type='{self.termination_type}' runtime={self.runtime_ms:.2f}ms>"
        )
