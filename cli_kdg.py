#!/usr/bin/env python3
"""
CLI-KDG: Single-file executable entry point for CLI-KDG v1.1.
Executes target commands using POSIX process primitives without third-party dependencies.
"""

import sys
from cli_kdg.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
