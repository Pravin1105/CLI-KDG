#!/usr/bin/env python3
"""Fixture: Generates large volume STDOUT and STDERR output to test pipe buffering."""
import sys

large_stdout = "A" * 100000
large_stderr = "B" * 100000

for _ in range(5):
    sys.stdout.write(large_stdout + "\n")
    sys.stderr.write(large_stderr + "\n")

sys.stdout.flush()
sys.stderr.flush()
sys.exit(0)
