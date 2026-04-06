#!/usr/bin/env python3
"""SessionStart hook: warn if engineering baseline is stale (>90 days)."""

import datetime
import json
import os
import sys


def main():
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not plugin_root:
        print("{}")
        return

    baseline = os.path.join(
        plugin_root, "skills", "review-claude-config",
        "references", "engineering-baseline.md",
    )
    with open(baseline, "r") as f:
        for line in f:
            if line.startswith("last_refreshed:"):
                date_str = line.split(":", 1)[1].strip()
                ref_date = datetime.date.fromisoformat(date_str)
                age = (datetime.date.today() - ref_date).days
                if age > 90:
                    msg = (
                        f"Engineering baseline last refreshed {date_str} "
                        f"({age} days ago). "
                        f"Run /refresh-engineering-baseline to update."
                    )
                    print(json.dumps({
                        "hookSpecificOutput": {
                            "hookEventName": "SessionStart",
                            "additionalContext": msg,
                        }
                    }))
                    return
                break

    print("{}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        print("{}")
    finally:
        sys.exit(0)
