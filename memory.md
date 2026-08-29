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

Every command invocation pattern supported by CLI-KDG (v1.1, v1.2 & v1.3):

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
| `run_tests.py` | Automated test suite (35/35 tests passing: unit, AST audit, integration) | Updated (v1.3) |
| `fixtures/cli_target.py` | Mock CLI target v1 fixture for discovery & snapshot testing | Created (v1.2) |
| `fixtures/cli_target_v2.py` | Mock CLI target v2 fixture for replay regression testing | Created (v1.3) |
| `.github/workflows/ci.yml` | GitHub Actions CI matrix (Python 3.11, 3.12, 3.13) | Locked |
| `.github/workflows/release.yml` | GitHub Actions release packaging & checksum publisher | Locked |
| `README.md` | Complete system documentation (v1.1, v1.2 intact + v1.3 appended) | Updated (v1.3) |
| `memory.md` | Continuous memory tracking & architecture state log | Updated for v1.3 |

---

## Transition Log — Phase v1.3 Completion

- **v1.3 Objective Achieved**: Implemented historical test observation serialization (`snapshot`), versioned format validation (`version: 1`), stored test case re-execution (`replay`), and field-by-field behavioral regression analysis.
- **Zero Third-Party Dependency Invariant Enforced**: Built strictly with Python standard library modules (`json`, `sys`, `os`, `time`, `select`, `fcntl`, `ast`). AST import auditor verified zero `site-packages` imports.
- **Runtime Invariance Verified**: Duration (`runtime_ms`) is treated as metadata and never triggers behavioral regression diffs.
- **Controlled Error Handling**: Corrupt JSON, missing snapshot files, or unsupported format versions produce clean `CLKDGUserError` output without Python tracebacks.
- **Test Suite Expansion**: Total passing tests increased from 26 to **35 tests**.
- **Documentation Standards**: Preserved v1.1 and v1.2 documentation in `README.md` without modification; appended `## CLI-KDG v1.3` section.
- **Status**: Completed v1.3 implementation, verified locally, ready for version control branch commit and push.



