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

Every command invocation pattern supported by CLI-KDG (v1.1 & v1.2):

| Invocation Form | Syntax Pattern | Example Command |
| :--- | :--- | :--- |
| **Executable Script (Run)** | `python3 cli_kdg.py run <target> [args]` | `python3 cli_kdg.py run python3 fixtures/success.py` |
| **Executable Script (Discover)**| `python3 cli_kdg.py discover <target> [args]` | `python3 cli_kdg.py discover python3 fixtures/cli_target.py` |
| **Direct Binary Shell** | `./cli_kdg.py run <target> [args]` | `./cli_kdg.py run python3 fixtures/success.py` |
| **Python Module** | `python3 -m cli_kdg discover <target> [args]` | `python3 -m cli_kdg discover python3 fixtures/cli_target.py` |
| **Timeout Flag (Long)** | `python3 cli_kdg.py discover --timeout <SEC> <target>` | `python3 cli_kdg.py discover --timeout 2.5 python3 fixtures/cli_target.py` |
| **Timeout Flag (Short)** | `python3 cli_kdg.py run -t <SEC> <target>` | `python3 cli_kdg.py run -t 1.0 python3 fixtures/slow.py` |
| **Option Separator** | `python3 cli_kdg.py run --timeout 5 -- <target>` | `python3 cli_kdg.py run --timeout 5 -- python3 fixtures/success.py` |
| **Automated Test Suite**| `python3 run_tests.py` | `python3 run_tests.py` |

---

## Component Inventory & Memory Map

| File | Purpose | Status |
| :--- | :--- | :--- |
| `cli_kdg/__init__.py` | Package identity & version | Locked (v1.1) |
| `cli_kdg/models.py` | Dataclasses (`ExecutionResult`, `CLIOption`, `CLIModel`, `TestCase`, `DiscoveryResult`) | Updated (v1.2) |
| `cli_kdg/errors.py` | Custom error exceptions (`CLKDGUserError`, `CLKDGExecutionError`) | Locked (v1.1) |
| `cli_kdg/parser.py` | Manual `sys.argv` parser supporting `run` and `discover` subcommands | Updated (v1.2) |
| `cli_kdg/help_parser.py` | Manual CLI `--help` output parser (zero `argparse`/regex dependency) | Created (v1.2) |
| `cli_kdg/generator.py` | Deterministic test case generator with category classifications | Created (v1.2) |
| `cli_kdg/discover.py` | Automated discovery orchestration engine | Created (v1.2) |
| `cli_kdg/process.py` | POSIX process engine (`fork`, `dup2`, `execvp`, `waitpid`, `kill`, `select`) | Locked (v1.1) |
| `cli_kdg/reporter.py` | Formatter generating human-readable observation & discovery reports | Updated (v1.2) |
| `cli_kdg/__main__.py` | Main module execution entry point routing `run` and `discover` | Updated (v1.2) |
| `cli_kdg.py` | Single-file executable entry point (`chmod +x cli_kdg.py`) | Locked (v1.1) |
| `run_tests.py` | Automated test suite (26/26 tests passing: unit, AST audit, integration) | Updated (v1.2) |
| `fixtures/cli_target.py` | Mock CLI target fixture for v1.2 discovery testing | Created (v1.2) |
| `.github/workflows/ci.yml` | GitHub Actions CI matrix (Python 3.11, 3.12, 3.13) | Locked |
| `.github/workflows/release.yml` | GitHub Actions release packaging & checksum publisher | Locked |
| `README.md` | Complete system documentation (v1.1 intact + v1.2 appended) | Updated (v1.2) |
| `memory.md` | Continuous memory tracking & architecture state log | Updated for v1.2 |

---

## Transition Log — Phase v1.2 Completion

- **v1.2 Objective Achieved**: Built automated `--help` interrogation, structured option parsing (`CLIModel`), deterministic test case generation (`TestCase`), and execution through v1.1 POSIX process engine.
- **Zero Third-Party Dependency Invariant Enforced**: Pure Python standard library implementation (`sys`, `os`, `time`, `select`, `fcntl`, `ast`). Verified by AST import auditor in test suite.
- **Modular Component Structure**: Implemented `help_parser.py`, `generator.py`, and `discover.py`.
- **Test Suite Expansion**: Total passing tests increased from 21 to **26 tests**.
- **Documentation Standards**: Preserved v1.1 documentation in `README.md` without modification; appended `## CLI-KDG v1.2` section.
- **Git Commit State**: Staged in working tree without committing, awaiting senior developer review.


