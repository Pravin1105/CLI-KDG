# CLI-KDG — System Documentation & Architecture Reference

**CLI-KDG (CLI Known Data Generator & Behavioral Regression Engine)** is a lightweight, zero-dependency command-line testing framework designed to interrogate CLI applications, auto-generate deterministic test cases, freeze historical behavioral snapshots, and detect regression diffs across application releases.

---

## 1. Project Overview & Core Purpose

CLI-KDG provides an end-to-end testing lifecycle for command-line tools without requiring external dependencies, package managers, or third-party libraries.

### Core System Capabilities:
- **`run` Subcommand**: Executes arbitrary CLI binaries under isolated POSIX process supervision with strict STDOUT/STDERR pipe separation, deadlock protection, and monotonic timeout enforcement.
- **`discover` Subcommand**: Interrogates target `--help` interfaces, parses option specifications, generates bounded deterministic test cases, and executes them.
- **`snapshot` Subcommand**: Freezes historical test execution observations (`exit_code`, `status`, `stdout`, `stderr`, `termination_type`) into versioned JSON artifacts (`version: 1`).
- **`replay` Subcommand**: Re-executes stored historical test cases against updated target binaries and performs field-by-field comparative regression analysis.

---

## 2. Zero External Dependency Architecture

CLI-KDG strictly enforces a **Zero Third-Party Package Policy**. The entire codebase relies exclusively on the Python standard library and low-level POSIX operating system primitives.

### Standard Library Modules Used:
- `sys`, `os`: Environment interaction, process management, and file descriptor manipulation.
- `time`: Monotonic timing measurements (`time.monotonic()`) and UTC timestamp formatting.
- `select`, `fcntl`: Non-blocking I/O multiplexing and asynchronous pipe flag configuration (`O_NONBLOCK`).
- `signal`: POSIX process termination signals (`SIGTERM`, `SIGKILL`).
- `json`: Versioned snapshot serialization and parsing.
- `ast`, `importlib`: Automated AST import auditing verifying zero external `site-packages` references.
- `unittest`: Built-in automated unit, policy, and integration test execution.

### Low-Level POSIX System Calls:
Instead of high-level process wrappers or external packages, CLI-KDG directly manages child process lifecycles via:
- `os.fork()`: Creates isolated child process contexts.
- `os.pipe()`: Sets up independent non-blocking file descriptors for standard output and standard error streams.
- `os.dup2()`: Redirects child file descriptors to pipe write handles.
- `os.execvp()`: Replaces child process image with target binary.
- `os.waitpid()`: Reaps child process exit status non-blockingly (`WNOHANG`).
- `os.kill()`: Issues termination signals on deadline expiration.

---

## 3. System Workflow Architecture

```text
1. EXECUTION WORKFLOW (run)
Target Command ──> POSIX fork() ──> Isolated STDOUT/STDERR Pipes ──> Select Loop ──> Report (0/1/2)

2. DISCOVERY WORKFLOW (discover)
Target --help ──> Manual Parser ──> CLIModel ──> Deterministic Generator ──> Execute Cases ──> Report

3. SNAPSHOT WORKFLOW (snapshot)
Target CLI ──> Run Discovery ──> Collect TestObservations ──> JSON Serialization (v1) ──> File (.json)

4. REPLAY WORKFLOW (replay)
Snapshot JSON ──> Reconstruct TestCases ──> Execute on Target v2 ──> Compare Fields ──> Regression Report
```

---

## 4. Version History & Feature Matrix

| Version | Milestone Features | Exit Code Contract | Standard Library Audit |
| :--- | :--- | :--- | :--- |
| **v1.1.0** | POSIX Process Engine (`run`), STDOUT/STDERR pipe isolation, deadlock protection, monotonic timeout, clean error formatting. | `0` (Success)<br>`1` (Target Failure)<br>`2` (CLI Syntax Error) | PASSED (Zero external packages) |
| **v1.2.0** | Automated CLI `--help` interrogation, manual text parser (`help_parser.py`), deterministic test case generator (`generator.py`), `discover` subcommand. | `0` (Success)<br>`1` (Discovery Failure)<br>`2` (CLI Syntax Error) | PASSED (Zero external packages) |
| **v1.3.0** | Snapshot persistence (`snapshot`), versioned format schema (`version: 1`), exact test replayer & field comparator (`replay`), runtime invariance. | `0` (No Regressions)<br>`1` (Regressions/Failure)<br>`2` (CLI Syntax Error) | PASSED (Zero external packages) |

---

## 5. Detailed Release Change Logs

