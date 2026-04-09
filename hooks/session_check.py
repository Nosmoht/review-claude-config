#!/usr/bin/env python3
"""SessionStart hook: warn if any shared reference file is stale (>90 days);
emit research corpus stats for maintainer orientation.

Hard-enforced: engineering-baseline.md (with specific refresh command hint).
Opportunistic: all *.md files in the references/ directory tree, including
domain-cache/ subdirectory. Reports only the single oldest stale file to
avoid noise. Malformed last_refreshed values are surfaced as warnings (exit 0
preserved — validate_schema.py handles hard enforcement via CI).

Research corpus: counts all *.md files under research/ and emits corpus
size so the maintainer knows CAG-range loading is available.
"""

import datetime
import glob
import json
import os
import re
import sys

# Keep in sync with scripts/validate_schema.py DATE_RE
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_last_refreshed(path):
    """Return (date, date_str, error) from YAML frontmatter last_refreshed.

    - Valid date:              (datetime.date, "YYYY-MM-DD", None)
    - Field absent/no FM/I/O: (None, None, None)
    - Malformed date present:  (None, raw_str, error_message)
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
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
                    if not date_str:
                        return None, None, None  # empty value → treat as absent
                    if not DATE_RE.match(date_str):
                        return None, date_str, "not strict YYYY-MM-DD"
                    try:
                        return datetime.date.fromisoformat(date_str), date_str, None
                    except ValueError:
                        return None, date_str, "not a valid calendar date"
    except (OSError, UnicodeDecodeError):
        pass
    return None, None, None


def _check_stale_references(refs_dir, today):
    """Return (oldest_stale, malformed_errors) for all reference files.

    oldest_stale: (path, date_str, age) for the single oldest stale file, or None.
    malformed_errors: list of (path, raw_value, error_msg) for malformed dates.
    """
    ref_files = glob.glob(os.path.join(refs_dir, "**", "*.md"), recursive=True)
    oldest_age = -1
    oldest_info = None
    malformed_errors = []

    for path in ref_files:
        ref_date, date_str, error = _parse_last_refreshed(path)
        if error is not None:
            malformed_errors.append((path, date_str, error))
            continue
        if ref_date is None:
            continue
        age = (today - ref_date).days
        if age > 90 and age > oldest_age:
            oldest_age = age
            oldest_info = (path, date_str, age)

    return oldest_info, malformed_errors


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

    # --- Stale reference file check (includes domain-cache/) ---
    refs_dir = os.path.join(plugin_root, "skills", "review-claude-config", "references")
    stale, malformed_errors = _check_stale_references(refs_dir, today)

    # Malformed dates: surface as warnings (one per file)
    for path, raw, error in malformed_errors:
        name = os.path.basename(path)
        messages.append(
            f"Unparseable last_refreshed in '{name}': '{raw}' — expected YYYY-MM-DD"
            f" ({error}). Run python scripts/validate_schema.py to audit."
        )

    # Staleness: report only the oldest stale file
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
