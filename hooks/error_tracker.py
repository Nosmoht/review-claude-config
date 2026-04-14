#!/usr/bin/env python3
"""StopFailure hook: log API errors to audit trace.

Hook type: StopFailure
Trigger: (all error types — no matcher)
Output: {} (async, non-blocking)

Writes api_error entries to $CLAUDE_PLUGIN_DATA/audit/{session_id}.audit.jsonl.
Captures error_type (rate_limit, authentication_failed, billing_error,
server_error, max_output_tokens, unknown).
"""

import datetime
import json
import os
import sys


def _audit_path(plugin_data, session_id):
    """Return path to session audit file, creating dir if needed."""
    audit_dir = os.path.join(plugin_data, "audit")
    os.makedirs(audit_dir, exist_ok=True)
    return os.path.join(audit_dir, f"{session_id}.audit.jsonl")


def main():
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if not plugin_data:
        print("{}")
        return

    input_data = json.load(sys.stdin)

    session_id = input_data.get("session_id", "unknown")

    entry = {
        "type": "api_error",
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "session_id": session_id,
        "error_type": input_data.get("error_type", "unknown"),
        "agent_id": input_data.get("agent_id"),
        "cwd": input_data.get("cwd"),
    }

    path = _audit_path(plugin_data, session_id)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")

    print("{}")


if __name__ == "__main__":  # pragma: no cover
    try:
        main()
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        print("{}")
    finally:
        sys.exit(0)
