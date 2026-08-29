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
│   ├── discover.py      # Automated discovery orchestration engine (v1.2)
│   ├── errors.py        # Exception hierarchy & clean error formatting
│   ├── generator.py     # Deterministic test case generator (v1.2)
│   ├── help_parser.py   # Manual CLI help text parser (v1.2)
│   ├── models.py        # Data models (ExecutionResult, CLIModel, TestCase, DiscoveryResult)
│   ├── parser.py        # Manual sys.argv parser (run and discover subcommands)
│   ├── process.py       # POSIX process engine (fork, execvp, dup2, waitpid)
│   └── reporter.py      # Human-readable report formatting engine (v1.1 & v1.2)
├── fixtures/            # Test targets for verification
│   ├── cli_target.py    # Mock CLI target for v1.2 discovery testing
│   ├── failure.py
│   ├── large_output.py
│   ├── mixed_output.py
│   ├── slow.py
│   └── success.py
├── .github/workflows/
│   ├── ci.yml           # GitHub Actions CI matrix (Python 3.11, 3.12, 3.13)
│   └── release.yml      # Release archive packaging & SHA256 checksum publisher
├── cli_kdg.py           # Top-level executable entry point script
├── run_tests.py         # Zero-dependency automated test suite (26 passing tests)
├── memory.md            # Continuous memory state & implementation log
└── README.md            # Exhaustive human-interpretable system documentation
```

---

## CLI-KDG v1.2 — Automated Discovery & Test Generation Engine

CLI-KDG v1.2 introduces automated target interrogation and deterministic test case authoring on top of the v1.1 POSIX process execution engine.

### 1. Architectural Concept

Instead of requiring manual test case construction, v1.2 interrogates an unfamiliar target binary's `--help` output, extracts option specifications, constructs a structured `CLIModel`, generates bounded test cases, and executes them through the POSIX process engine.

```text
target → --help → parse options → CLIModel → generate TestCase[] → v1.1 execution → report
```

### 2. Exhaustive v1.2 Command Matrix & Syntax Patterns

Every invocation pattern supported by the `discover` subcommand in CLI-KDG v1.2:

| Invocation Pattern | Command Syntax Example | Description |
| :--- | :--- | :--- |
| **Executable Script** | `python3 cli_kdg.py discover <target> [target_args]` | Interrogates `<target>` help output, extracts option specifications, generates deterministic test cases, and executes them. |
| **Direct Shell Execution** | `./cli_kdg.py discover <target> [target_args]` | Direct executable script invocation when `chmod +x cli_kdg.py` is enabled. |
| **Python Package Module** | `python3 -m cli_kdg discover <target> [target_args]` | Invokes the discovery engine as a Python package module (`cli_kdg`). |
| **Timeout Flag (Space)** | `python3 cli_kdg.py discover --timeout 5.0 <target>` | Enforces an execution timeout limit of `5.0` seconds for every generated test case. |
| **Timeout Flag (Short)** | `python3 cli_kdg.py discover -t 2.5 <target>` | Short flag alias enforcing a `2.5` second execution limit per test case. |
| **Timeout Flag (Equals)**| `python3 cli_kdg.py discover --timeout=3.0 <target>` | Inline key-value assignment syntax for timeout limit (`3.0` seconds). |
| **Option Separator** | `python3 cli_kdg.py discover --timeout 5 -- <target>` | Explicit `--` separator isolating CLI-KDG flags from target options. |
| **Automated Test Suite** | `python3 run_tests.py` | Runs the full 26-test zero-dependency automated unit, AST import audit, and integration test suite. |

### 3. Supported Help Option Grammar (`help_parser.py`)

The manual help text parser recognizes common CLI option declarations without regex or external libraries:

- `--verbose` (Boolean Flag)
- `--output FILE` or `--output=FILE` (Value-requiring option with descriptor)
- `-o` (Short boolean flag)
- `-o FILE` or `-o=FILE` (Short value-requiring option)
- `-o, --output FILE` (Combined short and long option)

### 4. Deterministic Test Case Classification (`generator.py`)

Generated test cases are bounded (maximum 15 cases) and categorized into clear test classifications:

- **`HELP`**: Verifies standard `--help` execution.
- **`UNKNOWN_OPTION`**: Verifies error handling when an invalid flag (`--unknown-flag-xyz-kdg`) is passed.
- **`FLAG_VALID`**: Verifies boolean flag activation (e.g., `--verbose`).
- **`FLAG_UNEXPECTED_ARG`**: Verifies behavior when a boolean flag receives an unexpected positional argument.
- **`OPTION_MISSING_VAL`**: Verifies error handling when an option value is omitted.
- **`OPTION_VALID_VAL`**: Verifies option execution with valid string or numeric boundary arguments (e.g. `0`).
- **`OPTION_INVALID_VAL`**: Verifies numeric option behavior when given negative (`-1`) or non-numeric (`abc`) strings.

### 5. Detailed Discovery Command Example

```bash
python3 cli_kdg.py discover python3 fixtures/cli_target.py
```

**Output**:
```text
CLI-KDG Discovery & Test Execution Report (v1.2)
==================================================
Target:               python3 fixtures/cli_target.py
Help Interrogation:   Exit 0 (17.24 ms)
Discovered Options:   4
Generated Test Cases: 12
==================================================

