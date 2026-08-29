# STDLIB Manifest & Value Proposition: CLI-KDG Compliance Log

## 1. Core Paradigm: Zero-Third-Party Runtime Dependency

The fundamental directive of **CLI-KDG** is to avoid third-party Python runtime packages and implement the required functionality using the Python standard library and POSIX system primitives.

The application is designed to run on a Python 3.11+ POSIX environment without installing third-party Python packages.

Example:

```bash
python3 cli_kdg.py discover python3 fixtures/cli_target.py
```

The precise claim is:

> **CLI-KDG has no third-party Python runtime dependencies.**

This does not claim that the repository, its development environment, or its CI infrastructure has no external dependencies. CI/CD may use external GitHub Actions, while the CLI-KDG runtime itself remains third-party-package-free.

---

## 2. Standard-Library & POSIX Alternatives

The following matrix describes functionality that can commonly be provided by higher-level libraries or frameworks and the lower-level mechanisms deliberately used by CLI-KDG.

These are **avoided dependency categories**, not claims that each named package was previously installed in this repository and subsequently removed.

| Capability | Higher-Level Alternative | CLI-KDG Implementation | Why |
| :--- | :--- | :--- | :--- |
| **Process Control** | High-level process wrappers such as `subprocess` | `os.fork()` + `os.execvp()` | Provides direct control over process creation, descriptor inheritance, and target execution without `subprocess`. |
| **I/O Multiplexing** | Higher-level asynchronous/event frameworks | `select.select()` + non-blocking descriptors | Provides the multiplexing required by the execution engine without introducing an asynchronous framework. |
| **CLI Parsing** | `argparse` and similar CLI frameworks | Manual `sys.argv` parsing | Keeps command parsing explicit and dependency-free. |
| **Behavior Comparison** | Generic comparison/deep-comparison libraries | Explicit field-by-field comparisons | v1.3 has a small, defined observation schema, so generic comparison machinery is unnecessary. |
| **Help Parsing** | General-purpose parser/regex abstractions | Primitive string operations and bounded parsing rules | Keeps parsing intentionally narrow and auditable for the supported CLI-help format. |
| **Persistence** | YAML/object-serialization frameworks | Standard-library `json` | Provides human-readable, data-only snapshots without an additional package. |
| **Testing** | Third-party test runners/frameworks | Python standard-library `unittest` | Keeps the repository test suite within the standard library. |
| **Test Generation** | General-purpose fuzzing frameworks | Bounded deterministic edge-case generation | Produces reproducible CLI boundary cases rather than uncontrolled random fuzzing. |

### Important distinction

The matrix means:

```text
required capability
        ↓
higher-level dependency is unnecessary
        ↓
standard-library/POSIX implementation
```

It does **not** mean:

```text
package X was installed
        ↓
package X was removed
        ↓
CLI-KDG recreated package X
```

This distinction keeps the dependency claim technically accurate.

---

## 3. Dependency Verification

CLI-KDG includes an explicit dependency-policy test.

The repository's test harness uses Python's AST facilities to inspect imports and checks imported modules against third-party package locations such as `site-packages` and `dist-packages`.

The intended runtime boundary is:

```text
Python 3.11+
      +
Python standard library
      +
POSIX operating-system primitives
      ↓
CLI-KDG
```

The CLI-KDG runtime does not require a `pip install` step for third-party Python packages.

This is a **runtime dependency claim**, not a claim that CI/CD or development tooling has no external dependencies.

---

## 4. Deep-Dive Case Study: Pipe Deadlock Mitigation

### The Problem

A parent process that waits on one output stream while the child fills another pipe can deadlock when a pipe buffer becomes full.

A simplified failure pattern is:

```text
child writes stderr
       ↓
stderr pipe becomes full
       ↓
child blocks
       ↓
parent is waiting for another event
       ↓
execution can deadlock
```

This matters when a CLI produces substantial stdout and stderr concurrently.

### CLI-KDG's Implementation

The execution engine manages the communication channels directly at the file-descriptor level.

#### 1. Non-blocking descriptors

It configures descriptors using `fcntl` and `O_NONBLOCK`.

Conceptually:

```python
flags = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
```

#### 2. Kernel-level I/O multiplexing

The engine uses:

```python
select.select()
```

to wait for readable stdout/stderr descriptors.

#### 3. Incremental reads

Available data is consumed in bounded chunks:

```python
os.read(fd, 4096)
```

stdout and stderr are accumulated independently.

Conceptually:

```text
              child
             /              stdout    stderr
            │        │
          pipe      pipe
            │        │
            └──┬─────┘
               │
          select.select()
               │
        non-blocking read
               │
       separate buffers
               │
       ExecutionResult
```

This is a concrete example of replacing a high-level process/I/O abstraction with directly controlled Python standard-library and POSIX primitives.

The precise claim is **deadlock mitigation through concurrent non-blocking stream servicing**, rather than an absolute guarantee that every possible process interaction can never deadlock.

---

## 5. Deterministic Test Generation

CLI-KDG v1.2 does not attempt to be a general-purpose random fuzzing framework.

Its generator creates a bounded, deterministic set of CLI cases from the discovered interface.

The generator has an explicit maximum test-case bound and uses deterministic edge values such as:

```text
--help
unknown option
0
-1
abc
```

where applicable to the discovered option.

This provides reproducible CLI boundary testing.

The accurate claim is:

> **CLI-KDG performs bounded deterministic edge-case generation; it does not provide general-purpose random fuzzing.**

