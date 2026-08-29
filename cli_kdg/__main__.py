"""
cli_kdg.__main__
~~~~~~~~~~~~~~~~

Main execution entry point when CLI-KDG is invoked via:
    python3 -m cli_kdg run ...
"""

import sys
from cli_kdg.parser import parse_args
from cli_kdg.process import execute_target
from cli_kdg.reporter import format_report
from cli_kdg.errors import CLKDGUserError, CLKDGExecutionError, format_error_message


def main() -> int:
    """CLI-KDG entry point routine."""
    try:
        target, target_args, timeout = parse_args(sys.argv[1:])
        result = execute_target(target, target_args, timeout)
        report = format_report(result)
        print(report)
        return 0 if result.is_success() else (result.exit_code or 1)
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
