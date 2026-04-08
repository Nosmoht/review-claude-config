#!/usr/bin/env python3
"""SessionStart hook: warn if any shared reference file is stale (>90 days);
emit research corpus stats for maintainer orientation.

Hard-enforced: engineering-baseline.md (with specific refresh command hint).
Opportunistic: all other *.md files in the same references/ directory.
Reports only the single oldest stale file to avoid noise.

Research corpus: counts all *.md files under research/ and emits corpus
size so the maintainer knows CAG-range loading is available.
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


def _check_stale_references(refs_dir, today):
    """Return (path, date_str, age) for the single oldest stale reference file, or None."""
    ref_files = glob.glob(os.path.join(refs_dir, "*.md"))
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

    return oldest_info


def _check_research_corpus(plugin_root):
    """Return a one-line corpus summary, or None if research/ does not exist."""
    research_dir = os.path.join(plugin_root, "research")
    if not os.path.isdir(research_dir):
        return None
    md_files = glob.glob(os.path.join(research_dir, "**", "*.md"), recursive=True)
    count = len(md_files)
    if count == 0:
        return None
    # Rough estimate: ~1 K tokens per file on average
    return (
        f"Research corpus: {count} files (~{count}K tokens). "
        f"Fits in CAG range for 200K-context models. "
        f"Load selectively via 'Research References' in CLAUDE.md."
    )


def main():
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if not plugin_root:
        print("{}")
        return

    today = datetime.date.today()
    messages = []

    # --- Stale reference file check ---
    refs_dir = os.path.join(plugin_root, "skills", "review-claude-config", "references")
    stale = _check_stale_references(refs_dir, today)
    if stale:
        path, date_str, age = stale
        name = os.path.basename(path)
        hint = ""
        if name == "engineering-baseline.md":
            hint = " Run /refresh-engineering-baseline to update."
        messages.append(
            f"Reference file '{name}' was last refreshed {date_str} "
            f"({age} days ago). Check if content is still current.{hint}"
        )

    # --- Research corpus stats ---
    corpus_msg = _check_research_corpus(plugin_root)
    if corpus_msg:
        messages.append(corpus_msg)

    if messages:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": " | ".join(messages),
                    }
                }
            )
        )
        return

    print("{}")


if __name__ == "__main__":  # pragma: no cover
    try:
        main()
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        print("{}")
    finally:
        sys.exit(0)
