"""
cli_kdg.parser
~~~~~~~~~~~~~~

Manual CLI argument parser for CLI-KDG.
Parses command-line tokens without external libraries or argparse dependencies.

Supported Syntax:
    cli-kdg run [--timeout SECONDS] <target> [target arguments...]
"""

from typing import List, Tuple, Optional
from cli_kdg.errors import CLKDGUserError


def parse_args(args: List[str]) -> Tuple[str, List[str], Optional[float]]:
    """
    Manually parses command line argument vector.

    Args:
        args: List of argument strings (excluding the script/executable name).

    Returns:
        Tuple containing:
            - target (str): Executable target path or command name.
            - target_args (List[str]): List of arguments to pass to the target.
            - timeout (Optional[float]): Timeout limit in seconds, or None if unspecified.

    Raises:
        CLKDGUserError: If syntax is invalid, missing target, or malformed flags.
    """
    if not args:
        raise CLKDGUserError(
            "Missing subcommand. Usage: cli-kdg run [--timeout SECONDS] <target> [target arguments...]"
        )

    # First positional token must be the 'run' action command
    if args[0] != "run":
        raise CLKDGUserError(
            f"Unknown subcommand '{args[0]}'. Only 'run' is supported. "
            "Usage: cli-kdg run [--timeout SECONDS] <target> [target arguments...]"
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
            "Missing target executable. Usage: cli-kdg run [--timeout SECONDS] <target> [target arguments...]"
        )

    target = args[index]
    target_args = args[index + 1 :]

    return target, target_args, timeout
