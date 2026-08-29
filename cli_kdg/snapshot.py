"""
cli_kdg.snapshot — Snapshot Persistence & Serialization Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Handles creation, JSON serialization, disk storage, and versioned loading (version == 1).
"""

import os
import json
from typing import Optional, List
from cli_kdg.models import Snapshot, TestObservation
from cli_kdg.discover import discover_target
from cli_kdg.errors import CLKDGUserError, CLKDGExecutionError


def create_snapshot(target: str, target_args: List[str], timeout: Optional[float] = None) -> Snapshot:
    """Runs automated discovery against target CLI and packages observations into a Snapshot."""
    disc_res = discover_target(target, target_args, timeout=timeout)
    if disc_res.discovery_error or not disc_res.is_success():
        raise CLKDGExecutionError(f"Snapshot creation failed: {disc_res.discovery_error or 'Discovery failed'}")

    obs_list = [
        TestObservation(c.arguments, c.category, c.reason, r.exit_code, r.stdout, r.stderr, r.runtime_ms, r.termination_type)
        for c, r in disc_res.case_results
    ]
    return Snapshot(target=target, target_args=target_args, observations=obs_list)


def save_snapshot(snapshot: Snapshot, filepath: str) -> None:
    """Serializes a Snapshot object to a JSON file."""
    try:
        dir_name = os.path.dirname(os.path.abspath(filepath))
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(snapshot.to_dict(), f, indent=2, ensure_ascii=False)
    except OSError as err:
        raise CLKDGUserError(f"Failed to write snapshot file '{filepath}': {err}")


def load_snapshot(filepath: str) -> Snapshot:
    """Loads and deserializes a versioned Snapshot object from a JSON file."""
    if not os.path.exists(filepath):
        raise CLKDGUserError(f"Snapshot file '{filepath}' does not exist.")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as err:
        raise CLKDGUserError(f"Corrupt snapshot file '{filepath}': Invalid JSON format ({err}).")

    if not isinstance(data, dict):
        raise CLKDGUserError(f"Corrupt snapshot file '{filepath}': Expected top-level JSON object.")

    if data.get("version") != 1:
        raise CLKDGUserError(f"Unsupported snapshot format version '{data.get('version')}' in '{filepath}'. Only version 1 is supported by CLI-KDG v1.3.")

    try:
        return Snapshot.from_dict(data)
    except Exception as err:
        raise CLKDGUserError(f"Corrupt snapshot schema in '{filepath}': {err}")
