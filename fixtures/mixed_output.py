#!/usr/bin/env python3
"""Fixture: Interleaving STDOUT and STDERR messages."""
import sys

print("STDOUT message line 1")
sys.stderr.write("STDERR error line 1\n")
sys.stderr.flush()
print("STDOUT message line 2")
sys.stderr.write("STDERR error line 2\n")
sys.exit(0)
