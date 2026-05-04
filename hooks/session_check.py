#!/usr/bin/env python3
"""SessionStart hook: warn if any shared reference file is stale (>90 days);
emit research corpus stats. Advisory only — exit 0 always."""

from __future__ import annotations

import datetime
import functools
import glob
import json
import os
import pathlib
import re
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    staleness_days_threshold: int
    check_paths: list[str]

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_LAZY_NAMES = frozenset({"staleness_days_threshold", "check_paths"})
_DEFAULT_CONFIG_PATH = pathlib.Path(__file__).resolve().parent / "session_check.json"


def _config_path() -> pathlib.Path:
    env = os.environ.get("SESSION_CHECK_CONFIG_PATH")
    return pathlib.Path(env) if env else _DEFAULT_CONFIG_PATH


@functools.lru_cache(maxsize=1)
def _load_config_cached(path: str) -> dict[str, Any]:
    p = pathlib.Path(path)
    if not p.exists():
        raise RuntimeError(f"session_check.json missing at {p} — see hooks/session_check.json")
    with p.open(encoding="utf-8") as fh:
        return json.load(fh)


def _resolve(name: str) -> Any:
    cfg = _load_config_cached(str(_config_path()))
    if name == "staleness_days_threshold":
        return int(cfg["staleness_days_threshold"])
    if name == "check_paths":
        return list(cfg["check_paths"])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __getattr__(name: str) -> Any:
    if name in _LAZY_NAMES:
        return _resolve(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _parse_last_refreshed(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            in_fm = False
            for line in f:
                line = line.rstrip("\n")
                if line == "---":
                    if not in_fm:
                        in_fm = True
                        continue
                    break
                if in_fm and line.startswith("last_refreshed:"):
                    ds = line.split(":", 1)[1].strip()
                    if not ds:
                        return None, None, None
                    if not DATE_RE.match(ds):
                        return None, ds, "not strict YYYY-MM-DD"
                    try:
                        return datetime.date.fromisoformat(ds), ds, None
                    except ValueError:
                        return None, ds, "not a valid calendar date"
    except FileNotFoundError:
        return None, None, None
    except (OSError, UnicodeDecodeError) as exc:
        return None, None, f"unreadable: {type(exc).__name__}"
    return None, None, None


def _check_stale_references(refs_dir, today):
    threshold = _resolve("staleness_days_threshold")
    oldest_age, oldest_info, malformed_errors = -1, None, []
    for path in glob.glob(os.path.join(refs_dir, "**", "*.md"), recursive=True):
        ref_date, ds, error = _parse_last_refreshed(path)
        if error is not None:
            malformed_errors.append((path, ds, error))
            continue
        if ref_date is None:
            continue
        age = (today - ref_date).days
        if age > threshold and age > oldest_age:
            oldest_age, oldest_info = age, (path, ds, age)
    return oldest_info, malformed_errors


def _check_research_corpus(plugin_root):
    rd = os.path.join(plugin_root, "research")
    if not os.path.isdir(rd):
        return None
    count = len(glob.glob(os.path.join(rd, "**", "*.md"), recursive=True))
    if count == 0:
        return None
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
    today, messages, oldest_info, oldest_age, mal = datetime.date.today(), [], None, -1, []
    for sub in _resolve("check_paths"):
        stale, errors = _check_stale_references(os.path.join(plugin_root, sub), today)
        mal.extend(errors)
        if stale and stale[2] > oldest_age:
            oldest_age, oldest_info = stale[2], stale
    for path, raw, error in mal:
        name = os.path.basename(path)
        if raw is None:
            messages.append(
                f"Cannot read reference file '{name}' ({error}). Run python scripts/validate_schema.py to audit."
            )
        else:
            messages.append(
                f"Unparseable last_refreshed in '{name}': '{raw}'"
                f" — expected YYYY-MM-DD ({error})."
                " Run python scripts/validate_schema.py to audit."
            )
    if oldest_info:
        path, ds, age = oldest_info
        name = os.path.basename(path)
        hint = " Run /refresh-engineering-baseline to update." if name == "engineering-baseline.md" else ""
        messages.append(
            f"Reference file '{name}' was last refreshed {ds}"
            f" ({age} days ago). Check if content is still current.{hint}"
        )
    if corpus_msg := _check_research_corpus(plugin_root):
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
