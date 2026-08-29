#!/usr/bin/env python3
"""
CLI-KDG Zero-Dependency Test Suite (v1.1 & v1.2)
=================================================

Automated tests for CLI-KDG using standard library unittest framework.
Validates:
- Manual CLI argument parsing (run and discover)
- POSIX process lifecycle execution (fork, execvp, waitpid)
- Isolated STDOUT & STDERR pipe capture
- Pipe buffer deadlock protection on large output
- Monotonic timeout deadline execution & child process reaping
- Controlled error formatting without uncaught tracebacks
- Zero third-party dependency policy AST audit
- Automated CLI --help interrogation & option parsing (v1.2)
- Deterministic test case generation & execution (v1.2)
"""

import sys
import os
import unittest

from cli_kdg.parser import parse_args
from cli_kdg.process import execute_target
from cli_kdg.reporter import format_report, format_discovery_report
from cli_kdg.models import TerminationType
from cli_kdg.errors import CLKDGUserError, CLKDGExecutionError
from cli_kdg.help_parser import parse_help_text
from cli_kdg.generator import generate_test_cases
from cli_kdg.discover import discover_target


PYTHON_BIN = sys.executable
FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


class TestParser(unittest.TestCase):
    """Unit tests for manual CLI argument parsing."""

    def test_valid_parse(self):
        sub, target, target_args, timeout = parse_args(["run", "python3", "app.py", "--arg1"])
        self.assertEqual(sub, "run")
        self.assertEqual(target, "python3")
        self.assertEqual(target_args, ["app.py", "--arg1"])
        self.assertIsNone(timeout)

    def test_discover_parse(self):
        sub, target, target_args, timeout = parse_args(["discover", "python3", "app.py"])
        self.assertEqual(sub, "discover")
        self.assertEqual(target, "python3")
        self.assertEqual(target_args, ["app.py"])
        self.assertIsNone(timeout)

    def test_timeout_flag_parsing(self):
        sub, target, target_args, timeout = parse_args(["run", "--timeout", "2.5", "python3", "app.py"])
        self.assertEqual(sub, "run")
        self.assertEqual(target, "python3")
        self.assertEqual(target_args, ["app.py"])
        self.assertEqual(timeout, 2.5)

    def test_timeout_equals_syntax(self):
        sub, target, target_args, timeout = parse_args(["run", "--timeout=10", "ls", "-la"])
        self.assertEqual(sub, "run")
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


class TestHelpParser(unittest.TestCase):
    """Unit tests for v1.2 CLI help text parser."""

    def test_parse_help_text(self):
        sample_help = """
        Usage: app [OPTIONS]
        Options:
          -v, --verbose        Enable verbose output
          -o, --output FILE    Write output to specified file
          --count INTEGER      Specify loop iteration count
        """
        model = parse_help_text(sample_help)
        self.assertEqual(len(model.options), 3)

        verbose_opt = next((o for o in model.options if o.long_name == "--verbose"), None)
        self.assertIsNotNone(verbose_opt)
        self.assertEqual(verbose_opt.short_name, "-v")
        self.assertFalse(verbose_opt.requires_value)

        output_opt = next((o for o in model.options if o.long_name == "--output"), None)
        self.assertIsNotNone(output_opt)
        self.assertTrue(output_opt.requires_value)
        self.assertEqual(output_opt.value_hint, "FILE")

        count_opt = next((o for o in model.options if o.long_name == "--count"), None)
        self.assertIsNotNone(count_opt)
        self.assertTrue(count_opt.requires_value)
        self.assertEqual(count_opt.value_hint, "INTEGER")


class TestGenerator(unittest.TestCase):
    """Unit tests for v1.2 deterministic test case generator."""

    def test_generate_test_cases(self):
        sample_help = """
        Options:
          -v, --verbose        Enable verbose output
          --count INTEGER      Specify loop iteration count
        """
        model = parse_help_text(sample_help)
        cases = generate_test_cases(model)

        self.assertGreaterEqual(len(cases), 4)

        help_case = next((c for c in cases if c.category == "HELP"), None)
        self.assertIsNotNone(help_case)
        self.assertEqual(help_case.arguments, ["--help"])

        unknown_case = next((c for c in cases if c.category == "UNKNOWN_OPTION"), None)
        self.assertIsNotNone(unknown_case)

        flag_case = next((c for c in cases if c.category == "FLAG_VALID"), None)
        self.assertIsNotNone(flag_case)
        self.assertIn("--verbose", flag_case.arguments)

        numeric_missing = next((c for c in cases if c.category == "OPTION_MISSING_VAL"), None)
        self.assertIsNotNone(numeric_missing)
        self.assertIn("--count", numeric_missing.arguments)


class TestDiscoverIntegration(unittest.TestCase):
    """End-to-end integration tests for v1.2 discover subcommand."""

    def test_discover_target_execution(self):
        fixture = os.path.join(FIXTURES_DIR, "cli_target.py")
        res = discover_target(PYTHON_BIN, [fixture])

        self.assertTrue(res.is_success())
        self.assertGreaterEqual(len(res.model.options), 3)
        self.assertGreaterEqual(len(res.test_cases), 4)
        self.assertEqual(len(res.test_cases), len(res.case_results))

    def test_discover_cli_script_entrypoint(self):
        script_path = os.path.join(os.path.dirname(__file__), "cli_kdg.py")
        fixture = os.path.join(FIXTURES_DIR, "cli_target.py")
        res = execute_target(PYTHON_BIN, [script_path, "discover", PYTHON_BIN, fixture])

        self.assertTrue(res.is_success())
        self.assertIn("CLI-KDG Discovery & Test Execution Report (v1.2)", res.stdout)
        self.assertIn("Discovered Option Specifications:", res.stdout)
        self.assertIn("DISCOVERY STATUS: SUCCESS", res.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
