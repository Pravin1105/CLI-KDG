"""
cli_kdg.discover — Automated Target Interrogation Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Orchestrates --help interrogation, option parsing, case generation, and POSIX process execution.
"""

from typing import List, Optional, Tuple
from cli_kdg.models import DiscoveryResult, TestCase, ExecutionResult
from cli_kdg.process import execute_target
from cli_kdg.help_parser import parse_help_text
from cli_kdg.generator import generate_test_cases


def discover_target(
    target: str,
    target_args: List[str],
    timeout: Optional[float] = None
) -> DiscoveryResult:
    """Interrogates a target CLI executable, generates test cases, and executes them."""
    help_res = execute_target(target, target_args + ["--help"], timeout=timeout)

    if not help_res.is_success() and not help_res.stdout.strip():
        err_msg = help_res.error or f"Target exited with code {help_res.exit_code} and empty STDOUT on --help."
        return DiscoveryResult(target=target, target_args=target_args, help_execution=help_res, discovery_error=err_msg)

    model = parse_help_text(help_res.stdout)
    test_cases = generate_test_cases(model)
    case_results: List[Tuple[TestCase, ExecutionResult]] = [
        (c, execute_target(target, target_args + c.arguments, timeout=timeout)) for c in test_cases
    ]

    return DiscoveryResult(
        target=target,
        target_args=target_args,
        help_execution=help_res,
        model=model,
        test_cases=test_cases,
        case_results=case_results
    )
