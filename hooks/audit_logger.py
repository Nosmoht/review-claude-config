#!/usr/bin/env python3
"""PostToolUse / PostToolUseFailure hook: append audit trace entry per tool call.

Hook type: PostToolUse, PostToolUseFailure
Trigger: (all tools — no matcher)
Output: {} (async, no blocking)

Writes structured JSONL to $CLAUDE_PLUGIN_DATA/audit/{session_id}.audit.jsonl.
Tool input is hashed (SHA-256) for privacy — raw arguments are never logged.
"""

import datetime
import hashlib
import json
import os
import sys


def _hash_input(tool_input):
    """SHA-256 hash of JSON-serialized tool input for privacy."""
    try:
        raw = json.dumps(tool_input, sort_keys=True, default=str)
        return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()[:16]
    except (TypeError, ValueError):
        return "sha256:unknown"


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
    hook_event = input_data.get("hook_event_name", "")
    success = hook_event != "PostToolUseFailure"

    entry = {
        "type": "tool_call",
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "session_id": session_id,
        "agent_id": input_data.get("agent_id"),
        "agent_type": input_data.get("agent_type"),
        "tool_name": input_data.get("tool_name", "unknown"),
        "tool_use_id": input_data.get("tool_use_id"),
        "input_hash": _hash_input(input_data.get("tool_input", {})),
        "success": success,
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
