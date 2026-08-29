"""
CLI-KDG: CLI Known Deterministic Generator & Observation Engine (v1.1)

A zero-dependency process execution and observation system built strictly using
Python standard library primitives and low-level POSIX process mechanisms.

Key Features:
- POSIX low-level process lifecycle: fork(), dup2(), execvp(), waitpid(), kill()
- Non-blocking I/O multiplexing for isolated STDOUT and STDERR collection
- Monotonic deadline handling and deterministic child process reaping
- Zero external package dependencies (no pip required)
"""

__version__ = "1.1.0"
__author__ = "CLI-KDG Development Team"
