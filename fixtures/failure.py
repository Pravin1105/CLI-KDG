#!/usr/bin/env python3
"""Fixture: Failed execution returning exit code 3."""
import sys

sys.stderr.write("Fatal execution error occurred!\n")
sys.exit(3)
