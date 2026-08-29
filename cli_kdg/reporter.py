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