Discovered Option Specifications:
  • -h, --help
  • -v, --verbose
  • -o, --output FILE
  • --count INTEGER

==================================================

Executed Test Cases:
--------------------------------------------------
[1/12] Category: HELP
Command:  python3 fixtures/cli_target.py --help
Reason:   Verify standard help flag execution
Outcome:  Exit 0 | Runtime: 16.14 ms | Status: SUCCESS
--------------------------------------------------
[2/12] Category: UNKNOWN_OPTION
Command:  python3 fixtures/cli_target.py --unknown-flag-xyz-kdg
Reason:   Verify unknown option handling and error reporting
Outcome:  Exit 2 | Runtime: 15.94 ms | Status: EXITED
STDERR:
  Error: Unrecognized option '--unknown-flag-xyz-kdg'
--------------------------------------------------
[5/12] Category: FLAG_VALID
Command:  python3 fixtures/cli_target.py --verbose
Reason:   Verify boolean flag '--verbose' activation
Outcome:  Exit 0 | Runtime: 15.42 ms | Status: SUCCESS
--------------------------------------------------
[7/12] Category: OPTION_MISSING_VAL
Command:  python3 fixtures/cli_target.py --output
Reason:   Verify error handling when value for option '--output' is omitted
Outcome:  Exit 1 | Runtime: 15.58 ms | Status: EXITED
STDERR:
  Error: Option '--output' requires a FILE argument.
--------------------------------------------------
[10/12] Category: OPTION_VALID_VAL
Command:  python3 fixtures/cli_target.py --count 0
Reason:   Verify numeric option '--count' with zero boundary value
Outcome:  Exit 0 | Runtime: 15.49 ms | Status: SUCCESS
--------------------------------------------------
[11/12] Category: OPTION_INVALID_VAL
Command:  python3 fixtures/cli_target.py --count -1
Reason:   Verify numeric option '--count' with negative value
Outcome:  Exit 1 | Runtime: 15.46 ms | Status: EXITED
STDERR:
  Error: '--count' must be non-negative.
--------------------------------------------------
DISCOVERY STATUS: SUCCESS
```

---

## CLI-KDG v1.3 — Snapshot, Replay & Behavioral Regression Engine

CLI-KDG v1.3 introduces historical test observation persistence (`snapshot`) and exact behavioral regression comparison (`replay`) on top of the v1.1 process engine and v1.2 discovery parser.

### 1. Architectural Concept

Instead of regenerating test cases before comparison, v1.3 freezes historical `TestCase` observations into a versioned JSON snapshot, replays the exact same test cases against a later version of the target CLI, and compares observable behavior field-by-field.

```text
SNAPSHOT (v1.2 discovery → JSON format version 1)
   │
   ├── later version of target CLI
   │
REPLAY (execute exact stored TestCase[] objects)
   │
COMPARE (field-by-field discrepancy analysis)
   │
