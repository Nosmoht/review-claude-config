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

    if not any(fnmatch(file_path, p) for p in SKILL_PATTERNS):
        print("{}")
        return

    guidelines_path = os.path.join(plugin_root, "hooks", "guidelines.md")
    with open(guidelines_path, "r") as f:
        guidelines = f.read()

    print(json.dumps({"systemMessage": guidelines}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("{}")
    finally:
        sys.exit(0)
