#!/usr/bin/env python3
"""
CLI-KDG Zero-Dependency Test Suite (v1.1, v1.2 & v1.3)
======================================================
Automated test suite validating argument parsing, POSIX execution engine,
AST dependency policy audit, help parser, test generator, snapshot manager, and replay comparator.
"""

import sys
import os
import tempfile
import unittest

from cli_kdg.parser import parse_args
from cli_kdg.process import execute_target
from cli_kdg.reporter import format_report
from cli_kdg.models import TerminationType, TestObservation
from cli_kdg.errors import CLKDGUserError
from cli_kdg.help_parser import parse_help_text
from cli_kdg.generator import generate_test_cases
from cli_kdg.discover import discover_target
from cli_kdg.snapshot import create_snapshot, save_snapshot, load_snapshot
from cli_kdg.replay import replay_snapshot, compare_observations

PYTHON_BIN = sys.executable
FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


class TestParser(unittest.TestCase):
    """Unit tests for manual CLI argument parsing."""
    def test_valid_parse(self):
        sub, target, args, timeout, out_file = parse_args(["run", "python3", "app.py", "--arg1"])
        self.assertEqual((sub, target, args, timeout, out_file), ("run", "python3", ["app.py", "--arg1"], None, None))

    def test_discover_parse(self):
        sub, target, args, timeout, out_file = parse_args(["discover", "python3", "app.py"])
        self.assertEqual((sub, target, args, timeout, out_file), ("discover", "python3", ["app.py"], None, None))

    def test_snapshot_parse(self):
        sub, target, args, timeout, out_file = parse_args(["snapshot", "--output", "snap.json", "python3", "app.py"])
        self.assertEqual((sub, target, args, timeout, out_file), ("snapshot", "python3", ["app.py"], None, "snap.json"))

    def test_replay_parse(self):
        sub, target, args, timeout, out_file = parse_args(["replay", "snap.json", "python3", "app.py"])
        self.assertEqual((sub, target, args, timeout, out_file), ("replay", "snap.json", ["python3", "app.py"], None, None))

    def test_timeout_flag_parsing(self):
        sub, target, args, timeout, out_file = parse_args(["run", "--timeout", "2.5", "python3", "app.py"])
        self.assertEqual((sub, target, args, timeout), ("run", "python3", ["app.py"], 2.5))

    def test_timeout_equals_syntax(self):
        sub, target, args, timeout, out_file = parse_args(["run", "--timeout=10", "ls", "-la"])
        self.assertEqual((sub, target, args, timeout), ("run", "ls", ["-la"], 10.0))

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
        res = execute_target(PYTHON_BIN, [os.path.join(FIXTURES_DIR, "success.py")])
        self.assertTrue(res.is_success())
        self.assertIn("Execution successful!", res.stdout)

    def test_failure_fixture(self):
        res = execute_target(PYTHON_BIN, [os.path.join(FIXTURES_DIR, "failure.py")])
        self.assertEqual(res.exit_code, 3)
        self.assertFalse(res.is_success())

    def test_mixed_output_fixture(self):
        res = execute_target(PYTHON_BIN, [os.path.join(FIXTURES_DIR, "mixed_output.py")])
        self.assertEqual(res.exit_code, 0)
        self.assertIn("STDOUT message line 1", res.stdout)
        self.assertIn("STDERR error line 1", res.stderr)

    def test_large_output_fixture(self):
        res = execute_target(PYTHON_BIN, [os.path.join(FIXTURES_DIR, "large_output.py")])
        self.assertEqual(res.exit_code, 0)
        self.assertGreaterEqual(len(res.stdout), 500000)

    def test_timeout_execution(self):
        res = execute_target(PYTHON_BIN, [os.path.join(FIXTURES_DIR, "slow.py")], timeout=0.5)
        self.assertEqual(res.termination_type, TerminationType.TIMED_OUT)
        self.assertFalse(res.is_success())

    def test_nonexistent_binary(self):
        res = execute_target("./nonexistent_binary_xyz_123", [])
        self.assertFalse(res.is_success())


class TestReporter(unittest.TestCase):
    """Unit tests for report formatting engine."""
    def test_reporter_formatting(self):
        res = execute_target(PYTHON_BIN, [os.path.join(FIXTURES_DIR, "success.py")])
        report = format_report(res)
        self.assertIn("CLI-KDG v1.1", report)
        self.assertIn("STATUS: SUCCESS", report)


