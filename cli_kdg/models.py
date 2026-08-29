"""
cli_kdg.models — Core Data Models (v1.1, v1.2, v1.3)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Zero-dependency dataclasses representing process execution outcomes,
discovered CLI models, test cases, behavioral snapshots, and replay diffs.
"""

import time
from typing import Optional, List, Tuple


class TerminationType:
    """Process termination classifications."""
    EXITED = "EXITED"
    SIGNALED = "SIGNALED"
    TIMED_OUT = "TIMED_OUT"
    START_FAILED = "START_FAILED"
    CLI_ERROR = "CLI_ERROR"


class ExecutionResult:
    """Observed execution outcome of a target process."""
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
        """Returns True if process exited cleanly with status 0."""
        return self.termination_type == TerminationType.EXITED and self.exit_code == 0

    def __repr__(self) -> str:
        return f"<ExecutionResult cmd='{self.command}' exit={self.exit_code} type='{self.termination_type}'>"


class CLIOption:
    """Discovered CLI option specification."""
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
        """Returns clean human-readable name of option."""
        names = ", ".join(filter(None, [self.short_name, self.long_name]))
        return f"{names} {self.value_hint or 'VALUE'}" if self.requires_value else names

    def __repr__(self) -> str:
        return f"<CLIOption short='{self.short_name}' long='{self.long_name}'>"


class CLIModel:
    """Structured representation of an interrogated target CLI."""
    def __init__(self, options: List[CLIOption], raw_help_text: str = "") -> None:
        self.options = options
        self.raw_help_text = raw_help_text


class TestCase:
    """Generated test case for a CLI target."""
    def __init__(self, arguments: List[str], category: str, reason: str) -> None:
        self.arguments = arguments
        self.category = category
        self.reason = reason


class DiscoveryResult:
    """Outcome of a 'discover' subcommand run."""
    def __init__(
        self,
        target: str,
        target_args: List[str],
        help_execution: ExecutionResult,
        model: Optional[CLIModel] = None,
        test_cases: Optional[List[TestCase]] = None,
        case_results: Optional[List[Tuple[TestCase, ExecutionResult]]] = None,
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
        """Returns True if discovery and all generated test cases succeeded."""
        return not self.discovery_error and self.help_execution.is_success()


class TestObservation:
    """Persisted observation outcome of a test case."""
    def __init__(
        self,
        arguments: List[str],
        category: str,
        reason: str,
        exit_code: Optional[int],
        stdout: str,
        stderr: str,
        runtime_ms: float,
        termination_type: str
    ) -> None:
        self.arguments = arguments
        self.category = category
        self.reason = reason
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.runtime_ms = runtime_ms
        self.termination_type = termination_type

    def is_success(self) -> bool:
        """Returns True if historical process exited cleanly with code 0."""
        return self.termination_type == TerminationType.EXITED and self.exit_code == 0

    def to_dict(self) -> dict:
        """Serializes observation object to dictionary."""
        return {
            "arguments": self.arguments,
            "category": self.category,
            "reason": self.reason,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "runtime_ms": self.runtime_ms,
            "termination_type": self.termination_type
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TestObservation":
        """Deserializes dictionary to TestObservation."""
        return cls(
            arguments=data.get("arguments", []),
            category=data.get("category", "UNKNOWN"),
            reason=data.get("reason", ""),
            exit_code=data.get("exit_code"),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            runtime_ms=data.get("runtime_ms", 0.0),
            termination_type=data.get("termination_type", TerminationType.EXITED)
        )


class Snapshot:
    """Versioned historical test observation container."""
    def __init__(
        self,
        target: str,
        target_args: List[str],
        observations: List[TestObservation],
        version: int = 1,
        cli_kdg_version: str = "1.3.0",
        created_at: Optional[str] = None
    ) -> None:
        self.version = version
        self.cli_kdg_version = cli_kdg_version
        self.created_at = created_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.target = target
        self.target_args = target_args
        self.observations = observations

    def to_dict(self) -> dict:
        """Serializes snapshot to dictionary."""
        return {
            "version": self.version,
            "cli_kdg_version": self.cli_kdg_version,
            "created_at": self.created_at,
            "target": self.target,
            "target_args": self.target_args,
            "observations": [obs.to_dict() for obs in self.observations]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        """Deserializes dictionary to Snapshot object."""
        obs_list = [TestObservation.from_dict(d) for d in data.get("observations", [])]
        return cls(
            version=data.get("version", 1),
            cli_kdg_version=data.get("cli_kdg_version", "1.3.0"),
            created_at=data.get("created_at"),
            target=data.get("target", ""),
            target_args=data.get("target_args", []),
            observations=obs_list
        )


class ComparisonDetail:
    """Record of a field discrepancy between baseline and current behavior."""
    def __init__(self, field: str, baseline_val: str, current_val: str) -> None:
        self.field = field
        self.baseline_val = baseline_val
        self.current_val = current_val


class ReplayCaseResult:
    """Outcome of replaying a single test case against a current target."""
    def __init__(
        self,
        test_case: TestCase,
        baseline_obs: TestObservation,
        current_res: ExecutionResult,
        classification: str,
        diffs: Optional[List[ComparisonDetail]] = None
    ) -> None:
        self.test_case = test_case
        self.baseline_obs = baseline_obs
        self.current_res = current_res
        self.classification = classification
        self.diffs = diffs or []


class ReplayResult:
    """Complete summary of a replay comparison run."""
    def __init__(
        self,
        snapshot_path: str,
        target: str,
        target_args: List[str],
        case_results: List[ReplayCaseResult]
    ) -> None:
        self.snapshot_path = snapshot_path
        self.target = target
        self.target_args = target_args
        self.case_results = case_results

    def is_success(self) -> bool:
        """Returns True if all cases are UNCHANGED."""
        return all(cr.classification == "UNCHANGED" for cr in self.case_results)

    def count_by_classification(self, classification: str) -> int:
        """Returns count of cases matching a classification."""
        return sum(1 for cr in self.case_results if cr.classification == classification)
