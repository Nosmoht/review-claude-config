#!/usr/bin/env python3
"""SessionStart hook: warn if any shared reference file is stale (>90 days).

Hard-enforced: engineering-baseline.md (with specific refresh command hint).
Opportunistic: all other *.md files in the same references/ directory.
Reports only the single oldest stale file to avoid noise.
"""

import datetime
import glob
import json
import os
import sys


def _parse_last_refreshed(path):
    """Return (date, date_str) from YAML frontmatter last_refreshed, or (None, None)."""
    try:
        with open(path, "r") as f:
            in_frontmatter = False
            for line in f:
                line = line.rstrip("\n")
                if line == "---":
                    if not in_frontmatter:
                        in_frontmatter = True
                        continue
                    else:
                        break  # end of frontmatter
                if in_frontmatter and line.startswith("last_refreshed:"):
                    date_str = line.split(":", 1)[1].strip()
                    return datetime.date.fromisoformat(date_str), date_str
    except Exception:
        pass
    return None, None


def main():
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not plugin_root:
        print("{}")
        return

    refs_dir = os.path.join(
        plugin_root, "skills", "review-claude-config", "references"
    )
    ref_files = glob.glob(os.path.join(refs_dir, "*.md"))

    today = datetime.date.today()
    oldest_age = -1
    oldest_info = None

    for path in ref_files:
        ref_date, date_str = _parse_last_refreshed(path)
        if ref_date is None:
            continue
        age = (today - ref_date).days
        if age > 90 and age > oldest_age:
            oldest_age = age
            oldest_info = (path, date_str, age)

    if oldest_info:
        path, date_str, age = oldest_info
        name = os.path.basename(path)
        hint = ""
        if name == "engineering-baseline.md":
            hint = " Run /refresh-engineering-baseline to update."
        msg = (
            f"Reference file '{name}' was last refreshed {date_str} "
            f"({age} days ago). Check if content is still current.{hint}"
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": msg,
            }
        }))
        return

    print("{}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        print("{}")
    finally:
        sys.exit(0)
