"""
cli_kdg.parser — Manual Command Line Argument Parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Parses sys.argv for run, discover, snapshot, and replay subcommands without argparse.
"""

from typing import List, Tuple, Optional
from cli_kdg.errors import CLKDGUserError

VALID_SUBCOMMANDS = {"run", "discover", "snapshot", "replay"}


def parse_args(args: List[str]) -> Tuple[str, str, List[str], Optional[float], Optional[str]]:
    """Manually parses argument vector into (subcommand, target, target_args, timeout, output_file)."""
    if not args:
        raise CLKDGUserError("Missing subcommand. Usage: cli-kdg <run|discover|snapshot|replay> [options] <target> [args...]")

    subcommand = args[0]
    if subcommand not in VALID_SUBCOMMANDS:
        raise CLKDGUserError(f"Unknown subcommand '{subcommand}'. Supported: 'run', 'discover', 'snapshot', 'replay'.")

    index, timeout, output_file, n = 1, None, None, len(args)

    while index < n:
        token = args[index]
        if token in ["--timeout", "-t"]:
            if index + 1 >= n:
                raise CLKDGUserError("Flag '--timeout' requires a numeric seconds value.")
            try:
                timeout = float(args[index + 1])
                if timeout <= 0:
                    raise ValueError()
            except ValueError:
                raise CLKDGUserError(f"Invalid timeout value '{args[index + 1]}'. Must be a positive number.")
            index += 2
        elif token.startswith("--timeout="):
            try:
                timeout = float(token.split("=", 1)[1])
                if timeout <= 0:
                    raise ValueError()
            except ValueError:
                raise CLKDGUserError(f"Invalid timeout value '{token.split('=', 1)[1]}'. Must be a positive number.")
            index += 1
        elif token in ["--output", "-o"]:
            if index + 1 >= n:
                raise CLKDGUserError("Flag '--output' requires a output file path.")
            output_file = args[index + 1]
            index += 2
        elif token.startswith("--output="):
            output_file = token.split("=", 1)[1]
            index += 1
        elif token == "--":
            index += 1
            break
        elif token.startswith("-"):
            raise CLKDGUserError(f"Unknown CLI-KDG option '{token}'.")
        else:
            break

    if index >= n:
        msg = "Missing snapshot file and target executable." if subcommand == "replay" else "Missing target executable."
        raise CLKDGUserError(f"{msg} Usage: cli-kdg {subcommand} [options] <target> [target arguments...]")

    return subcommand, args[index], args[index + 1:], timeout, output_file
