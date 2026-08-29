"""
cli_kdg.__main__
~~~~~~~~~~~~────

Main execution entry point when CLI-KDG is invoked via:
    python3 -m cli_kdg run ...
    python3 -m cli_kdg discover ...
"""

import sys
from cli_kdg.parser import parse_args
from cli_kdg.process import execute_target
from cli_kdg.reporter import format_report, format_discovery_report
from cli_kdg.discover import discover_target
from cli_kdg.errors import CLKDGUserError, CLKDGExecutionError, format_error_message


def main() -> int:
    """CLI-KDG entry point routine."""
    try:
        subcommand, target, target_args, timeout = parse_args(sys.argv[1:])

        if subcommand == "run":
            result = execute_target(target, target_args, timeout=timeout)
            report = format_report(result)
            print(report)
            return 0 if result.is_success() else (result.exit_code or 1)
        elif subcommand == "discover":
            discovery_res = discover_target(target, target_args, timeout=timeout)
            report = format_discovery_report(discovery_res)
            print(report)
            return 0 if discovery_res.is_success() else 1
        else:
            raise CLKDGUserError(f"Unsupported subcommand '{subcommand}'.")

    except CLKDGUserError as err:
        sys.stderr.write(f"{format_error_message(str(err))}\n")
        return 2
    except CLKDGExecutionError as err:
        sys.stderr.write(f"{format_error_message(str(err))}\n")
        return 1
    except Exception as err:
        sys.stderr.write(f"{format_error_message(f'Unexpected error: {err}')}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
