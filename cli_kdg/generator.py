"""
cli_kdg.generator — Deterministic Test Case Generator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Transforms a CLIModel into a bounded (max 15) list of classified TestCase objects.
"""

from typing import List
from cli_kdg.models import CLIModel, TestCase

MAX_TEST_CASES = 15


def generate_test_cases(model: CLIModel) -> List[TestCase]:
    """Generates a bounded, deterministic list of classified test cases from a CLIModel."""
    cases = [
        TestCase(["--help"], "HELP", "Verify standard help flag execution"),
        TestCase(["--unknown-flag-xyz-kdg"], "UNKNOWN_OPTION", "Verify unknown option handling and error reporting")
    ]

    def add_case(args: List[str], cat: str, reason: str) -> bool:
        if len(cases) < MAX_TEST_CASES:
            cases.append(TestCase(args, cat, reason))
            return True
        return False

    for opt in model.options:
        opt_name = opt.long_name or opt.short_name
        if not opt_name or len(cases) >= MAX_TEST_CASES:
            break

        if not opt.requires_value:
            add_case([opt_name], "FLAG_VALID", f"Verify boolean flag '{opt_name}' activation")
            add_case([opt_name, "extra_arg"], "FLAG_UNEXPECTED_ARG", f"Verify flag '{opt_name}' unexpected argument behavior")
        else:
            add_case([opt_name], "OPTION_MISSING_VAL", f"Verify error handling when option '{opt_name}' value is omitted")
            is_num = any(k in (opt.value_hint or "").upper() for k in ["INT", "INTEGER", "NUM", "COUNT"])
            if is_num:
                add_case([opt_name, "0"], "OPTION_VALID_VAL", f"Verify numeric option '{opt_name}' zero value")
                add_case([opt_name, "-1"], "OPTION_INVALID_VAL", f"Verify numeric option '{opt_name}' negative value")
                add_case([opt_name, "abc"], "OPTION_INVALID_VAL", f"Verify numeric option '{opt_name}' non-numeric value")
            else:
                add_case([opt_name, "test_val"], "OPTION_VALID_VAL", f"Verify option '{opt_name}' standard string value")

    return cases[:MAX_TEST_CASES]
