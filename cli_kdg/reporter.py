"""
cli_kdg.reporter — Human-Readable Terminal Report Generators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Formats raw execution outcomes, discovery models, snapshots, and replay diffs.
"""

from cli_kdg.models import ExecutionResult, TerminationType, DiscoveryResult, Snapshot, ReplayResult


def format_report(result: ExecutionResult) -> str:
    """Formats an ExecutionResult into a human-readable observation report."""
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

    stdout_content = result.stdout.strip() or "<empty>"
    stderr_content = result.stderr.strip() or "<empty>"

    lines = [
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
        lines.extend([f"ERROR: {result.error}", ""])

    lines.append(f"STATUS: {status_str}")
    return "\n".join(lines)


def format_discovery_report(result: DiscoveryResult) -> str:
    """Formats a DiscoveryResult into a structured discovery terminal report."""
    target_cmd = f"{result.target} {' '.join(result.target_args)}".strip()

    lines = [
        "CLI-KDG Discovery & Test Execution Report (v1.2)",
        "==================================================",
        f"Target:               {target_cmd}",
        f"Help Interrogation:   Exit {result.help_execution.exit_code} ({result.help_execution.runtime_ms:.2f} ms)",
    ]

    if result.discovery_error:
        lines.extend(["Discovery Status:     FAILED", f"Error:                {result.discovery_error}", "=================================================="])
        return "\n".join(lines)

    opts_cnt = len(result.model.options) if result.model else 0
    cases_cnt = len(result.test_cases)
    lines.extend([f"Discovered Options:   {opts_cnt}", f"Generated Test Cases: {cases_cnt}", "==================================================", ""])

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
            f"[{idx}/{cases_cnt}] Category: {case.category}",
            f"Command:  {cmd_str}",
            f"Reason:   {case.reason}",
            f"Outcome:  Exit {res.exit_code if res.exit_code is not None else '<none>'} | Runtime: {res.runtime_ms:.2f} ms | Status: {status_label}",
        ])
        if res.stdout.strip():
            lines.extend(["STDOUT:", f"  {res.stdout.strip()[:200]}"])
        if res.stderr.strip():
            lines.extend(["STDERR:", f"  {res.stderr.strip()[:200]}"])
        lines.append("--------------------------------------------------")

    overall = "SUCCESS" if result.is_success() else "COMPLETED_WITH_FAILURES"
    lines.append(f"DISCOVERY STATUS: {overall}")
    return "\n".join(lines)


def format_snapshot_report(snapshot: Snapshot, filepath: str) -> str:
    """Formats Snapshot creation outcome into a terminal report."""
    target_cmd = f"{snapshot.target} {' '.join(snapshot.target_args)}".strip()
    return "\n".join([
        "CLI-KDG Behavioral Snapshot Report (v1.3)",
        "==================================================",
        f"Snapshot Path:        {filepath}",
        f"Format Version:       {snapshot.version}",
        f"Engine Version:       {snapshot.cli_kdg_version}",
        f"Timestamp:            {snapshot.created_at}",
        f"Target Command:       {target_cmd}",
        f"Persisted Cases:      {len(snapshot.observations)}",
        "==================================================",
        f"SNAPSHOT CREATED SUCCESSFULLY: {filepath}"
    ])


def format_replay_report(result: ReplayResult) -> str:
    """Formats ReplayResult into a behavioral regression report."""
    target_cmd = f"{result.target} {' '.join(result.target_args)}".strip()
    total = len(result.case_results)
    unchanged = result.count_by_classification("UNCHANGED")
    changed = result.count_by_classification("CHANGED")
    failed = result.count_by_classification("FAILED")

    lines = [
        "CLI-KDG Behavioral Regression & Replay Report (v1.3)",
        "==================================================",
        f"Snapshot Path:        {result.snapshot_path}",
        f"Replay Target:        {target_cmd}",
        f"Total Test Cases:     {total}",
        f"Unchanged Behavior:   {unchanged}",
        f"Changed Behavior:     {changed}",
        f"Execution Failures:   {failed}",
        "==================================================",
        "",
        "Replay Test Case Details:",
        "--------------------------------------------------"
    ]

    for idx, cr in enumerate(result.case_results, start=1):
        res = cr.current_res
        cmd_str = f"{res.command} {' '.join(res.arguments)}".strip()
        lines.extend([
            f"[{idx}/{total}] Classification: {cr.classification}",
            f"Category: {cr.test_case.category}",
            f"Command:  {cmd_str}",
            f"Reason:   {cr.test_case.reason}",
            f"Outcome:  Exit {res.exit_code if res.exit_code is not None else '<none>'} | Runtime: {res.runtime_ms:.2f} ms | Status: {'SUCCESS' if res.is_success() else res.termination_type}",
        ])
        if cr.classification == "CHANGED":
            lines.append("Behavioral Discrepancies:")
            for d in cr.diffs:
                lines.extend([f"  • Field '{d.field}':", f"      Baseline: {d.baseline_val}", f"      Current:  {d.current_val}"])
        elif cr.classification == "FAILED":
            lines.append(f"Execution Error: {res.error or 'Failed to start executable'}")
        lines.append("--------------------------------------------------")

    overall = "UNCHANGED (No Regressions Detected)" if result.is_success() else "BEHAVIORAL_REGRESSIONS_DETECTED"
    lines.append(f"REPLAY RESULT: {overall}")
    return "\n".join(lines)
