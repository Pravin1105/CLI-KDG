"""
cli_kdg.help_parser
~~~~~~~~~~~~~~~~~~~

Manual help text parser for CLI-KDG v1.2.
Parses `--help` output text into a structured CLIModel without external packages or argparse.

Supported Option Syntax Patterns:
  --verbose
  --output FILE
  --output=FILE
  -o
  -o FILE
  -o, --output FILE
"""

from typing import List, Optional, Tuple
from cli_kdg.models import CLIOption, CLIModel


def parse_help_text(help_text: str) -> CLIModel:
    """
    Parses CLI --help text output and extracts option specifications into a CLIModel.

    Args:
        help_text (str): Captured stdout/stderr text from target --help execution.

    Returns:
        CLIModel: Structured model containing discovered CLIOption instances.
    """
    options: List[CLIOption] = []
    seen = set()

    for line in help_text.splitlines():
        line_clean = line.strip()
        if not line_clean or not ("-" in line_clean):
            continue

        # Look for lines containing option flag declarations (starting with '-' after leading spaces)
        # Option declarations typically start in the first column or after indentation
        leading_ws = len(line) - len(line.lstrip())
        if leading_ws > 20:
            # Skip deeply indented description wrap lines
            continue

        option = _extract_option_from_line(line_clean)
        if option and (option.short_name or option.long_name):
            key = (option.short_name, option.long_name)
            if key not in seen:
                seen.add(key)
                options.append(option)

    return CLIModel(options=options, raw_help_text=help_text)


def _extract_option_from_line(line: str) -> Optional[CLIOption]:
    """Helper method to parse a single line for short/long options and value hints."""
    tokens = line.split()
    if not tokens:
        return None

    short_name: Optional[str] = None
    long_name: Optional[str] = None
    requires_value: bool = False
    value_hint: Optional[str] = None

    idx = 0
    n = len(tokens)

    while idx < n:
        token = tokens[idx].rstrip(",")

        # Check for inline equal assignment e.g. --output=FILE or -o=FILE
        if "=" in token and token.startswith("-"):
            flag_part, val_part = token.split("=", 1)
            requires_value = True
            value_hint = val_part.strip("<>[]")
            if flag_part.startswith("--"):
                long_name = flag_part
            elif flag_part.startswith("-"):
                short_name = flag_part
            idx += 1
            break

        # Check for standard long option e.g. --output or --verbose
        if token.startswith("--"):
            # Avoid matching option list headers or non-flag separators
            if token == "--":
                idx += 1
                continue
            long_name = token
            # Check if next token is a value descriptor
            if idx + 1 < n:
                next_tok = tokens[idx + 1].strip("<>[]")
                if _is_value_descriptor(next_tok):
                    requires_value = True
                    value_hint = next_tok
                    idx += 1
            idx += 1
            continue

        # Check for short option e.g. -o or -v
        if token.startswith("-") and len(token) >= 2 and not token.startswith("--"):
            # Ensure token is an option flag (e.g. -o, -v, -h)
            if token[1].isalnum():
                short_name = token
                if idx + 1 < n:
                    next_tok = tokens[idx + 1].strip("<>[]")
                    if _is_value_descriptor(next_tok):
                        requires_value = True
                        value_hint = next_tok
                        idx += 1
                idx += 1
                continue

        # Stop scanning option flags once option description text is reached
        if not token.startswith("-") and not (token in [",", "/"]):
            break

        idx += 1

    if short_name or long_name:
        return CLIOption(
            short_name=short_name,
            long_name=long_name,
            requires_value=requires_value,
            value_hint=value_hint
        )

    return None


def _is_value_descriptor(token: str) -> bool:
    """Determines if a token represents an option value descriptor hint (e.g., FILE, INTEGER, <path>)."""
    if not token or token.startswith("-"):
        return False

    # Check for all-uppercase value hints e.g. FILE, PATH, INT, NUM, INTEGER, DIR, ARG, VALUE
    if token.isupper() and len(token) >= 2:
        return True

    # Check for typical hint names
    known_hints = {"file", "path", "int", "integer", "num", "number", "dir", "arg", "val", "value", "str", "string"}
    if token.lower() in known_hints:
        return True

    return False
