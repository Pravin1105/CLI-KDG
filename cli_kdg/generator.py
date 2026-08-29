"""
cli_kdg.generator
~~~~~~~~~~~~~~~~~

Deterministic test case generator for CLI-KDG v1.2.
Transforms a structured CLIModel into a bounded, deterministic list of TestCase instances.

Guarantees:
- Bounded execution (maximum 15 test cases).
- Universal help and unknown flag validation.
- Clear classification category and human-interpretable rationale for every test case.
- Zero external dependencies.
"""

from typing import List
from cli_kdg.models import CLIModel, TestCase

MAX_TEST_CASES = 15


def generate_test_cases(model: CLIModel) -> List[TestCase]:
    """
    Generates a deterministic list of test cases from a CLIModel.

    Args:
        model (CLIModel): Discovered CLI model.

    Returns:
        List[TestCase]: List of bounded, deterministic test cases.
    """
    cases: List[TestCase] = []

    # 1. Universal Base Test Cases
    cases.append(
        TestCase(
            arguments=["--help"],
            category="HELP",
            reason="Verify standard help flag execution"
        )
    )

    cases.append(
        TestCase(
            arguments=["--unknown-flag-xyz-kdg"],
            category="UNKNOWN_OPTION",
            reason="Verify unknown option handling and error reporting"
        )
    )

    # 2. Option-Specific Test Cases
    for opt in model.options:
        if len(cases) >= MAX_TEST_CASES:
            break

        opt_name = opt.long_name or opt.short_name
        if not opt_name:
            continue

        if not opt.requires_value:
            # Boolean Flag Test Cases
            cases.append(
                TestCase(
                    arguments=[opt_name],
                    category="FLAG_VALID",
                    reason=f"Verify boolean flag '{opt_name}' activation"
                )
            )

            if len(cases) < MAX_TEST_CASES:
                cases.append(
                    TestCase(
                        arguments=[opt_name, "extra_arg"],
                        category="FLAG_UNEXPECTED_ARG",
                        reason=f"Verify behavior when boolean flag '{opt_name}' receives an unexpected argument"
                    )
                )
        else:
            # Value-Requiring Option Test Cases
            cases.append(
                TestCase(
                    arguments=[opt_name],
                    category="OPTION_MISSING_VAL",
                    reason=f"Verify error handling when value for option '{opt_name}' is omitted"
                )
            )

            hint_upper = (opt.value_hint or "").upper()
            is_numeric = any(k in hint_upper for k in ["INT", "INTEGER", "NUM", "COUNT"])

            if is_numeric:
                if len(cases) < MAX_TEST_CASES:
                    cases.append(
                        TestCase(
                            arguments=[opt_name, "0"],
                            category="OPTION_VALID_VAL",
                            reason=f"Verify numeric option '{opt_name}' with zero boundary value"
                        )
                    )
                if len(cases) < MAX_TEST_CASES:
                    cases.append(
                        TestCase(
                            arguments=[opt_name, "-1"],
                            category="OPTION_INVALID_VAL",
                            reason=f"Verify numeric option '{opt_name}' with negative value"
                        )
                    )
                if len(cases) < MAX_TEST_CASES:
                    cases.append(
                        TestCase(
                            arguments=[opt_name, "abc"],
                            category="OPTION_INVALID_VAL",
                            reason=f"Verify numeric option '{opt_name}' with non-numeric string value"
                        )
                    )
            else:
                if len(cases) < MAX_TEST_CASES:
                    cases.append(
                        TestCase(
                            arguments=[opt_name, "test_val"],
                            category="OPTION_VALID_VAL",
                            reason=f"Verify option '{opt_name}' with standard string value"
                        )
                    )

    return cases[:MAX_TEST_CASES]
