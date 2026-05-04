#!/usr/bin/env python3
"""Sync `.claude-plugin/marketplace.json` to `.claude-plugin/plugin.json#version`.

After release-please-action bumps `plugin.json.version`, this script propagates
that version to two fields in `marketplace.json`:

- `plugins[0].version` (must equal `plugin.json.version`)
- `plugins[0].source.ref` (must equal `"v" + plugin.json.version`)

Format-preserving: the script uses targeted regex replacements instead of full
JSON re-serialization, so the file's hand-formatted style (inline `owner` and
`tags` arrays) is kept intact.

`metadata.version` (the marketplace-catalog version) is intentionally not
touched. It is a separate concept from the plugin version.

Idempotent: a second run on already-synced state produces no diff and exits 0.

Failure modes — all return non-zero with a diagnostic:
  - either input file missing
  - either regex matches zero or multiple times (structural drift)
  - in-memory new text fails strict JSON parse
  - on-disk re-read after write fails the version+ref invariant
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PLUGIN = Path(".claude-plugin/plugin.json")
MARKETPLACE = Path(".claude-plugin/marketplace.json")

VERSION_PATTERN = r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.\-]+)?"


def main() -> int:
    if not PLUGIN.exists() or not MARKETPLACE.exists():
        print(
            f"sync-marketplace-ref: required file missing "
            f"(plugin={PLUGIN.exists()}, marketplace={MARKETPLACE.exists()})",
            file=sys.stderr,
        )
        return 1

    version = json.loads(PLUGIN.read_text(encoding="utf-8"))["version"]
    expected_ref = f"v{version}"

    text = MARKETPLACE.read_text(encoding="utf-8")

    new_text, n_ref = re.subn(
        rf'("source"\s*:\s*\{{[^}}]*?"ref"\s*:\s*)"v{VERSION_PATTERN}"',
        rf'\1"{expected_ref}"',
        text,
        count=1,
    )

    plugins_match = re.search(r'"plugins"\s*:\s*\[', new_text)
    if plugins_match is None:
        print(
            "sync-marketplace-ref: cannot locate 'plugins' array in marketplace.json",
            file=sys.stderr,
        )
        return 1

    head = new_text[: plugins_match.end()]
    tail = new_text[plugins_match.end() :]
    tail_new, n_version = re.subn(
        rf'("version"\s*:\s*)"{VERSION_PATTERN}"',
        rf'\1"{version}"',
        tail,
        count=1,
    )
    new_text = head + tail_new

    if n_ref != 1 or n_version != 1:
        print(
            f"sync-marketplace-ref: structural drift — "
            f"ref-substitutions={n_ref} (expected 1), "
            f"version-substitutions={n_version} (expected 1). "
            f"marketplace.json shape may have changed.",
            file=sys.stderr,
        )
        return 1

    try:
        json.loads(new_text)
    except json.JSONDecodeError as exc:
        print(
            f"sync-marketplace-ref: produced invalid JSON: {exc}",
            file=sys.stderr,
        )
        return 1

    if new_text == text:
        print(f"sync-marketplace-ref: marketplace.json already in sync (version={version}, ref={expected_ref})")
        return 0

    MARKETPLACE.write_text(new_text, encoding="utf-8", newline="\n")

    on_disk = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    actual_version = on_disk["plugins"][0]["version"]
    actual_ref = on_disk["plugins"][0]["source"]["ref"]
    if actual_version != version or actual_ref != expected_ref:
        print(
            f"sync-marketplace-ref: post-write verification failed "
            f"(version={actual_version} expected={version}, "
            f"ref={actual_ref} expected={expected_ref})",
            file=sys.stderr,
        )
        return 1

    print(f"sync-marketplace-ref: bumped to version={version}, ref={expected_ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
