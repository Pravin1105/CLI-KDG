"""
cli_kdg.replay — Snapshot Replay & Behavioral Regression Analyzer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Re-executes historical TestCase objects from a Snapshot and compares observable behavior field-by-field.
"""

from typing import List, Optional, Tuple
from cli_kdg.models import (
    Snapshot, TestObservation, TestCase, ExecutionResult,
    ComparisonDetail, ReplayCaseResult, ReplayResult, TerminationType
)
from cli_kdg.process import execute_target


def replay_snapshot(
    snapshot: Snapshot,
    target: str,
    target_args: List[str],
    timeout: Optional[float] = None
) -> ReplayResult:
    """Replays stored historical test cases from Snapshot against target CLI and classifies results."""
    case_results: List[ReplayCaseResult] = []

    for obs in snapshot.observations:
        test_case = TestCase(obs.arguments, obs.category, obs.reason)
        current_res = execute_target(target, target_args + obs.arguments, timeout=timeout)
        classification, diffs = compare_observations(obs, current_res)

        case_results.append(ReplayCaseResult(
            test_case=test_case,
            baseline_obs=obs,
            current_res=current_res,
            classification=classification,
            diffs=diffs
        ))

    return ReplayResult(snapshot_path="", target=target, target_args=target_args, case_results=case_results)


def compare_observations(baseline: TestObservation, current: ExecutionResult) -> Tuple[str, List[ComparisonDetail]]:
    """Compares baseline TestObservation against current ExecutionResult field-by-field (runtime ignored)."""
    if current.termination_type == TerminationType.START_FAILED:
        return "FAILED", [ComparisonDetail("termination_type", baseline.termination_type, current.termination_type)]

    diffs: List[ComparisonDetail] = []

    if baseline.exit_code != current.exit_code:
        diffs.append(ComparisonDetail("exit_code", str(baseline.exit_code), str(current.exit_code)))

    if baseline.is_success() != current.is_success():
        diffs.append(ComparisonDetail("status", "SUCCESS" if baseline.is_success() else "FAILURE", "SUCCESS" if current.is_success() else "FAILURE"))

    if baseline.stdout.strip() != current.stdout.strip():
        diffs.append(ComparisonDetail("stdout", baseline.stdout.strip() or "<empty>", current.stdout.strip() or "<empty>"))

    if baseline.stderr.strip() != current.stderr.strip():
        diffs.append(ComparisonDetail("stderr", baseline.stderr.strip() or "<empty>", current.stderr.strip() or "<empty>"))

    if baseline.termination_type != current.termination_type:
        diffs.append(ComparisonDetail("termination_type", baseline.termination_type, current.termination_type))

    return ("CHANGED" if diffs else "UNCHANGED"), diffs
