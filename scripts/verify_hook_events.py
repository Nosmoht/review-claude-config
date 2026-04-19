#!/usr/bin/env python3
"""Verify hooks.json events against installed Claude Code CLI version.

For each event registered in the supplied hooks.json, look it up in the
repo-local event-to-version map (sourced from
research/hook-observation/hook-based-runtime-observation-patterns.md
"Full Event Catalog" table) and emit a JSON status entry.

Status values:
- ok: event known, installed CLI >= min CLI version.
- version_too_old: event known but installed CLI < required min version.
- unknown_event: event name not in map (likely future or typo).

Usage:
  scripts/verify_hook_events.py <hooks.json> [--cli-version X.Y.Z]
"""

import argparse
import json
import pathlib
import re
import subprocess
import sys

# Source: research/hook-observation/hook-based-runtime-observation-patterns.md
# §"Full Event Catalog (26 events, v2.1.114 baseline)"
EVENT_MIN_VERSION: dict[str, str] = {
    "SessionStart": "2.0.0",
    "SessionEnd": "2.0.0",
    "UserPromptSubmit": "2.0.0",
    "Stop": "2.0.0",
    "StopFailure": "2.1.78",
    "PreToolUse": "2.0.0",
    "PostToolUse": "2.0.0",
    "PostToolUseFailure": "2.1.76",
    "PermissionRequest": "2.0.0",
    "PermissionDenied": "2.1.89",
    "SubagentStart": "2.0.0",
    "SubagentStop": "2.0.0",
    "TaskCreated": "2.1.84",
    "TaskCompleted": "2.0.0",
    "TeammateIdle": "2.0.0",
    "ConfigChange": "2.0.0",
    "CwdChanged": "2.1.83",
    "FileChanged": "2.1.83",
    "InstructionsLoaded": "2.0.0",
    "PreCompact": "2.1.76",
    "PostCompact": "2.1.76",
    "Elicitation": "2.1.76",
    "ElicitationResult": "2.1.76",
    "Notification": "2.0.0",
    "WorktreeCreate": "2.0.0",
    "WorktreeRemove": "2.0.0",
}


def parse_semver(s: str) -> tuple[int, int, int]:
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", s.strip())
    if not m:
        raise ValueError(f"invalid semver: {s!r}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def detect_cli_version() -> str | None:
    try:
        out = subprocess.check_output(["claude", "--version"], text=True, stderr=subprocess.DEVNULL, timeout=5)
    except (FileNotFoundError, subprocess.SubprocessError):
        return None
    m = re.search(r"\b(\d+\.\d+\.\d+)\b", out)
    return m.group(1) if m else None


def verify(hooks_path: pathlib.Path, cli_version: str | None) -> list[dict]:
    data = json.loads(hooks_path.read_text(encoding="utf-8"))
    results: list[dict] = []
    cli_tuple = parse_semver(cli_version) if cli_version else None

    hooks_section = data.get("hooks", data) if isinstance(data, dict) else {}
    for event_name, entries in (hooks_section or {}).items():
        entry = {"event": event_name, "status": "ok", "details": ""}
        min_v = EVENT_MIN_VERSION.get(event_name)
        if min_v is None:
            entry["status"] = "unknown_event"
            entry["details"] = f"event {event_name!r} not in 26-event catalog — verify against installed CLI"
        elif cli_tuple is not None and cli_tuple < parse_semver(min_v):
            entry["status"] = "version_too_old"
            entry["details"] = f"requires CLI >= {min_v}, installed {cli_version}"
        else:
            entry["details"] = f"min CLI {min_v}"
        results.append(entry)

    return results


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("hooks_json", type=pathlib.Path)
    p.add_argument("--cli-version", default=None, help="Override detected CLI version")
    args = p.parse_args()

    if not args.hooks_json.is_file():
        print(f"error: {args.hooks_json}: not a file", file=sys.stderr)
        return 1

    cli_version = args.cli_version or detect_cli_version()
    results = verify(args.hooks_json, cli_version)
    print(json.dumps({"cli_version": cli_version, "events": results}, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