---

## 6. Historical Behavioral Replay

CLI-KDG v1.3 introduces historical behavioral baselines.

The workflow is:

```text
Version A
    ↓
v1.2 generated cases
    ↓
execute
    ↓
snapshot
    ↓
Version B
    ↓
replay historical cases
    ↓
compare behavior
```

The key property is:

> **The historical test inputs remain fixed while the target implementation changes.**

Replay reconstructs the historical `TestCase` objects from the stored observations. It does not regenerate tests from the current target's `--help` output.

This makes the comparison about observable target behavior rather than about a newly generated test set.

---

## 7. Behavioral Comparison

v1.3 compares these observable fields:

```text
exit_code
status
stdout
stderr
termination_type
```

The snapshot also records:

```text
runtime_ms
```

but runtime is not used as a behavioral equality field.

Therefore:

```text
baseline runtime = 15 ms
current runtime  = 31 ms
```

does not automatically produce a behavioral regression when the compared observable fields remain equal.

This avoids treating ordinary scheduler or machine-load variation as a functional CLI regression.

---

## 8. Snapshot Persistence

v1.3 uses Python's standard-library `json` module for snapshots.

The implemented snapshot structure contains:

```text
version
cli_kdg_version
created_at
target
target_args
observations[]
```

The format is explicitly versioned so that unsupported snapshot versions can be rejected rather than silently interpreted.

JSON keeps the artifact:
- human-readable
- inspectable
- data-oriented
- supported by the Python standard library

---

## 9. Shell-Free Target Execution

CLI-KDG passes the target and its arguments directly to `os.execvp()`.

Conceptually:

```text
user arguments
      ↓
argument vector
      ↓
os.execvp()
      ↓
target process
```

It does not construct a shell command for target execution.

Therefore shell metacharacters such as:

```text
&&
;
|
```

are not interpreted as shell syntax merely because they occur inside an argument.

The accurate security claim is:

> **Direct `execvp()` execution avoids shell interpretation of target arguments and reduces the shell-injection surface.**

This is not a claim that the entire application is immune to every possible security vulnerability.

---

## 10. Maintainability and Auditability

The critical execution and regression path is directly inspectable:

```text
CLI parsing
    ↓
POSIX process creation
    ↓
file-descriptor management
    ↓
non-blocking I/O
    ↓
timeout handling
    ↓
observation
    ↓
JSON persistence
    ↓
historical replay
    ↓
field-level comparison
```

The core runtime does not depend on an external package to provide these mechanisms.

A reviewer can trace:
- where the child process is created
- where arguments are passed
- where descriptors are configured
- where stdout/stderr are collected
- where timeout handling occurs
- where observations are persisted
- where historical behavior is compared

The value is therefore **inspectability and control**, not simply a low package count.

---

## 11. CI/CD Dependency Boundary

The application runtime and CI/CD environment should be distinguished.

CLI-KDG itself has no third-party Python runtime packages.

The repository's GitHub Actions workflow can use external actions such as:

```text
actions/checkout
actions/setup-python
softprops/action-gh-release
```

These are CI/CD dependencies, not Python packages required by the CLI-KDG runtime.

Therefore the accurate statement is:

> **CLI-KDG has no third-party Python runtime dependencies; its CI/CD workflow may use external GitHub Actions.**

---

## 12. What CLI-KDG Can Truthfully Claim

CLI-KDG can truthfully claim that it:

- has no third-party Python runtime dependencies
- avoids `subprocess` for target process execution
- uses `os.fork()` and `os.execvp()` for process creation/execution
- uses non-blocking descriptors and `select.select()` for concurrent stdout/stderr collection
- manually parses CLI arguments
- parses its supported help grammar using standard string operations and bounded rules
- uses standard-library JSON for snapshots
- uses Python's standard-library `unittest` test framework
- performs bounded deterministic CLI edge-case generation
- does not implement general-purpose random fuzzing
- freezes historical test inputs for v1.3 replay
- does not regenerate replay cases from current `--help`
- compares explicit observable behavioral fields
- excludes runtime from default behavioral regression classification
- records process `termination_type`
- avoids shell interpretation during direct target execution
- includes an AST-based dependency-policy test

---

## 13. Claims CLI-KDG Should Not Make

The project should **not** claim that it:

- removed ten third-party packages that were previously project dependencies
- recreated or replaced specific third-party packages unless that package was actually a project dependency
- uses `select()` as a functional replacement for unrelated tools such as process-tree inspection
- provides general-purpose fuzzing equivalent to a dedicated fuzzing framework
- is immune to all injection or security vulnerabilities
- guarantees that every possible process interaction can never deadlock
- has zero external dependencies anywhere in its development/CI ecosystem
- has been independently validated on every Python 3 version and every POSIX platform

---

## 14. Final Value Proposition

The technically defensible value proposition is:

```text
No third-party Python runtime packages
              +
Direct POSIX process control
              +
Non-blocking stdout/stderr collection
              +
Deterministic bounded CLI testing
              +
Versioned behavioral snapshots
              +
Exact historical replay
              +
Field-level regression comparison
              =
Small, inspectable CLI behavioral regression engine
```

The differentiator is therefore not:

> “We did not use libraries.”

It is:

> **CLI-KDG deliberately uses a small, inspectable execution stack built from Python's standard library and POSIX primitives, then builds deterministic historical replay on top of that foundation to make CLI behavioral regression reproducible.**
