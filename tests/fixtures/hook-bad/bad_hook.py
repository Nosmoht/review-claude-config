"""Deliberately defective hook script — eval fixture for case 18 (D9 Hook Quality).

Seeded defects:
  HC-7: exits with sys.exit(1) on the success path (non-zero exit blocks PreToolUse
        when the hook should have allowed the action).
  SR-1: logs a credential-read to stdout via print(os.environ.get("API_TOKEN")),
        exposing any token value present in the environment.
  PY-1: reads input from sys.argv instead of sys.stdin; hook events provide
        JSON on stdin, so argv-based input silently drops the event payload.

This script is intentionally non-functional — it exists only as a detection
fixture. Do NOT register this hook in any real settings.json.
"""

import os
import sys

# PY-1: reads from sys.argv instead of sys.stdin
tool_name = sys.argv[1] if len(sys.argv) > 1 else "unknown"

# SR-1: logs a credential from the environment to stdout
print(os.environ.get("API_TOKEN"))

# HC-7: exits non-zero on the success path (should exit 0 to allow the action)
sys.exit(1)
