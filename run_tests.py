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


class TestDependencyPolicy(unittest.TestCase):
    """Audit tests enforcing strict zero third-party dependency policy."""

    def test_ast_import_audit(self):
        """Parse AST of all Python source files to verify only standard library modules are imported."""
        import ast
        import glob
        import importlib

        project_root = os.path.dirname(os.path.abspath(__file__))
        source_files = glob.glob(os.path.join(project_root, "cli_kdg", "*.py"))
        source_files.append(os.path.join(project_root, "cli_kdg.py"))
        source_files.append(os.path.join(project_root, "run_tests.py"))

        internal_modules = {"cli_kdg"}

        for filepath in source_files:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=filepath)

            for node in ast.walk(tree):
                imported_mods = []
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_mods.append(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.level == 0:
                        imported_mods.append(node.module.split(".")[0])

                for mod_name in imported_mods:
                    if mod_name in internal_modules:
                        continue
                    try:
                        mod = importlib.import_module(mod_name)
                        mod_file = getattr(mod, "__file__", "") or ""
                        self.assertNotIn(
                            "site-packages",
                            mod_file,
                            f"Forbidden third-party site-packages import '{mod_name}' detected in {filepath}"
                        )
                        self.assertNotIn(
                            "dist-packages",
                            mod_file,
                            f"Forbidden third-party dist-packages import '{mod_name}' detected in {filepath}"
                        )
                    except ImportError:
                        self.fail(f"Could not import module '{mod_name}' referenced in {filepath}")


    def test_no_external_manifests(self):
        """Verify absence of third-party package installation manifests."""
        project_root = os.path.dirname(os.path.abspath(__file__))
        forbidden_files = ["requirements.txt", "Pipfile", "Pipfile.lock", "poetry.lock"]
        for fname in forbidden_files:
            fpath = os.path.join(project_root, fname)
            self.assertFalse(
                os.path.exists(fpath),
                f"Forbidden dependency manifest file found: {fname}"
            )


class TestCLIIntegration(unittest.TestCase):
    """End-to-end integration execution tests for CLI-KDG entry points."""

    def test_cli_executable_direct(self):
        """Verify direct execution via python3 cli_kdg.py run <target>."""
        script_path = os.path.join(os.path.dirname(__file__), "cli_kdg.py")
        fixture = os.path.join(FIXTURES_DIR, "success.py")
        res = execute_target(PYTHON_BIN, [script_path, "run", PYTHON_BIN, fixture])
        self.assertTrue(res.is_success())
        self.assertIn("CLI-KDG v1.1", res.stdout)
        self.assertIn("STATUS: SUCCESS", res.stdout)

    def test_cli_module_invocation(self):
        """Verify python module invocation via python3 -m cli_kdg run <target>."""
        fixture = os.path.join(FIXTURES_DIR, "success.py")
        res = execute_target(PYTHON_BIN, ["-m", "cli_kdg", "run", PYTHON_BIN, fixture])
        self.assertTrue(res.is_success())
        self.assertIn("STATUS: SUCCESS", res.stdout)

    def test_cli_short_timeout_flag(self):
        """Verify short timeout flag '-t' on slow process execution."""
        fixture = os.path.join(FIXTURES_DIR, "slow.py")
        res = execute_target(PYTHON_BIN, ["-m", "cli_kdg", "run", "-t", "0.5", PYTHON_BIN, fixture])
        self.assertFalse(res.is_success())
        self.assertIn("STATUS: TIMEOUT", res.stdout)

    def test_cli_option_separator(self):
        """Verify option separator '--' behavior."""
        fixture = os.path.join(FIXTURES_DIR, "success.py")
        res = execute_target(PYTHON_BIN, ["-m", "cli_kdg", "run", "--timeout", "5", "--", PYTHON_BIN, fixture])
        self.assertTrue(res.is_success())
        self.assertIn("STATUS: SUCCESS", res.stdout)

    def test_cli_controlled_error_handling(self):
        """Verify missing argument error yields clean output without Python traceback."""
        res = execute_target(PYTHON_BIN, ["-m", "cli_kdg", "run"])
        self.assertEqual(res.exit_code, 2)
        self.assertIn("CLI-KDG error:", res.stderr)
        self.assertNotIn("Traceback (most recent call last)", res.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

