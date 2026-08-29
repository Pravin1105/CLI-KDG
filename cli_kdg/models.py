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


# =============================================================================
# v1.2 AUTOMATED DISCOVERY & TEST GENERATION MODELS
# =============================================================================

class CLIOption:
    """
    Represents an extracted CLI option specification discovered from help interface.

    Attributes:
        short_name (Optional[str]): Short flag identifier (e.g., '-o' or '-v').
        long_name (Optional[str]): Long flag identifier (e.g., '--output' or '--verbose').
        requires_value (bool): True if option requires a value argument.
        value_hint (Optional[str]): Advertised value descriptor hint (e.g., 'FILE', 'INTEGER').
    """
    def __init__(
        self,
        short_name: Optional[str] = None,
        long_name: Optional[str] = None,
        requires_value: bool = False,
        value_hint: Optional[str] = None
    ) -> None:
        self.short_name = short_name
        self.long_name = long_name
        self.requires_value = requires_value
        self.value_hint = value_hint

    def display_name(self) -> str:
        """Returns clean human-readable representation of option."""
        parts = []
        if self.short_name:
            parts.append(self.short_name)
        if self.long_name:
            parts.append(self.long_name)
        names = ", ".join(parts)
        if self.requires_value:
            hint = self.value_hint or "VALUE"
            return f"{names} {hint}"
        return names

    def __repr__(self) -> str:
        return f"<CLIOption short='{self.short_name}' long='{self.long_name}' req_val={self.requires_value}>"


class CLIModel:
    """
    Structured model representation of an interrogated CLI target.

    Attributes:
        options (List[CLIOption]): Discovered option specifications.
        raw_help_text (str): Complete raw help output text captured from --help.
    """
    def __init__(self, options: List[CLIOption], raw_help_text: str = "") -> None:
        self.options = options
        self.raw_help_text = raw_help_text

    def __repr__(self) -> str:
        return f"<CLIModel options_count={len(self.options)}>"


class TestCase:
    """
    Represents a deterministically generated test invocation case.

    Attributes:
        arguments (List[str]): List of argument tokens to append to target command.
        category (str): Classification category (e.g., 'HELP', 'FLAG_VALID', 'OPTION_MISSING_VAL').
        reason (str): Human-interpretable technical explanation of what this test case verifies.
    """
    def __init__(self, arguments: List[str], category: str, reason: str) -> None:
        self.arguments = arguments
        self.category = category
        self.reason = reason

    def __repr__(self) -> str:
        return f"<TestCase category='{self.category}' args={self.arguments}>"


class DiscoveryResult:
    """
    Complete observation result for a 'discover' subcommand execution.

    Attributes:
        target (str): Target executable command.
        target_args (List[str]): Base target arguments.
        help_execution (ExecutionResult): Result of running --help on target.
        model (Optional[CLIModel]): Parsed CLI model (None if discovery failed).
        test_cases (List[TestCase]): List of generated test cases.
        case_results (List[Tuple[TestCase, ExecutionResult]]): Execution outcomes for test cases.
        discovery_error (Optional[str]): Error message if help interrogation failed.
    """
    def __init__(
        self,
        target: str,
        target_args: List[str],
        help_execution: ExecutionResult,
        model: Optional[CLIModel] = None,
        test_cases: Optional[List[TestCase]] = None,
        case_results: Optional[List[tuple]] = None,
        discovery_error: Optional[str] = None
    ) -> None:
        self.target = target
        self.target_args = target_args
        self.help_execution = help_execution
        self.model = model
        self.test_cases = test_cases or []
        self.case_results = case_results or []
        self.discovery_error = discovery_error

    def is_success(self) -> bool:
        """Returns True if discovery succeeded and all test cases executed cleanly."""
        if self.discovery_error or not self.help_execution.is_success():
            return False
        return True

