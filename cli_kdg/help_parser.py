"""
cli_kdg.help_parser — Manual CLI Help Output Text Parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Extracts option specifications from --help text without regex or external packages.
"""

from typing import List, Optional
from cli_kdg.models import CLIOption, CLIModel


def parse_help_text(help_text: str) -> CLIModel:
    """Parses CLI --help text output and extracts option specifications into a CLIModel."""
    options: List[CLIOption] = []
    seen = set()

    for line in help_text.splitlines():
        line_clean = line.strip()
        if not line_clean or "-" not in line_clean or len(line) - len(line.lstrip()) > 20:
            continue

        opt = _extract_option_from_line(line_clean)
        if opt and (opt.short_name or opt.long_name):
            key = (opt.short_name, opt.long_name)
            if key not in seen:
                seen.add(key)
                options.append(opt)

    return CLIModel(options=options, raw_help_text=help_text)


def _extract_option_from_line(line: str) -> Optional[CLIOption]:
    """Extracts short/long option tokens and value descriptor hints from a single text line."""
    tokens = line.split()
    if not tokens:
        return None

    short_name, long_name, requires_value, value_hint = None, None, False, None
    idx, n = 0, len(tokens)

    while idx < n:
        token = tokens[idx].rstrip(",")

        if "=" in token and token.startswith("-"):
            flag_part, val_part = token.split("=", 1)
            requires_value, value_hint = True, val_part.strip("<>[]")
            if flag_part.startswith("--"):
                long_name = flag_part
            elif flag_part.startswith("-"):
                short_name = flag_part
            break

        if token.startswith("--") and token != "--":
            long_name = token
            if idx + 1 < n and _is_value_descriptor(tokens[idx + 1].strip("<>[]")):
                requires_value, value_hint = True, tokens[idx + 1].strip("<>[]")
                idx += 1
            idx += 1
            continue

        if token.startswith("-") and len(token) >= 2 and not token.startswith("--") and token[1].isalnum():
            short_name = token
            if idx + 1 < n and _is_value_descriptor(tokens[idx + 1].strip("<>[]")):
                requires_value, value_hint = True, tokens[idx + 1].strip("<>[]")
                idx += 1
            idx += 1
            continue

        if not token.startswith("-") and token not in [",", "/"]:
            break
        idx += 1

    if short_name or long_name:
        return CLIOption(short_name, long_name, requires_value, value_hint)
    return None


def _is_value_descriptor(token: str) -> bool:
    """Determines if a token represents a value descriptor hint (e.g. FILE, INTEGER, <path>)."""
    if not token or token.startswith("-"):
        return False
    known = {"file", "path", "int", "integer", "num", "number", "dir", "arg", "val", "value", "str", "string"}
    return (token.isupper() and len(token) >= 2) or token.lower() in known
