#!/usr/bin/env python3
"""SessionEnd hook: rotate audit JSONL when it exceeds 10 MB.

Hook type: SessionEnd
Trigger: (no matcher)
Output: {} (no blocking)

Rotation strategy:
  - If $CLAUDE_PLUGIN_DATA/audit/<session_id>.audit.jsonl > 10 MB, rotate
    through a 3-generation suffix ladder: <name>.1 → <name>.2 → dropped.
  - Use os.replace() for atomicity on POSIX (clobbers existing target atomically).
  - Acquire fcntl.flock() on the source file for the rename duration to prevent
    races with concurrent writes from other hooks (PostToolUse audit_logger,
    SubagentStop delegation_tracker).
  - On any error, log to stderr and return {} — never block session end.
"""

from __future__ import annotations

import fcntl
import json
import os
import sys

ROTATE_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_GENERATIONS = 2  # .1 and .2; older drops off


def _rotate(path: str) -> None:
    """Rotate path through .1 → .2 → dropped, keeping ≤MAX_GENERATIONS suffixes."""
    # Drop the oldest before promoting. Start from the top.
    for n in range(MAX_GENERATIONS, 0, -1):
        src = f"{path}.{n}" if n > 1 else f"{path}.1"
        dst = f"{path}.{n + 1}"
        if n == MAX_GENERATIONS:
            # Drop the oldest rather than promoting past MAX_GENERATIONS.
            if os.path.exists(src):
                try:
                    os.remove(src)
                except OSError:
                    pass
            continue
        if os.path.exists(src):
            try:
                os.replace(src, dst)
            except OSError:
                pass
    # Finally move the live file to .1
    if os.path.exists(path):
        try:
            os.replace(path, f"{path}.1")
        except OSError:
            pass


def main() -> None:
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if not plugin_data:
        print("{}")
        return

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return

    session_id = input_data.get("session_id", "")
    if not session_id:
        print("{}")
        return

    audit_dir = os.path.join(plugin_data, "audit")
    audit_path = os.path.join(audit_dir, f"{session_id}.audit.jsonl")
    if not os.path.exists(audit_path):
        print("{}")
        return

    try:
        size = os.path.getsize(audit_path)
    except OSError:
        print("{}")
        return

    if size <= ROTATE_THRESHOLD_BYTES:
        print("{}")
        return

    # Acquire exclusive lock on the source file for the rotation duration.
    # Concurrent append writes from other hooks will block on this lock; since
    # SessionEnd fires late, this is acceptable.
    try:
        with open(audit_path, "a", encoding="utf-8") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                _rotate(audit_path)
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except OSError:
        # Never block session end on rotation failure.
        pass

    print("{}")


if __name__ == "__main__":  # pragma: no cover
    try:
        main()
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        print("{}")
    finally:
        sys.exit(0)
