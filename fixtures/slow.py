#!/usr/bin/env python3
"""Fixture: Slow execution sleeping for 3 seconds to trigger timeout."""
import time
import sys

print("Starting long-running process...")
sys.stdout.flush()
time.sleep(3)
print("Finished long-running process!")
