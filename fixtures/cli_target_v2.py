#!/usr/bin/env python3
"""
CLI-KDG Discovery Target Fixture (Version 2.0 with Intentional Behavioral Regressions)
======================================================================================

A mock CLI application v2.0 used to test v1.3 snapshot replay and regression reporting.
Implements intentional behavioral changes compared to fixtures/cli_target.py:
1. --count 0 exits with code 1 instead of code 0.
2. --verbose outputs "Verbose v2 mode active" instead of "Verbose execution enabled".
"""

import sys

HELP_TEXT = """
CLI Target App v2.0
Usage: cli_target.py [OPTIONS]

Options:
  -h, --help           Show this help message and exit
  -v, --verbose        Enable verbose logging output
  -o, --output FILE    Specify output target file path
  --count INTEGER      Specify execution iteration count
"""


def main():
    args = sys.argv[1:]
    if not args or "--help" in args or "-h" in args:
        print(HELP_TEXT.strip())
        sys.exit(0)

    if "--unknown-flag-xyz-kdg" in args:
        sys.stderr.write("Error: Unrecognized option '--unknown-flag-xyz-kdg'\n")
        sys.exit(2)

    verbose = "--verbose" in args or "-v" in args
    output_file = None
    count = 1

    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg in ["--output", "-o"]:
            if idx + 1 >= len(args):
                sys.stderr.write("Error: Option '--output' requires a FILE argument.\n")
                sys.exit(1)
            output_file = args[idx + 1]
            idx += 2
        elif arg == "--count":
            if idx + 1 >= len(args):
                sys.stderr.write("Error: Option '--count' requires an INTEGER argument.\n")
                sys.exit(1)
            try:
                count = int(args[idx + 1])
                # Behavioral Regression in v2: zero is rejected as invalid!
                if count <= 0:
                    sys.stderr.write("Error: '--count' must be strictly positive.\n")
                    sys.exit(1)
            except ValueError:
                sys.stderr.write(f"Error: Invalid integer value '{args[idx + 1]}' for '--count'.\n")
                sys.exit(1)
            idx += 2
        else:
            idx += 1

    if verbose:
        print(f"Verbose v2 mode active. Output file: {output_file}, Count: {count}")
    else:
        print(f"Executed v2. Output: {output_file}, Count: {count}")

    sys.exit(0)


if __name__ == "__main__":
    main()
