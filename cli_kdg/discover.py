"""
cli_kdg.discover
~~~~~~~~~~~~~~~~

Discovery execution engine for CLI-KDG v1.2.
Orchestrates automated target interrogation, CLIModel construction, test case generation,
and execution through the v1.1 POSIX process engine.

Process Workflow:
    target → --help → parse options → CLIModel → generate TestCase[] → v1.1 execution → report
"""

from typing import List, Optional, Tuple
from cli_kdg.models import ExecutionResult, DiscoveryResult
from cli_kdg.process import execute_target
from cli_kdg.help_parser import parse_help_text
from cli_kdg.generator import generate_test_cases


def discover_target(
    target: str,
    target_args: List[str],
    timeout: Optional[float] = None
) -> DiscoveryResult:
    """
    Interrogates a target CLI executable, generates deterministic test cases, and executes them.

    Args:
        target (str): Target executable binary name or path.
        target_args (List[str]): Base target arguments.
        timeout (Optional[float]): Execution timeout limit in seconds.

    Returns:
        DiscoveryResult: Captured discovery observation outcome.
    """
    # Step 1: Interrogate target --help interface via POSIX process engine
    help_args = target_args + ["--help"]
    help_res = execute_target(target, help_args, timeout=timeout)

    # Step 2: Handle discovery execution failure gracefully
    if not help_res.is_success() and not help_res.stdout.strip():
        err_msg = help_res.error or f"Target exited with code {help_res.exit_code} and empty STDOUT on --help."
        return DiscoveryResult(
            target=target,
            target_args=target_args,
            help_execution=help_res,
            discovery_error=err_msg
        )

    # Step 3: Parse stdout help text into structured CLIModel
    model = parse_help_text(help_res.stdout)

    # Step 4: Generate bounded deterministic test cases
    test_cases = generate_test_cases(model)

    # Step 5: Execute generated test cases through v1.1 POSIX process engine
    case_results: List[Tuple] = []
    for case in test_cases:
        full_args = target_args + case.arguments
        res = execute_target(target, full_args, timeout=timeout)
        case_results.append((case, res))

    return DiscoveryResult(
        target=target,
        target_args=target_args,
        help_execution=help_res,
        model=model,
        test_cases=test_cases,
        case_results=case_results
    )