REGRESSION REPORT (UNCHANGED / CHANGED / FAILED)
```

### 2. Exhaustive v1.3 Command Matrix & Syntax Patterns

Every invocation pattern supported by `snapshot` and `replay` subcommands:

| Invocation Pattern | Command Syntax Example | Description |
| :--- | :--- | :--- |
| **Snapshot Creation (Default Output)** | `python3 cli_kdg.py snapshot <target> [target_args]` | Runs discovery on `<target>`, collects observations, and saves to `snapshot.json`. |
| **Snapshot Custom Output (`--output`)** | `python3 cli_kdg.py snapshot --output v1_base.json <target>` | Saves baseline snapshot to specified output file path (`v1_base.json`). |
| **Snapshot Short Flag (`-o`)** | `python3 cli_kdg.py snapshot -o v1_base.json <target>` | Short flag alias for custom output file destination. |
| **Snapshot Direct Execution** | `./cli_kdg.py snapshot -o v1_base.json <target>` | Direct executable script invocation for snapshot creation. |
| **Snapshot Python Module** | `python3 -m cli_kdg snapshot -o v1_base.json <target>` | Module invocation of snapshot creation engine. |
| **Replay Baseline Snapshot** | `python3 cli_kdg.py replay v1_base.json <target_v2>` | Replays stored historical test cases against `<target_v2>` and reports behavioral changes. |
| **Replay with Timeout Limit** | `python3 cli_kdg.py replay --timeout 5.0 v1_base.json <target>` | Enforces a `5.0` second limit per replayed test case execution. |
| **Replay Direct Execution** | `./cli_kdg.py replay v1_base.json <target_v2>` | Direct executable script invocation of replay engine. |
| **Replay Python Module** | `python3 -m cli_kdg replay v1_base.json <target_v2>` | Module invocation of replay engine. |
| **Automated Test Suite** | `python3 run_tests.py` | Runs full 35-test zero-dependency automated unit, AST import audit, and integration test suite. |

### 3. Versioned Snapshot Schema Format (`snapshot.py`)

Snapshots are serialized in human-readable JSON format with explicit format versioning (`version: 1`):

```json
{
  "version": 1,
  "cli_kdg_version": "1.3.0",
  "created_at": "2026-08-29T14:16:49Z",
  "target": "python3",
  "target_args": ["fixtures/cli_target.py"],
  "observations": [
    {
      "arguments": ["--count", "0"],
      "category": "OPTION_VALID_VAL",
      "reason": "Verify numeric option '--count' with zero boundary value",
      "exit_code": 0,
      "stdout": "Executed. Output: None, Count: 0",
      "stderr": "",
      "runtime_ms": 15.49,
      "termination_type": "EXITED"
    }
  ]
}
```

### 4. Behavioral Comparison & Runtime Invariance (`replay.py`)

During `replay`, baseline observations and current execution results are compared across observable fields:

- **`exit_code`**: Process exit status code comparison.
- **`status`**: Success classification (`is_success()`) comparison.
- **`stdout`**: Captured standard output text comparison.
- **`stderr`**: Captured standard error text comparison.
- **`termination_type`**: POSIX process termination classification.

> [!NOTE]
> **Runtime Invariance**: Execution duration (`runtime_ms`) is metadata and is **never** used to trigger behavioral regressions.

### 5. Classification Outcomes

- **`UNCHANGED`**: All observable behavior fields match the baseline snapshot.
- **`CHANGED`**: Observable exit code, stdout, stderr, or status differs from baseline.
- **`FAILED`**: Target executable failed to start or raised execution errors.

### 6. Snapshot & Replay Command Example

```bash
# 1. Create baseline snapshot of v1 CLI target
python3 cli_kdg.py snapshot --output v1_snap.json python3 fixtures/cli_target.py

# 2. Replay snapshot against v2 CLI target to detect regressions
python3 cli_kdg.py replay v1_snap.json python3 fixtures/cli_target_v2.py
```

**Replay Output**:
```text
CLI-KDG Behavioral Regression & Replay Report (v1.3)
==================================================
Snapshot Path:        v1_snap.json
Replay Target:        python3 fixtures/cli_target_v2.py
Total Test Cases:     12
Unchanged Behavior:   4
Changed Behavior:     8
Execution Failures:   0
==================================================

Replay Test Case Details:
--------------------------------------------------
[10/12] Classification: CHANGED
Category: OPTION_VALID_VAL
Command:  python3 fixtures/cli_target_v2.py --count 0
Reason:   Verify numeric option '--count' with zero boundary value
Outcome:  Exit 1 | Runtime: 15.12 ms | Status: EXITED
Behavioral Discrepancies:
  • Field 'exit_code':
      Baseline: 0
      Current:  1
  • Field 'status':
      Baseline: SUCCESS
      Current:  FAILURE
  • Field 'stdout':
      Baseline: Executed. Output: None, Count: 0
      Current:  <empty>
  • Field 'stderr':
      Baseline: <empty>
      Current:  Error: '--count' must be strictly positive.
--------------------------------------------------
REPLAY RESULT: BEHAVIORAL_REGRESSIONS_DETECTED
```



