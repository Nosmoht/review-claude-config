#!/usr/bin/env python3
"""SessionEnd hook: compute and append session summary to audit trace.

Hook type: SessionEnd
Trigger: (all session end reasons — no matcher)
Output: {} (synchronous — runs at session end, no user impact)

Reads accumulated audit entries from $CLAUDE_PLUGIN_DATA/audit/{session_id}.audit.jsonl,
computes summary metrics, and appends a session_summary entry as the final line.
"""

import datetime
import json
import os
import sys


def _audit_path(plugin_data, session_id):
    """Return path to session audit file."""
    return os.path.join(plugin_data, "audit", f"{session_id}.audit.jsonl")


def _compute_summary(entries, session_id):
    """Compute session metrics from audit entries."""
    tool_calls = [e for e in entries if e.get("type") == "tool_call"]
    delegations = [e for e in entries if e.get("type") == "delegation"]

    tool_errors = sum(1 for e in tool_calls if not e.get("success", True))

    # Compute delegation max depth (approximate from start/stop nesting)
    depth = 0
    max_depth = 0
    for d in delegations:
        if d.get("event") == "start":
            depth += 1
            max_depth = max(max_depth, depth)
        elif d.get("event") == "stop" and depth > 0:
            depth -= 1

    # Duration from first to last timestamp
    timestamps = []
    for e in entries:
        ts = e.get("ts")
        if ts:
            try:
                timestamps.append(datetime.datetime.fromisoformat(ts))
            except (ValueError, TypeError):
                pass

    duration_sec = 0
    if len(timestamps) >= 2:
        duration_sec = int((max(timestamps) - min(timestamps)).total_seconds())

    return {
        "type": "session_summary",
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "session_id": session_id,
        "duration_sec": duration_sec,
        "tool_calls": len(tool_calls),
        "tool_errors": tool_errors,
        "delegations": len([d for d in delegations if d.get("event") == "start"]),
        "max_depth": max_depth,
    }


def main():
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if not plugin_data:
        print("{}")
        return

    input_data = json.load(sys.stdin)
    session_id = input_data.get("session_id", "unknown")

    path = _audit_path(plugin_data, session_id)
    if not os.path.isfile(path):
        # No audit data for this session (hooks may not have fired)
        print("{}")
        return

    # Read existing entries
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    if not entries:
        print("{}")
        return

    # Idempotency guard: skip if summary already exists
    if any(e.get("type") == "session_summary" for e in entries):
        print("{}")
        return

    # Compute and append summary
    summary = _compute_summary(entries, session_id)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary, default=str) + "\n")

    print("{}")


if __name__ == "__main__":  # pragma: no cover
    try:
        main()
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        print("{}")
    finally:
        sys.exit(0)
