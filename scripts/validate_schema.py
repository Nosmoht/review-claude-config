#!/usr/bin/env python3
"""Programmatic schema validator for frontmatter and hooks.json.

Validates:
- Reference files: name, description, last_refreshed (strict ISO 8601)
- Skill files: name, description (min 20 chars after strip)
- Research files: last_refreshed (strict ISO 8601)
- Domain cache files: domain, last_refreshed (strict ISO 8601)
- Agent files: name, description, model, tools + SAMP-1/2 sampling-param check
- hooks.json: JSON syntax, script path references

Frontmatter parsing uses PyYAML with a custom Loader (`StrictStringsLoader`)
that keeps timestamps and booleans as raw scalar strings — preserving the
strict YYYY-MM-DD format check and avoiding silent type coercion of values
like ``disable-model-invocation: true``.

Exit codes: 0 = all valid, 1 = validation errors found.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Any

import yaml

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DESCRIPTION_MIN_LEN = 20  # chars after strip — catches empty block scalars


class StrictStringsLoader(yaml.SafeLoader):
    """SafeLoader subclass that keeps timestamp and bool scalars as raw strings.

    Default ``yaml.SafeLoader`` coerces ``2026-01-01`` to ``datetime.date`` and
    ``true``/``yes``/``no`` to ``bool``. Both break this validator's downstream
    consumers (``validate_date`` expects ``str``, the description min-length
    check expects ``str``). Overriding these constructors on a subclass keeps
    the global SafeLoader intact for any other consumer.
    """


def _construct_scalar_string(loader: yaml.Loader, node: yaml.Node) -> str:
    return loader.construct_scalar(node)


StrictStringsLoader.add_constructor("tag:yaml.org,2002:timestamp", _construct_scalar_string)
StrictStringsLoader.add_constructor("tag:yaml.org,2002:bool", _construct_scalar_string)


def parse_frontmatter(path: pathlib.Path) -> dict[str, Any] | None:
    """Extract YAML frontmatter as a dict.

    Returns ``None`` when the file is missing, has no frontmatter delimiter as
    its first line, has no closing ``---``, or contains malformed YAML.
    Returns ``{}`` for an empty-but-delimited frontmatter block, preserving the
    distinction "no frontmatter" vs "empty frontmatter" so validators can emit
    the more useful "missing required field" error in the latter case.
    """
    try:
        # utf-8-sig strips a leading BOM if present
        text = path.read_text(encoding="utf-8-sig")
    except Exception:
        return None

    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None

    # Find the closing --- on its own line. Substring search would mis-slice
    # if a multi-line quoted scalar contained '---' inside it.
    end_idx: int | None = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return None  # truncated frontmatter

    block = "\n".join(lines[1:end_idx])

    try:
        loaded = yaml.load(block, Loader=StrictStringsLoader)
    except yaml.YAMLError:
        return None

    if loaded is None:
        return {}  # empty frontmatter -> empty dict, not "missing"
    if not isinstance(loaded, dict):
        return None  # frontmatter must be a mapping
    return loaded


def validate_date(value: Any, path: pathlib.Path, field: str) -> list[str]:
    """Validate strict YYYY-MM-DD format and that the date is real.

    Non-string input is reported as a type error rather than silently crashing
    on regex match — covers cases where a future field has been quoted or
    coerced to a non-string type that the StrictStringsLoader did not catch.
    """
    if not isinstance(value, str):
        return [
            f"{path}: {field} expected str, got {type(value).__name__} "
            f"({value!r}) — quote the value to keep it a string"
        ]
    if not DATE_RE.match(value):
        return [f"{path}: {field} '{value}' is not strict YYYY-MM-DD"]
    try:
        import datetime

        datetime.date.fromisoformat(value)
    except ValueError:
        return [f"{path}: {field} '{value}' is not a valid date"]
    return []


def _validate_description(fm: dict[str, Any], path: pathlib.Path) -> list[str]:
    """Common validator for the ``description`` field.

    Required, must be a string, must be at least ``DESCRIPTION_MIN_LEN`` chars
    after strip. Catches empty block scalars (``description: >`` with nothing
    underneath) which the previous hand-rolled parser silently dropped.
    """
    if "description" not in fm:
        return [f"{path}: missing required field 'description'"]
    value = fm["description"]
    if not isinstance(value, str):
        return [f"{path}: 'description' expected str, got {type(value).__name__}"]
    if len(value.strip()) < DESCRIPTION_MIN_LEN:
        return [
            f"{path}: 'description' is too short ({len(value.strip())} chars "
            f"after strip; min {DESCRIPTION_MIN_LEN}) — likely an empty block "
            f"scalar"
        ]
    return []


def validate_reference_files() -> list[str]:
    """Validate skills/*/references/*.md files."""
    errors: list[str] = []
    paths = sorted(REPO_ROOT.glob("skills/*/references/*.md"))
    if not paths:
        return ["No reference files found under skills/*/references/"]

    for path in paths:
        fm = parse_frontmatter(path)
        if fm is None:
            errors.append(f"{path}: missing YAML frontmatter")
            continue
        if "name" not in fm:
            errors.append(f"{path}: missing required field 'name'")
        errors.extend(_validate_description(fm, path))
        if "last_refreshed" not in fm:
            errors.append(f"{path}: missing required field 'last_refreshed'")
        else:
            errors.extend(validate_date(fm["last_refreshed"], path, "last_refreshed"))
    return errors


