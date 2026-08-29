"""
cli_kdg.__main__ — Main Module Entry Point
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Invoked via: python3 -m cli_kdg <run|discover|snapshot|replay>
"""

import sys
from cli_kdg.parser import parse_args
from cli_kdg.process import execute_target
from cli_kdg.reporter import format_report, format_discovery_report, format_snapshot_report, format_replay_report
from cli_kdg.discover import discover_target
from cli_kdg.snapshot import create_snapshot, save_snapshot, load_snapshot
from cli_kdg.replay import replay_snapshot
from cli_kdg.errors import CLKDGUserError, CLKDGExecutionError, format_error_message


def main() -> int:
    """CLI-KDG main execution entry point routine."""
    try:
        subcommand, target, target_args, timeout, output_file = parse_args(sys.argv[1:])

        if subcommand == "run":
            res = execute_target(target, target_args, timeout=timeout)
            print(format_report(res))
            return 0 if res.is_success() else (res.exit_code or 1)

        if subcommand == "discover":
            res = discover_target(target, target_args, timeout=timeout)
            print(format_discovery_report(res))
            return 0 if res.is_success() else 1

        if subcommand == "snapshot":
            filepath = output_file or "snapshot.json"
            snap = create_snapshot(target, target_args, timeout=timeout)
            save_snapshot(snap, filepath)
            print(format_snapshot_report(snap, filepath))
            return 0

        if subcommand == "replay":
            if not target_args:
                raise CLKDGUserError("Missing replay target executable. Usage: cli-kdg replay [options] <snapshot_file> <target> [args...]")
            snap = load_snapshot(target)
            replay_res = replay_snapshot(snap, target_args[0], target_args[1:], timeout=timeout)
            replay_res.snapshot_path = target
            print(format_replay_report(replay_res))
            return 0 if replay_res.is_success() else 1

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
