# CLI-KDG — Execution & Observation Engine

CLI-KDG (CLI Known Deterministic Generator / Observer) is a zero-dependency process execution and observation engine built strictly using Python standard library primitives and low-level POSIX process system calls.

---

## Technical Philosophy & Constraints

1. **Zero Third-Party Packages**:
   - Built exclusively with Python 3.11+ standard library modules (`os`, `sys`, `time`, `select`, `signal`, `fcntl`).
   - `pip install` is never required. Zero external dependencies.
2. **Low-Level POSIX System Calls**:
   - Avoids high-level process wrappers (`subprocess` module).
   - Executes target binaries via direct POSIX primitives: `os.pipe()`, `os.fork()`, `os.dup2()`, `os.execvp()`, `os.waitpid()`, `os.kill()`, `select.select()`.
3. **Pipe Deadlock Prevention**:
   - Sets pipe read descriptors to non-blocking mode via `fcntl`.
   - Uses `select.select()` I/O multiplexing to incrementally harvest STDOUT and STDERR streams without blocking or deadlocking on large outputs.
4. **Deterministic Resource Reaping**:
   - Enforces immediate closure of unused pipe ends in parent and child processes.
   - Guarantees child process reaping via `os.waitpid()` on normal exit, signal termination, or timeout killing (preventing zombie processes).
5. **No Uncaught Tracebacks**:
   - Normal CLI usage errors or execution start failures output clean human-readable error messages without exposing Python stack traces.

---

## Process Lifecycle Architecture

```text
               +----------------------+
               |    CLI-KDG Parent    |
               +----------------------+
                          |
                      os.pipe()
                     (stdout/stderr)
                          |
                      os.fork()
                      /       \
                     /         \
        +-----------------+   +------------------+
        | Parent Process  |   |  Child Process   |
        +-----------------+   +------------------+
        | - Close write   |   | - Close read     |
        |   descriptors   |   |   descriptors    |
        | - Non-blocking  |   | - os.dup2()      |
        |   fcntl         |   |   (stdout/stderr)|
        | - select() loop |   | - os.execvp()    |
        | - waitpid()     |   +------------------+
        +-----------------+
```

---

## Exhaustive Command Reference (CLI-KDG v1.1 & v1.2 Foundation)

Every single command syntax supported by CLI-KDG is documented below:

### 1. Primary Execution Subcommand (`run`)

| Invocation Form | Command Syntax | Description |
| :--- | :--- | :--- |
| **Executable Script** | `python3 cli_kdg.py run <target> [target_args...]` | Runs `<target>` binary with optional arguments using `cli_kdg.py`. |
| **Direct Execution** | `./cli_kdg.py run <target> [target_args...]` | Runs executable script directly when `chmod +x` is set. |
| **Python Module** | `python3 -m cli_kdg run <target> [target_args...]` | Invokes CLI-KDG as a Python module package (`cli_kdg`). |

### 2. Timeout Configuration Flags

| Flag Variant | Command Syntax Example | Behavior |
| :--- | :--- | :--- |
| **`--timeout` Space Separated** | `python3 cli_kdg.py run --timeout 5.0 <target> [args]` | Enforces execution limit of `5.0` seconds. |
| **`-t` Short Flag** | `python3 cli_kdg.py run -t 2.5 <target> [args]` | Short alias for timeout limit of `2.5` seconds. |
| **`--timeout=` Equals Syntax** | `python3 cli_kdg.py run --timeout=10 <target> [args]` | Inline key-value assignment for timeout of `10` seconds. |

### 3. Explicit Option Separator (`--`)

| Command Syntax | Description |
| :--- | :--- |
| `python3 cli_kdg.py run --timeout 5 -- <target> [args]` | Explicitly separates CLI-KDG options from target flags (prevents flag confusion if target uses `-t` or `--timeout`). |

### 4. Automated Test Suite Execution

| Command Syntax | Description |
| :--- | :--- |
| `python3 run_tests.py` | Runs the 14-test zero-dependency automated unit and integration test suite. |

---

## Detailed Command Examples

### Example 1: Standard Command Execution
```bash
python3 cli_kdg.py run python3 fixtures/success.py
```
**Output**:
```text
CLI-KDG v1.1
────────────────────────
Command: python3 fixtures/success.py
Exit:    0
Runtime: 18.08 ms

STDOUT
Execution successful!

STDERR
<empty>

STATUS: SUCCESS
```

### Example 2: Short Flag Timeout Execution
```bash
python3 cli_kdg.py run -t 1.0 python3 fixtures/slow.py
```
**Output**:
```text
CLI-KDG v1.1
────────────────────────
Command: python3 fixtures/slow.py
Exit:    <none>
Runtime: 1006.57 ms

STDOUT
Starting long-running process...

STDERR
<empty>

ERROR: Execution exceeded timeout limit of 1.0 seconds.

STATUS: TIMEOUT
```

### Example 3: Target Arguments & Option Separator
```bash
python3 cli_kdg.py run --timeout 3 -- python3 fixtures/mixed_output.py --verbose
```

---

## Project Structure

```text
CLI-KDG/
├── cli_kdg/
│   ├── __init__.py      # Package metadata & version string
│   ├── __main__.py      # Module entry point (python3 -m cli_kdg)
│   ├── errors.py        # Exception hierarchy & clean error formatting
│   ├── models.py        # ExecutionResult & TerminationType state models
│   ├── parser.py        # Manual sys.argv parser (zero argparse dependency)
│   ├── process.py       # POSIX process engine (fork, execvp, dup2, waitpid)
│   └── reporter.py      # Human-readable report formatting engine
├── fixtures/            # Test targets for verification
│   ├── failure.py
│   ├── large_output.py
│   ├── mixed_output.py
│   ├── slow.py
│   └── success.py
├── cli_kdg.py           # Top-level executable entry point script
├── run_tests.py         # Zero-dependency automated test suite
├── memory.md            # Continuous memory state & implementation log
└── README.md            # Exhaustive human-interpretable system documentation
```
