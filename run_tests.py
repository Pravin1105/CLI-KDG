#!/usr/bin/env python3
"""
CLI-KDG Zero-Dependency Test Suite
==================================

Automated tests for CLI-KDG using standard library unittest framework.
Validates:
- Manual CLI argument parsing
- POSIX process lifecycle execution (fork, execvp, waitpid)
- Isolated STDOUT & STDERR pipe capture
- Pipe buffer deadlock protection on large output
- Monotonic timeout deadline execution & child process reaping
- Controlled error formatting without uncaught tracebacks
"""

import sys
import os
import unittest

from cli_kdg.parser import parse_args
from cli_kdg.process import execute_target
from cli_kdg.reporter import format_report
from cli_kdg.models import TerminationType
from cli_kdg.errors import CLKDGUserError, CLKDGExecutionError


PYTHON_BIN = sys.executable
FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


class TestParser(unittest.TestCase):
    """Unit tests for manual CLI argument parsing."""

    def test_valid_parse(self):
        target, target_args, timeout = parse_args(["run", "python3", "app.py", "--arg1"])
        self.assertEqual(target, "python3")
        self.assertEqual(target_args, ["app.py", "--arg1"])
        self.assertIsNone(timeout)

    def test_timeout_flag_parsing(self):
        target, target_args, timeout = parse_args(["run", "--timeout", "2.5", "python3", "app.py"])
        self.assertEqual(target, "python3")
        self.assertEqual(target_args, ["app.py"])
        self.assertEqual(timeout, 2.5)

    def test_timeout_equals_syntax(self):
        target, target_args, timeout = parse_args(["run", "--timeout=10", "ls", "-la"])
        self.assertEqual(target, "ls")
        self.assertEqual(target_args, ["-la"])
        self.assertEqual(timeout, 10.0)

    def test_missing_subcommand(self):
        with self.assertRaises(CLKDGUserError):
            parse_args([])

    def test_invalid_subcommand(self):
        with self.assertRaises(CLKDGUserError):
            parse_args(["execute", "target"])

    def test_missing_target(self):
        with self.assertRaises(CLKDGUserError):
            parse_args(["run", "--timeout", "5"])

    def test_invalid_timeout_value(self):
        with self.assertRaises(CLKDGUserError):
            parse_args(["run", "--timeout", "invalid", "python3"])


class TestProcessExecution(unittest.TestCase):
    """Integration tests for POSIX process execution engine."""

    def test_success_fixture(self):
        fixture = os.path.join(FIXTURES_DIR, "success.py")
        res = execute_target(PYTHON_BIN, [fixture])
        self.assertEqual(res.termination_type, TerminationType.EXITED)
        self.assertEqual(res.exit_code, 0)
        self.assertIn("Execution successful!", res.stdout)
        self.assertEqual(res.stderr.strip(), "")
        self.assertGreater(res.runtime_ms, 0)
        self.assertTrue(res.is_success())

    def test_failure_fixture(self):
        fixture = os.path.join(FIXTURES_DIR, "failure.py")
        res = execute_target(PYTHON_BIN, [fixture])
        self.assertEqual(res.termination_type, TerminationType.EXITED)
        self.assertEqual(res.exit_code, 3)
        self.assertIn("Fatal execution error occurred!", res.stderr)
        self.assertFalse(res.is_success())

    def test_mixed_output_fixture(self):
        fixture = os.path.join(FIXTURES_DIR, "mixed_output.py")
        res = execute_target(PYTHON_BIN, [fixture])
        self.assertEqual(res.exit_code, 0)
        self.assertIn("STDOUT message line 1", res.stdout)
        self.assertIn("STDERR error line 1", res.stderr)

    def test_large_output_fixture(self):
        fixture = os.path.join(FIXTURES_DIR, "large_output.py")
        res = execute_target(PYTHON_BIN, [fixture])
        self.assertEqual(res.exit_code, 0)
        self.assertGreaterEqual(len(res.stdout), 500000)
        self.assertGreaterEqual(len(res.stderr), 500000)

    def test_timeout_execution(self):
        fixture = os.path.join(FIXTURES_DIR, "slow.py")
        res = execute_target(PYTHON_BIN, [fixture], timeout=0.5)
        self.assertEqual(res.termination_type, TerminationType.TIMED_OUT)
        self.assertIsNotNone(res.error)
        self.assertIn("exceeded timeout limit", res.error)
        self.assertFalse(res.is_success())

    def test_nonexistent_binary(self):
        res = execute_target("./nonexistent_binary_xyz_123", [])
        self.assertIn(res.termination_type, [TerminationType.START_FAILED, TerminationType.EXITED])
        self.assertFalse(res.is_success())


class TestReporter(unittest.TestCase):
    """Unit tests for report formatting engine."""

    def test_reporter_formatting(self):
        fixture = os.path.join(FIXTURES_DIR, "success.py")
        res = execute_target(PYTHON_BIN, [fixture])
        report = format_report(res)

        self.assertIn("CLI-KDG v1.1", report)
        self.assertIn("Command: ", report)
        self.assertIn("Exit:    0", report)
        self.assertIn("STDOUT", report)
        self.assertIn("STDERR", report)
        self.assertIn("STATUS: SUCCESS", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