def validate_skill_files() -> list[str]:
    """Validate skills/*/SKILL.md and .claude/skills/*/SKILL.md files."""
    errors: list[str] = []
    paths = sorted(list(REPO_ROOT.glob("skills/*/SKILL.md")) + list(REPO_ROOT.glob(".claude/skills/*/SKILL.md")))
    for path in paths:
        fm = parse_frontmatter(path)
        if fm is None:
            errors.append(f"{path}: missing YAML frontmatter")
            continue
        if "name" not in fm:
            errors.append(f"{path}: missing required field 'name'")
        errors.extend(_validate_description(fm, path))
    return errors


def validate_research_files() -> list[str]:
    """Validate research/**/*.md files."""
    errors: list[str] = []
    research_dir = REPO_ROOT / "research"
    if not research_dir.exists():
        return []

    for path in sorted(research_dir.rglob("*.md")):
        fm = parse_frontmatter(path)
        if fm is None:
            errors.append(f"{path}: missing YAML frontmatter")
            continue
        if "last_refreshed" not in fm:
            errors.append(f"{path}: missing required field 'last_refreshed'")
        else:
            errors.extend(validate_date(fm["last_refreshed"], path, "last_refreshed"))
    return errors


def validate_domain_cache_files() -> list[str]:
    """Validate skills/review-claude-config/references/domain-cache/*.md files."""
    errors: list[str] = []
    cache_dir = REPO_ROOT / "skills" / "review-claude-config" / "references" / "domain-cache"
    if not cache_dir.exists():
        return []

    for path in sorted(cache_dir.glob("*.md")):
        if path.name == "INDEX.md":
            continue  # Index file has different schema
        fm = parse_frontmatter(path)
        if fm is None:
            errors.append(f"{path}: missing YAML frontmatter")
            continue
        if "domain" not in fm:
            errors.append(f"{path}: missing required field 'domain'")
        if "last_refreshed" not in fm:
            errors.append(f"{path}: missing required field 'last_refreshed'")
        else:
            errors.extend(validate_date(fm["last_refreshed"], path, "last_refreshed"))
    return errors


SAMP_REGEX = re.compile(r"\b(temperature|top_p|top_k)\s*[:=]", re.IGNORECASE)


def validate_agent_files() -> list[str]:
    """Validate agents/*.md frontmatter + SAMP-1/2 sampling-param migration.

    Required frontmatter fields: name, description, model, tools.
    SAMP-1: body contains no hardcoded sampling-param references.
    SAMP-2: frontmatter contains no removed sampling params (runtime 400-error
    on Opus 4.7).
    """
    errors: list[str] = []
    agents_dir = REPO_ROOT / "agents"
    if not agents_dir.exists():
        return []

    for path in sorted(agents_dir.glob("*.md")):
        fm = parse_frontmatter(path)
        if fm is None:
            errors.append(f"{path}: missing YAML frontmatter")
            continue
        for field in ("name", "model", "tools"):
            if field not in fm:
                errors.append(f"{path}: missing required field '{field}'")
        errors.extend(_validate_description(fm, path))

        # SAMP regex still operates on the raw frontmatter text — it inspects
        # *literal source* for migration violations, not parsed values.
        text = path.read_text(encoding="utf-8-sig")
        frontmatter_end = text.find("---", 3)
        body = text[frontmatter_end + 3 :] if frontmatter_end != -1 else text
        frontmatter_text = text[3:frontmatter_end] if frontmatter_end != -1 else ""

        # SAMP-2: frontmatter check — hard failure (Opus 4.7 400-error)
        if SAMP_REGEX.search(frontmatter_text):
            errors.append(
                f"{path}: SAMP-2 FAIL — frontmatter contains removed Opus 4.7 "
                "sampling param (temperature/top_p/top_k) — runtime 400-error"
            )
        # SAMP-1: body check — PE cap at C on match outside quoted example
        if SAMP_REGEX.search(body):
            errors.append(
                f"{path}: SAMP-1 WARN — body contains sampling-param reference "
                "(temperature/top_p/top_k); verify it is quoted example text"
            )
    return errors


def validate_hooks_json() -> list[str]:
    """Validate hooks/hooks.json syntax and script path references."""
    errors: list[str] = []
    hooks_path = REPO_ROOT / "hooks" / "hooks.json"
    if not hooks_path.exists():
        return [f"{hooks_path}: file not found"]

    try:
        data = json.loads(hooks_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{hooks_path}: invalid JSON — {e}"]

    for event, entries in data.get("hooks", {}).items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                cmd = hook.get("command", "")
                match = re.search(r"\$\{CLAUDE_PLUGIN_ROOT\}/(.+)", cmd)
                if match:
                    rel_path = match.group(1).split()[0]
                    if not (REPO_ROOT / rel_path).exists():
                        errors.append(f"{hooks_path}: {event} references '{rel_path}' which does not exist")
    return errors


def main() -> int:
    all_errors: list[str] = []

    validators = [
        ("Reference files", validate_reference_files),
        ("Skill files", validate_skill_files),
        ("Agent files", validate_agent_files),
        ("Research files", validate_research_files),
        ("Domain cache files", validate_domain_cache_files),
        ("hooks.json", validate_hooks_json),
    ]

    for label, validator in validators:
        errors = validator()
        if errors:
            print(f"\n{label}:")
            for e in errors:
                print(f"  ERROR: {e}")
            all_errors.extend(errors)
        else:
            print(f"{label}: OK")

    if all_errors:
        print(f"\n{len(all_errors)} error(s) found.")
        return 1

    print("\nAll validations passed.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
