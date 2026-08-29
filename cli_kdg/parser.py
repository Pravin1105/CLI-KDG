"""
cli_kdg.parser
~~~~~~~~~~~~~~

Manual CLI argument parser for CLI-KDG (v1.1 & v1.2).
Parses command-line tokens without external libraries or argparse dependencies.

Supported Syntax:
    cli-kdg run [--timeout SECONDS] <target> [target arguments...]
    cli-kdg discover [--timeout SECONDS] <target> [target arguments...]
"""

from typing import List, Tuple, Optional
from cli_kdg.errors import CLKDGUserError

VALID_SUBCOMMANDS = {"run", "discover"}


def parse_args(args: List[str]) -> Tuple[str, str, List[str], Optional[float]]:
    """
    Manually parses command line argument vector for CLI-KDG.

    Args:
        args: List of argument strings (excluding script/executable name).

    Returns:
        Tuple containing:
            - subcommand (str): Subcommand action ('run' or 'discover').
            - target (str): Executable target path or command name.
            - target_args (List[str]): List of arguments to pass to target.
            - timeout (Optional[float]): Timeout limit in seconds, or None if unspecified.

    Raises:
        CLKDGUserError: If syntax is invalid, missing subcommand/target, or malformed flags.
    """
    if not args:
        raise CLKDGUserError(
            "Missing subcommand. Usage: cli-kdg <run|discover> [--timeout SECONDS] <target> [target arguments...]"
        )

    subcommand = args[0]
    if subcommand not in VALID_SUBCOMMANDS:
        raise CLKDGUserError(
            f"Unknown subcommand '{subcommand}'. Supported subcommands: 'run', 'discover'. "
            "Usage: cli-kdg <run|discover> [--timeout SECONDS] <target> [target arguments...]"
        )

    index = 1
    timeout: Optional[float] = None
    n = len(args)

    # Parse optional CLI-KDG flags before target command
    while index < n:
        token = args[index]
        if token == "--timeout" or token == "-t":
            if index + 1 >= n:
                raise CLKDGUserError("Flag '--timeout' requires a numeric seconds value.")
            timeout_str = args[index + 1]
            try:
                timeout = float(timeout_str)
                if timeout <= 0:
                    raise ValueError()
            except ValueError:
                raise CLKDGUserError(f"Invalid timeout value '{timeout_str}'. Must be a positive number.")
            index += 2
        elif token.startswith("--timeout="):
            val_str = token.split("=", 1)[1]
            try:
                timeout = float(val_str)
                if timeout <= 0:
                    raise ValueError()
            except ValueError:
                raise CLKDGUserError(f"Invalid timeout value '{val_str}'. Must be a positive number.")
            index += 1
        elif token == "--":
            # Explicit separator denoting start of target command
            index += 1
            break
        elif token.startswith("-"):
            raise CLKDGUserError(f"Unknown CLI-KDG option '{token}'.")
        else:
            # First non-flag token represents target executable
            break

    if index >= n:
        raise CLKDGUserError(
            f"Missing target executable. Usage: cli-kdg {subcommand} [--timeout SECONDS] <target> [target arguments...]"
        )

    target = args[index]
    target_args = args[index + 1 :]

    return subcommand, target, target_args, timeout