class TestDependencyPolicy(unittest.TestCase):
    """Audit tests enforcing strict zero third-party dependency policy."""
    def test_ast_import_audit(self):
        import ast, glob, importlib
        root = os.path.dirname(os.path.abspath(__file__))
        files = glob.glob(os.path.join(root, "cli_kdg", "*.py")) + [os.path.join(root, "cli_kdg.py"), os.path.join(root, "run_tests.py")]

        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=filepath)
            for node in ast.walk(tree):
                mods = []
                if isinstance(node, ast.Import):
                    mods.extend(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    mods.append(node.module.split(".")[0])
                for m in mods:
                    if m != "cli_kdg":
                        mod = importlib.import_module(m)
                        mod_file = getattr(mod, "__file__", "") or ""
                        self.assertNotIn("site-packages", mod_file, f"Third-party import '{m}' in {filepath}")
                        self.assertNotIn("dist-packages", mod_file, f"Third-party import '{m}' in {filepath}")

    def test_no_external_manifests(self):
        root = os.path.dirname(os.path.abspath(__file__))
        for fname in ["requirements.txt", "Pipfile", "Pipfile.lock", "poetry.lock"]:
            self.assertFalse(os.path.exists(os.path.join(root, fname)), f"Forbidden manifest found: {fname}")


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI-KDG entry points."""
    def test_cli_executable_direct(self):
        script = os.path.join(os.path.dirname(__file__), "cli_kdg.py")
        res = execute_target(PYTHON_BIN, [script, "run", PYTHON_BIN, os.path.join(FIXTURES_DIR, "success.py")])
        self.assertTrue(res.is_success())
        self.assertIn("STATUS: SUCCESS", res.stdout)

    def test_cli_module_invocation(self):
        res = execute_target(PYTHON_BIN, ["-m", "cli_kdg", "run", PYTHON_BIN, os.path.join(FIXTURES_DIR, "success.py")])
        self.assertTrue(res.is_success())

    def test_cli_short_timeout_flag(self):
        res = execute_target(PYTHON_BIN, ["-m", "cli_kdg", "run", "-t", "0.5", PYTHON_BIN, os.path.join(FIXTURES_DIR, "slow.py")])
        self.assertIn("STATUS: TIMEOUT", res.stdout)

    def test_cli_option_separator(self):
        res = execute_target(PYTHON_BIN, ["-m", "cli_kdg", "run", "--timeout", "5", "--", PYTHON_BIN, os.path.join(FIXTURES_DIR, "success.py")])
        self.assertTrue(res.is_success())

    def test_cli_controlled_error_handling(self):
        res = execute_target(PYTHON_BIN, ["-m", "cli_kdg", "run"])
        self.assertEqual(res.exit_code, 2)
        self.assertIn("CLI-KDG error:", res.stderr)
        self.assertNotIn("Traceback", res.stderr)


class TestHelpParser(unittest.TestCase):
    """Unit tests for v1.2 CLI help text parser."""
    def test_parse_help_text(self):
        sample = "Options:\n  -v, --verbose Enable verbose output\n  -o, --output FILE Output file\n  --count INTEGER Count"
        model = parse_help_text(sample)
        self.assertEqual(len(model.options), 3)
        self.assertEqual(next(o for o in model.options if o.long_name == "--output").value_hint, "FILE")


class TestGenerator(unittest.TestCase):
    """Unit tests for v1.2 deterministic test case generator."""
    def test_generate_test_cases(self):
        sample = "Options:\n  -v, --verbose Enable verbose output\n  --count INTEGER Count"
        cases = generate_test_cases(parse_help_text(sample))
        self.assertGreaterEqual(len(cases), 4)
        self.assertIsNotNone(next(c for c in cases if c.category == "HELP"))
        self.assertIsNotNone(next(c for c in cases if c.category == "UNKNOWN_OPTION"))


class TestDiscoverIntegration(unittest.TestCase):
    """Integration tests for v1.2 discover subcommand."""
    def test_discover_target_execution(self):
        res = discover_target(PYTHON_BIN, [os.path.join(FIXTURES_DIR, "cli_target.py")])
        self.assertTrue(res.is_success())
        self.assertGreaterEqual(len(res.test_cases), 4)

    def test_discover_cli_script_entrypoint(self):
        script = os.path.join(os.path.dirname(__file__), "cli_kdg.py")
        res = execute_target(PYTHON_BIN, [script, "discover", PYTHON_BIN, os.path.join(FIXTURES_DIR, "cli_target.py")])
        self.assertTrue(res.is_success())
        self.assertIn("DISCOVERY STATUS: SUCCESS", res.stdout)


class TestSnapshotManager(unittest.TestCase):
    """Unit tests for v1.3 Snapshot persistence manager."""
    def test_snapshot_create_save_load(self):
        snap = create_snapshot(PYTHON_BIN, [os.path.join(FIXTURES_DIR, "cli_target.py")])
        self.assertEqual(snap.version, 1)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            save_snapshot(snap, tmp_path)
            loaded = load_snapshot(tmp_path)
            self.assertEqual(loaded.version, 1)
            self.assertEqual(len(loaded.observations), len(snap.observations))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_unsupported_snapshot_version(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as tmp:
            tmp.write('{"version": 99, "target": "test", "observations": []}')
            tmp_path = tmp.name
        try:
            with self.assertRaises(CLKDGUserError) as ctx:
                load_snapshot(tmp_path)
            self.assertIn("Unsupported snapshot format version '99'", str(ctx.exception))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_missing_snapshot_file(self):
        with self.assertRaises(CLKDGUserError):
            load_snapshot("/nonexistent_path_xyz_123.json")


class TestReplayComparator(unittest.TestCase):
    """Unit tests for v1.3 replay comparator and runtime invariance."""
    def test_runtime_invariance_comparison(self):
        obs = TestObservation(["--help"], "HELP", "Reason", 0, "Out", "", 10.0, "EXITED")
        res = execute_target(PYTHON_BIN, [os.path.join(FIXTURES_DIR, "success.py")])
        res.exit_code, res.stdout, res.stderr, res.termination_type, res.runtime_ms = 0, "Out", "", "EXITED", 9999.0
        cls_name, diffs = compare_observations(obs, res)
        self.assertEqual((cls_name, len(diffs)), ("UNCHANGED", 0))

    def test_exit_code_discrepancy(self):
        obs = TestObservation(["--count", "0"], "OPTION_VALID_VAL", "Reason", 0, "Out", "", 10.0, "EXITED")
        res = execute_target(PYTHON_BIN, [os.path.join(FIXTURES_DIR, "failure.py")])
        cls_name, diffs = compare_observations(obs, res)
        self.assertEqual(cls_name, "CHANGED")
        self.assertGreaterEqual(len(diffs), 1)


class TestReplayIntegration(unittest.TestCase):
    """End-to-end integration tests for v1.3 snapshot and replay."""
    def test_snapshot_and_replay_unchanged(self):
        script = os.path.join(os.path.dirname(__file__), "cli_kdg.py")
        fix_v1 = os.path.join(FIXTURES_DIR, "cli_target.py")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            snap_path = tmp.name

        try:
            execute_target(PYTHON_BIN, [script, "snapshot", "--output", snap_path, PYTHON_BIN, fix_v1])
            res_replay = execute_target(PYTHON_BIN, [script, "replay", snap_path, PYTHON_BIN, fix_v1])
            self.assertTrue(res_replay.is_success())
            self.assertIn("UNCHANGED (No Regressions Detected)", res_replay.stdout)
        finally:
            if os.path.exists(snap_path):
                os.remove(snap_path)

    def test_replay_regression_detection(self):
        script = os.path.join(os.path.dirname(__file__), "cli_kdg.py")
        fix_v1 = os.path.join(FIXTURES_DIR, "cli_target.py")
        fix_v2 = os.path.join(FIXTURES_DIR, "cli_target_v2.py")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            snap_path = tmp.name

        try:
            execute_target(PYTHON_BIN, [script, "snapshot", "--output", snap_path, PYTHON_BIN, fix_v1])
            res_replay = execute_target(PYTHON_BIN, [script, "replay", snap_path, PYTHON_BIN, fix_v2])
            self.assertFalse(res_replay.is_success())
            self.assertIn("BEHAVIORAL_REGRESSIONS_DETECTED", res_replay.stdout)
        finally:
            if os.path.exists(snap_path):
                os.remove(snap_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
