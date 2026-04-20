#!/usr/bin/env python3
"""SubagentStart / SubagentStop hook: log delegation events to audit trace.

Hook type: SubagentStart, SubagentStop
Trigger: (all agent types — no matcher)
Output: {} (async, no blocking)

Writes delegation entries to $CLAUDE_PLUGIN_DATA/audit/{session_id}.audit.jsonl.
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
    hook_event = input_data.get("hook_event_name", "")

    event = "start" if hook_event == "SubagentStart" else "stop"

    entry = {
        "type": "delegation",
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "session_id": session_id,
        "agent_id": input_data.get("agent_id"),
        "agent_type": input_data.get("agent_type"),
        "parent_agent_id": input_data.get("parent_agent_id"),
        "tool_use_id": input_data.get("tool_use_id"),
        "event": event,
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
