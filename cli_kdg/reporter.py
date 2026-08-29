"""
cli_kdg.reporter
~~~~~~~~~~~~~~~~

Human-readable report generator for CLI-KDG execution outcomes.
Formats raw ExecutionResult instances into clean, deterministic terminal reports.
"""

from cli_kdg.models import ExecutionResult, TerminationType


def format_report(result: ExecutionResult) -> str:
    """
    Formats an ExecutionResult into a human-readable observation report.

    Args:
        result (ExecutionResult): Observed result object.

    Returns:
        str: Formatted multi-line text report.
    """
    cmd_line = f"{result.command} {' '.join(result.arguments)}".strip()
    exit_str = str(result.exit_code) if result.exit_code is not None else "<none>"

    if result.is_success():
        status_str = "SUCCESS"
    elif result.termination_type == TerminationType.TIMED_OUT:
        status_str = "TIMEOUT"
    elif result.termination_type == TerminationType.SIGNALED:
        status_str = "SIGNALED"
    elif result.termination_type == TerminationType.START_FAILED:
        status_str = "START_FAILED"
    else:
        status_str = "FAILURE"

    stdout_content = result.stdout.strip() if result.stdout.strip() else "<empty>"
    stderr_content = result.stderr.strip() if result.stderr.strip() else "<empty>"

    report_lines = [
        "CLI-KDG v1.1",
        "────────────────────────",
        f"Command: {cmd_line}",
        f"Exit:    {exit_str}",
        f"Runtime: {result.runtime_ms:.2f} ms",
        "",
        "STDOUT",
        stdout_content,
        "",
        "STDERR",
        stderr_content,
        ""
    ]

    if result.error:
        report_lines.extend([f"ERROR: {result.error}", ""])

    report_lines.append(f"STATUS: {status_str}")

    return "\n".join(report_lines)


# =============================================================================
# v1.2 DISCOVERY REPORT FORMATTER
# =============================================================================

def format_discovery_report(result: "DiscoveryResult") -> str:
    """
    Formats a DiscoveryResult instance into a structured human-readable terminal report.

    Args:
        result (DiscoveryResult): Observed discovery outcome.

    Returns:
        str: Formatted multi-line text report.
    """
    from cli_kdg.models import DiscoveryResult

    target_cmd = f"{result.target} {' '.join(result.target_args)}".strip()

    lines = [
        "CLI-KDG Discovery & Test Execution Report (v1.2)",
        "==================================================",
        f"Target:               {target_cmd}",
        f"Help Interrogation:   Exit {result.help_execution.exit_code} ({result.help_execution.runtime_ms:.2f} ms)",
    ]

    if result.discovery_error:
        lines.extend([
            f"Discovery Status:     FAILED",
            f"Error:                {result.discovery_error}",
            "=================================================="
        ])
        return "\n".join(lines)

    opts_count = len(result.model.options) if result.model else 0
    cases_count = len(result.test_cases)
    lines.extend([
        f"Discovered Options:   {opts_count}",
        f"Generated Test Cases: {cases_count}",
        "==================================================",
        ""
    ])

    if result.model and result.model.options:
        lines.append("Discovered Option Specifications:")
        for opt in result.model.options:
            lines.append(f"  • {opt.display_name()}")
        lines.extend(["", "==================================================", ""])

    lines.append("Executed Test Cases:")
    lines.append("--------------------------------------------------")

    for idx, (case, res) in enumerate(result.case_results, start=1):
        cmd_str = f"{res.command} {' '.join(res.arguments)}".strip()
        status_label = "SUCCESS" if res.is_success() else res.termination_type

        lines.extend([
            f"[{idx}/{cases_count}] Category: {case.category}",
            f"Command:  {cmd_str}",
            f"Reason:   {case.reason}",
            f"Outcome:  Exit {res.exit_code if res.exit_code is not None else '<none>'} | "
            f"Runtime: {res.runtime_ms:.2f} ms | Status: {status_label}",
        ])

        if res.stdout.strip():
            lines.append("STDOUT:")
            lines.append(f"  {res.stdout.strip()[:200]}")
        if res.stderr.strip():
            lines.append("STDERR:")
            lines.append(f"  {res.stderr.strip()[:200]}")

        lines.append("--------------------------------------------------")

    overall_status = "SUCCESS" if result.is_success() else "COMPLETED_WITH_FAILURES"
    lines.append(f"DISCOVERY STATUS: {overall_status}")

    return "\n".join(lines)

