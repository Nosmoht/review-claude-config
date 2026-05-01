#!/usr/bin/env python3
"""PreToolUse hook: inject quality guidelines when editing skill/agent/rule files."""

import json
import os
import sys
from fnmatch import fnmatch

SKILL_PATTERNS = [
    "*/skills/*/SKILL.md",
    "*/.claude/agents/*.md",
    "*/.claude/rules/*.md",
]


def main():
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not plugin_root:
        print("{}")
        return

    input_data = json.load(sys.stdin)
    file_path = input_data.get("tool_input", {}).get("file_path", "")

    abs_path = os.path.abspath(file_path) if file_path else ""
    if not any(fnmatch(abs_path, p) for p in SKILL_PATTERNS):
        print("{}")
        return

    guidelines_path = os.path.join(plugin_root, "hooks", "guidelines.md")
    # Defensive read: a missing/unreadable guidelines.md must not raise.
    # Covers FileNotFoundError, PermissionError, IsADirectoryError, and any
    # other OSError. The hook degrades to pass-through ("{}") rather than
    # falling back to the top-level Exception wrapper (which prints a
    # diagnostic to stderr and is therefore noisier than necessary).
    # See GitHub issue #118: phantom-block class from anthropics/claude-code#21988.
    try:
        with open(guidelines_path, "r", encoding="utf-8") as f:
            guidelines = f.read()
    except OSError:
        print("{}")
        return

    print(json.dumps({"systemMessage": guidelines}))


if __name__ == "__main__":  # pragma: no cover
    try:
        main()
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        print("{}")
    finally:
        sys.exit(0)
