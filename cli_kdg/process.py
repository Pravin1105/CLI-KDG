"""
cli_kdg.process
~~~~~~~~~~~~~~~

Low-level POSIX process execution and observation engine for CLI-KDG.
Implements direct process manipulation using standard POSIX system primitives:

    pipe() → fork() → dup2() → execvp() → waitpid() / select() / kill()

Key Senior Developer Requirements Handled:
1. Zero high-level wrappers (no subprocess module).
2. Explicit Pipe Ownership: Closes unused pipe descriptors immediately in child and parent.
3. Pipe Deadlock Prevention: Non-blocking I/O multiplexing via select() handles large outputs.
4. Monotonic Timeout Deadline: Uses time.monotonic() to eliminate wall-clock drift.
5. Deterministic Child Reaping: Guarantees waitpid() execution on timed-out or killed children.
"""

import os
import sys
import time
import select
import signal
import fcntl
from typing import List, Optional
from cli_kdg.models import ExecutionResult, TerminationType
from cli_kdg.errors import CLKDGExecutionError


def _set_nonblocking(fd: int) -> None:
    """Sets a file descriptor to non-blocking mode using POSIX fcntl."""
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)


def execute_target(
    target: str,
    target_args: List[str],
    timeout: Optional[float] = None
) -> ExecutionResult:
    """
    Executes a target executable in a child process and observes its runtime behavior.

    Args:
        target (str): Target executable binary name or path.
        target_args (List[str]): Arguments vector for target executable.
        timeout (Optional[float]): Execution timeout limit in seconds.

    Returns:
        ExecutionResult: Captured execution data including stdout, stderr, exit code, and runtime.

    Raises:
        CLKDGExecutionError: If process creation or pipe setup fails.
    """
    # Create POSIX pipes for STDOUT and STDERR isolation
    # Each pipe returns a tuple of (read_fd, write_fd)
    try:
        stdout_r, stdout_w = os.pipe()
        stderr_r, stderr_w = os.pipe()
    except OSError as err:
        raise CLKDGExecutionError(f"Failed to create POSIX pipes: {err}")

    start_time = time.monotonic()
    deadline = (start_time + timeout) if timeout is not None else None

    # Fork process execution into parent and child branches
    try:
        pid = os.fork()
    except OSError as err:
        # Clean up pipe file descriptors on fork failure
        os.close(stdout_r)
        os.close(stdout_w)
        os.close(stderr_r)
        os.close(stderr_w)
        raise CLKDGExecutionError(f"Failed to fork child process: {err}")

    # =========================================================================
    # CHILD PROCESS BRANCH (pid == 0)
    # =========================================================================
    if pid == 0:
        try:
            # 1. Close unneeded read descriptors in child
            os.close(stdout_r)
            os.close(stderr_r)

            # 2. Redirect standard stdout (1) and stderr (2) to pipe write ends
            os.dup2(stdout_w, 1)
            os.dup2(stderr_w, 2)

            # 3. Close write descriptors after duplicating
            os.close(stdout_w)
            os.close(stderr_w)

            # 4. Construct complete argv array: [executable_name, arg1, arg2, ...]
            argv = [target] + target_args

            # 5. Replace child process image with target binary
            os.execvp(target, argv)
        except Exception as err:
            # If execvp fails (e.g. target binary not found or no permission),
            # print error to redirected stderr and exit child cleanly.
            sys.stderr.write(f"CLI-KDG execvp error: {err}\n")
            sys.stderr.flush()
            os._exit(127)  # POSIX convention for command execution failure

    # =========================================================================
    # PARENT PROCESS BRANCH (pid > 0)
    # =========================================================================
    # 1. Parent does not write to pipes; close write ends immediately.
    # Essential to allow EOF detection when child closes its write descriptors.
    os.close(stdout_w)
    os.close(stderr_w)

    # 2. Set read ends to non-blocking mode to prevent select/read deadlocks
    _set_nonblocking(stdout_r)
    _set_nonblocking(stderr_r)

    stdout_bytes = bytearray()
    stderr_bytes = bytearray()

    readable_fds = [stdout_r, stderr_r]
    fd_map = {stdout_r: stdout_bytes, stderr_r: stderr_bytes}

    termination_type = TerminationType.EXITED
    exit_code: Optional[int] = None
    error_msg: Optional[str] = None
    child_exited = False

    try:
        while True:
            now = time.monotonic()

            # Check timeout deadline
            if deadline is not None and now >= deadline:
                termination_type = TerminationType.TIMED_OUT
                error_msg = f"Execution exceeded timeout limit of {timeout} seconds."

                # Send SIGKILL to forcibly terminate unresponsive child
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Child already exited

                # Synchronously harvest and reap child zombie process
                _, status = os.waitpid(pid, 0)
                child_exited = True
                break

            # Calculate remaining timeout duration for non-blocking select wait
            if deadline is not None:
                select_timeout = max(0.0, min(0.1, deadline - now))
            else:
                select_timeout = 0.1

            # Wait for pipe activity if readable descriptors remain open
            if readable_fds:
                r_ready, _, _ = select.select(readable_fds, [], [], select_timeout)
                for fd in r_ready:
                    try:
                        chunk = os.read(fd, 4096)
                        if chunk:
                            fd_map[fd].extend(chunk)
                        else:
                            # EOF reached; child closed writer descriptor
                            readable_fds.remove(fd)
                    except (OSError, BlockingIOError):
                        pass

            # Non-blocking check for child exit status
            if not child_exited:
                try:
                    wpid, status = os.waitpid(pid, os.WNOHANG)
                    if wpid == pid:
                        child_exited = True
                        if os.WIFEXITED(status):
                            exit_code = os.WEXITSTATUS(status)
                            termination_type = TerminationType.EXITED
                            if exit_code == 127 and b"CLI-KDG execvp error" in stderr_bytes:
                                termination_type = TerminationType.START_FAILED
                                error_msg = f"Failed to execute target binary '{target}'."
                        elif os.WIFSIGNALED(status):
                            exit_code = None
                            termination_type = TerminationType.SIGNALED
                            sig = os.WTERMSIG(status)
                            error_msg = f"Target process terminated by signal {sig}."
                        break
                except ChildProcessError:
                    child_exited = True
                    break

        # Drain any remaining bytes left in pipes after process exit
        for fd in readable_fds:
            while True:
                try:
                    chunk = os.read(fd, 4096)
                    if not chunk:
                        break
                    fd_map[fd].extend(chunk)
                except (OSError, BlockingIOError):
                    break

    finally:
        # Guarantee pipe read file descriptors are closed
        os.close(stdout_r)
        os.close(stderr_r)

    runtime_ms = (time.monotonic() - start_time) * 1000.0

    stdout_str = stdout_bytes.decode("utf-8", errors="replace")
    stderr_str = stderr_bytes.decode("utf-8", errors="replace")

    return ExecutionResult(
        command=target,
        arguments=target_args,
        exit_code=exit_code,
        stdout=stdout_str,
        stderr=stderr_str,
        runtime_ms=runtime_ms,
        termination_type=termination_type,
        error=error_msg
    )
