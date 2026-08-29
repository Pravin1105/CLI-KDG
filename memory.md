# Memory State — CLI-KDG

## Project Identity
- **Name**: CLI-KDG (CLI Known Deterministic Generator & Behavioral Regression Engine)
- **Current Version**: **v1.3.0 Release Milestone**
- **Architectural Paradigm**: Zero third-party packages, pure Python standard library + POSIX low-level process primitives (`fork`, `execvp`, `pipe`, `dup2`, `waitpid`, `kill`, `select`, `fcntl`).

---

## Technical Constraints & Senior Developer Invariants
1. **Zero External Dependencies**: Strictly no `pip` packages, third-party libraries, or high-level process wrappers. Verified by AST import audit.
2. **Minimal & Readable Codebase**: Clean, modular structure with human-interpretable code and comments.
3. **Controlled Error Paths**: Normal CLI user syntax errors and start failures produce human-readable error reports with zero uncaught Python tracebacks.
4. **Pipe Deadlock Protection**: STDOUT and STDERR pipes configured in non-blocking mode via `fcntl` and multiplexed via `select.select()`.
5. **Deterministic Child Reaping**: All processes are strictly reaped using `os.waitpid()` to prevent zombie process creation.

---

## Complete CLI-KDG Command Matrix

| Invocation Form | Syntax Pattern | Example Command |
| :--- | :--- | :--- |
| **Executable Script (Run)** | `python3 cli_kdg.py run <target> [args]` | `python3 cli_kdg.py run python3 fixtures/success.py` |
| **Executable Script (Discover)**| `python3 cli_kdg.py discover <target> [args]` | `python3 cli_kdg.py discover python3 fixtures/cli_target.py` |
| **Executable Script (Snapshot)**| `python3 cli_kdg.py snapshot -o snap.json <target>`| `python3 cli_kdg.py snapshot -o snap.json python3 fixtures/cli_target.py` |
| **Executable Script (Replay)**  | `python3 cli_kdg.py replay snap.json <target>` | `python3 cli_kdg.py replay snap.json python3 fixtures/cli_target_v2.py` |
| **Direct Binary Shell** | `./cli_kdg.py run <target> [args]` | `./cli_kdg.py run python3 fixtures/success.py` |
| **Python Module** | `python3 -m cli_kdg replay snap.json <target>` | `python3 -m cli_kdg replay snap.json python3 fixtures/cli_target_v2.py` |
| **Timeout Flag (Long)** | `python3 cli_kdg.py replay --timeout <SEC> snap.json <target>` | `python3 cli_kdg.py replay --timeout 2.5 snap.json python3 fixtures/cli_target_v2.py` |
| **Timeout Flag (Short)** | `python3 cli_kdg.py run -t <SEC> <target>` | `python3 cli_kdg.py run -t 1.0 python3 fixtures/slow.py` |
| **Option Separator** | `python3 cli_kdg.py run --timeout 5 -- <target>` | `python3 cli_kdg.py run --timeout 5 -- python3 fixtures/success.py` |
| **Automated Test Suite**| `python3 run_tests.py` | `python3 run_tests.py` |

---

## Component Inventory & Memory Map

| File | Purpose | Status |
| :--- | :--- | :--- |
| `.zero-dep.toml` | Policy manifest declaring zero external package policy | Created |
| `deps-proof.txt` | Empirical audit report proving zero third-party dependencies | Created |
| `LICENSE` | MIT License open-source copyright notice | Created |
| `CLI-KDG_DOCUMENTATION.md` | Standalone comprehensive documentation (workflow, change logs, limitations) | Created |
| `cli_kdg/__init__.py` | Package identity & version | Locked (v1.1) |
| `cli_kdg/models.py` | Dataclasses (`ExecutionResult`, `CLIModel`, `Snapshot`, `TestObservation`, `ReplayResult`) | Updated (v1.3) |
| `cli_kdg/errors.py` | Custom error exceptions (`CLKDGUserError`, `CLKDGExecutionError`) | Locked (v1.1) |
| `cli_kdg/parser.py` | Manual `sys.argv` parser supporting `run`, `discover`, `snapshot`, `replay` | Updated (v1.3) |
| `cli_kdg/help_parser.py` | Manual CLI `--help` output parser (zero `argparse`/regex dependency) | Locked (v1.2) |
| `cli_kdg/generator.py` | Deterministic test case generator with category classifications | Locked (v1.2) |
| `cli_kdg/discover.py` | Automated discovery orchestration engine | Locked (v1.2) |
| `cli_kdg/snapshot.py` | Snapshot persistence & JSON serialization manager | Created (v1.3) |
| `cli_kdg/replay.py` | Snapshot replay & field-by-field behavioral comparator | Created (v1.3) |
| `cli_kdg/process.py` | POSIX process engine (`fork`, `dup2`, `execvp`, `waitpid`, `kill`, `select`) | Locked (v1.1) |
| `cli_kdg/reporter.py` | Formatter generating observation, discovery, snapshot & replay reports | Updated (v1.3) |
| `cli_kdg/__main__.py` | Main module execution entry point routing all subcommands | Updated (v1.3) |
| `cli_kdg.py` | Single-file executable entry point (`chmod +x cli_kdg.py`) | Locked (v1.1) |
| `run_tests.py` | Automated test suite (38/38 tests passing: unit, AST audit, exit code, integration) | Updated (v1.3) |
| `fixtures/cli_target.py` | Mock CLI target v1 fixture for discovery & snapshot testing | Created (v1.2) |
| `fixtures/cli_target_v2.py` | Mock CLI target v2 fixture for replay regression testing | Created (v1.3) |
| `.github/workflows/ci.yml` | GitHub Actions CI matrix (Python 3.11, 3.12, 3.13) | Locked |
| `.github/workflows/release.yml` | GitHub Actions release packaging & checksum publisher | Locked |
| `README.md` | Complete system documentation (v1.1, v1.2 intact + v1.3 appended) | Updated (v1.3) |
| `memory.md` | Continuous memory tracking & architecture state log | Updated for v1.3 |

---

## Transition Log — Phase v1.3 Release Verification Complete

- **Zero-Dependency Audit**: Verified zero external package manifests and generated `deps-proof.txt` empirical audit log.
- **Zero-Dependency Policy Manifest**: Added `.zero-dep.toml`.
- **System Documentation File**: Created `CLI-KDG_DOCUMENTATION.md` detailing system workflows, version history, change logs, one-line build commands, and explicit limitations.
- **CLI Exit Code Verification**: Added explicit tests for exit codes `0`, `1`, `2` into `run_tests.py` (38/38 tests passing).
- **License**: Created `LICENSE` (MIT License).
- **Clean Checkout Build Verification**: Verified clean checkout tarball creation and test execution (`git archive`).
