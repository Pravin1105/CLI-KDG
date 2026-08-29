# Memory State — CLI-KDG

## Project Identity
- **Name**: CLI-KDG (CLI Known Deterministic Generator / Execution Engine)
- **Previous Identifier**: CLIProbe (Fully Deprecated & Replaced across all files & docs)
- **Current Version Phase**: **v1.2 Initiation Phase** (v1.1 baseline fully locked & verified)
- **Architectural Paradigm**: Zero third-party packages, pure Python standard library + POSIX low-level process primitives (`fork`, `execvp`, `pipe`, `dup2`, `waitpid`, `kill`, `select`, `fcntl`).

---

## Technical Constraints & Senior Developer Invariants
1. **Zero External Dependencies**: Strictly no `pip` packages, third-party libraries, or high-level process wrappers (`subprocess` module).
2. **Minimal & Readable Codebase**: Clean, modular structure with human-interpretable docstrings detailing every low-level POSIX call.
3. **Controlled Error Paths**: Normal CLI user syntax errors and binary start failures produce human-readable error reports with zero uncaught Python tracebacks.
4. **Pipe Deadlock Protection**: STDOUT and STDERR pipes configured in non-blocking mode via `fcntl` and multiplexed via `select.select()` to prevent deadlocks on large I/O outputs.
5. **Deterministic Child Reaping**: All processes (normal exit, signal terminated, or timed out) are strictly reaped using `os.waitpid()` to prevent zombie process creation.

---

## Complete CLI-KDG Command Matrix

Every command invocation pattern supported by CLI-KDG:

| Invocation Form | Syntax Pattern | Example Command |
| :--- | :--- | :--- |
| **Executable Script** | `python3 cli_kdg.py run <target> [args]` | `python3 cli_kdg.py run python3 fixtures/success.py` |
| **Direct Binary Shell** | `./cli_kdg.py run <target> [args]` | `./cli_kdg.py run python3 fixtures/success.py` |
| **Python Module** | `python3 -m cli_kdg run <target> [args]` | `python3 -m cli_kdg run python3 fixtures/success.py` |
| **Timeout Flag (Long)** | `python3 cli_kdg.py run --timeout <SEC> <target>` | `python3 cli_kdg.py run --timeout 2.5 python3 fixtures/slow.py` |
| **Timeout Flag (Short)** | `python3 cli_kdg.py run -t <SEC> <target>` | `python3 cli_kdg.py run -t 1.0 python3 fixtures/slow.py` |
| **Timeout Flag (Equals)**| `python3 cli_kdg.py run --timeout=<SEC> <target>` | `python3 cli_kdg.py run --timeout=1.0 python3 fixtures/slow.py` |
| **Option Separator** | `python3 cli_kdg.py run --timeout 5 -- <target>` | `python3 cli_kdg.py run --timeout 5 -- python3 fixtures/success.py` |
| **Automated Test Suite**| `python3 run_tests.py` | `python3 run_tests.py` |

---

## Component Inventory & Memory Map

| File | Purpose | Status |
| :--- | :--- | :--- |
| `cli_kdg/__init__.py` | Package identity & version | Locked (v1.1) |
| `cli_kdg/models.py` | Dataclasses for `ExecutionResult` and `TerminationType` | Locked (v1.1) |
| `cli_kdg/errors.py` | Custom error exceptions (`CLKDGUserError`, `CLKDGExecutionError`) | Locked (v1.1) |
| `cli_kdg/parser.py` | Manual `sys.argv` parser supporting `run [--timeout SEC] <target>` | Locked (v1.1) |
| `cli_kdg/process.py` | POSIX execution engine (`fork`, `dup2`, `execvp`, `waitpid`, `kill`, `select`) | Locked (v1.1) |
| `cli_kdg/reporter.py` | Formatter generating human-readable observation reports | Locked (v1.1) |
| `cli_kdg/__main__.py` | Main module execution entry point (`python3 -m cli_kdg`) | Locked (v1.1) |
| `cli_kdg.py` | Single-file executable entry point (`chmod +x cli_kdg.py`) | Locked (v1.1) |
| `run_tests.py` | Automated test suite (21/21 tests passing: 14 unit, 2 dependency audit, 5 CLI integration) | Updated |
| `.github/workflows/ci.yml` | GitHub Actions CI matrix (Python 3.11, 3.12, 3.13) | Locked |
| `.github/workflows/release.yml` | GitHub Actions release packaging & checksum publisher | Locked |
| `README.md` | Complete system documentation & exhaustive command reference | Updated |
| `memory.md` | Continuous memory tracking & architecture state log | Updated for v1.2 |

---

## Transition Log — Phase v1.2 Initiation

- **v1.1.0 Release Baseline Tagged**: Tag `v1.1.0` applied to baseline commit (`0e96351`) and pushed to GitHub `origin`.
- **Branch Strategy**: Branch `develop/v1.2` established and synced with `main`.
- **CI/CD Pipeline Activated**: Added `.github/workflows/ci.yml` testing Python 3.11, 3.12, and 3.13 on `ubuntu-latest`.
- **Zero-Third-Party Dependency Audit**: Implemented AST static analysis (`TestDependencyPolicy`) verifying zero `site-packages` or third-party module imports and zero external package manifests.
- **Integration Test Suite**: Expanded test suite to 21 tests covering direct executable script execution, module invocation (`python3 -m cli_kdg`), short/long timeout flags, option separators, and non-traceback error handling.
- **Automated Release Packaging**: Added `.github/workflows/release.yml` to package tarball/zip archives and publish SHA256 checksums upon tag release.
- **Verification**: Local and remote release bundle and test execution verified cleanly.
- **Status**: Completed items 1-9. Commencing v1.2 architecture design phase.