### v1.3.0 Change Log (Snapshot, Replay & Codebase Minimalism Optimization)
- **Added**: `snapshot` subcommand to freeze historical discovery observations into versioned JSON snapshot artifacts (`cli_kdg/snapshot.py`).
- **Added**: `replay` subcommand to re-execute stored test cases and compare exit codes, status, stdout, stderr, and termination types (`cli_kdg/replay.py`).
- **Added**: Field-by-field comparative analyzer enforcing **Runtime Invariance** (runtime duration is metadata and never causes regression diffs).
- **Added**: Mock CLI target v2 fixture (`fixtures/cli_target_v2.py`) for automated behavioral regression testing.
- **Refactored**: Codebase minimalism optimization reducing total lines by **31% (-841 lines)** while keeping 100% test pass rate.

### v1.2.0 Change Log (Automated CLI Interrogation & Test Case Generation)
- **Added**: `discover` subcommand to interrogate target `--help` output (`cli_kdg/discover.py`).
- **Added**: Manual `--help` output text parser supporting standard flag syntax without regex (`cli_kdg/help_parser.py`).
- **Added**: Deterministic test case generator producing bounded test cases (`HELP`, `UNKNOWN_OPTION`, `FLAG_VALID`, `OPTION_MISSING_VAL`, `OPTION_VALID_VAL`, `OPTION_INVALID_VAL`) (`cli_kdg/generator.py`).
- **Added**: Mock CLI target fixture (`fixtures/cli_target.py`).

### v1.1.0 Change Log (POSIX Process Engine Baseline)
- **Added**: Single-file executable entry point (`cli_kdg.py`) and package router (`cli_kdg/__main__.py`).
- **Added**: Manual argument parser (`cli_kdg/parser.py`) supporting `--timeout` flags and `--` option separators.
- **Added**: POSIX process engine with `fork`, `execvp`, `dup2`, `pipe`, `waitpid`, and non-blocking `select` I/O multiplexing (`cli_kdg/process.py`).
- **Added**: Human-readable report formatting engine (`cli_kdg/reporter.py`).
- **Added**: GitHub Actions CI/CD workflows (`ci.yml`, `release.yml`) and AST import auditor (`run_tests.py`).

---

## 6. Building & Running CLI-KDG

### One-Line Test & Build Command:
```bash
python3 run_tests.py
```

### One-Line Release Package Build Command:
```bash
git archive --format=tar.gz --prefix=cli-kdg-v1.3.0/ -o cli-kdg-v1.3.0.tar.gz HEAD
```

### Execution Command Reference:

```bash
# 1. Direct Execution Run (supervised process execution)
python3 cli_kdg.py run python3 fixtures/success.py

# 2. Automated Discovery Run (interrogate help and execute generated cases)
python3 cli_kdg.py discover python3 fixtures/cli_target.py

# 3. Create Baseline Snapshot
python3 cli_kdg.py snapshot --output v1_base.json python3 fixtures/cli_target.py

# 4. Replay Snapshot against Target v2 to Detect Regressions
python3 cli_kdg.py replay v1_base.json python3 fixtures/cli_target_v2.py
```

---

## 7. Explicit System Limitations

1. **POSIX Operating System Requirement**:
   CLI-KDG relies directly on POSIX process semantics (`fork`, `execvp`, `dup2`, `pipe`, `waitpid`, `kill`, `select`). It requires Linux, macOS, or BSD systems and cannot run directly on native Windows `cmd.exe` or PowerShell without a POSIX compatibility layer (e.g. WSL).

2. **Single-Level CLI Subcommand Parsing**:
   The automated discovery parser interrogates top-level `--help` output. It does not recursively discover multi-nested subcommand trees (e.g. `tool sub1 sub2 --help`).

3. **Text-Based `--help` Formatting Dependency**:
   The `help_parser.py` module parses standard POSIX text option declarations (`-o`, `--option`, `--output FILE`). Custom non-standard help text formatting may result in unparsed options.

4. **Bounded Test Case Limit**:
   To guarantee bounded execution duration, `generator.py` caps generated test cases at a maximum of **15 test cases** per discovery run.

5. **Pipe Buffer Multiplexing Limit**:
   STDOUT and STDERR stream capture is multiplexed via non-blocking `select()` calls. Extremely large output bursts rely on OS pipe buffer capacities (typically 64 KB per pipe buffer before drain).

---

## 8. CLI Exit Code Contract

CLI-KDG strictly follows standard POSIX exit code conventions:

| Exit Code | Meaning | Triggers |
| :---: | :--- | :--- |
| **`0`** | **SUCCESS** | Execution completed cleanly, discovery succeeded, snapshot created, or replay detected zero behavioral regressions. |
| **`1`** | **FAILURE** | Target process exited with non-zero status, process timed out, execution failed, or replay detected behavioral regressions (`BEHAVIORAL_REGRESSIONS_DETECTED`). |
| **`2`** | **USER ERROR** | Invalid CLI-KDG invocation syntax, missing subcommand/target, unrecognized flag, or malformed timeout argument. |
