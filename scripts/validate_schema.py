#!/usr/bin/env python3
"""Programmatic schema validator for frontmatter and hooks.json.

Validates:
- Reference files: name, description, last_refreshed (strict ISO 8601)
- Skill files: name, description
- Research files: last_refreshed (strict ISO 8601)
- Domain cache files: domain, last_refreshed (strict ISO 8601)
- hooks.json: JSON syntax, script path references

Exit codes: 0 = all valid, 1 = validation errors found.
"""

import json
import pathlib
import re
import sys

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def parse_frontmatter(path: pathlib.Path) -> dict[str, str] | None:
    """Extract YAML frontmatter as a flat key-value dict (strings only)."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None

    if not text.startswith("---"):
        return None

    lines = text.split("\n")
    if lines[0].strip() != "---":
        return None

    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        # Handle simple key: value (skip multi-line/block scalars)
        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value == ">" or value == "|":
                continue  # block scalar — skip
            if value:
                fields[key] = value
    return fields


def validate_date(value: str, path: pathlib.Path, field: str) -> list[str]:
    """Validate strict YYYY-MM-DD format."""
    if not DATE_RE.match(value):
        return [f"{path}: {field} '{value}' is not strict YYYY-MM-DD"]
    # Also check it's a real date
    try:
        import datetime

        datetime.date.fromisoformat(value)
    except ValueError:
        return [f"{path}: {field} '{value}' is not a valid date"]
    return []


def validate_reference_files() -> list[str]:
    """Validate skills/review-claude-config/references/*.md files."""
    errors = []
    refs_dir = REPO_ROOT / "skills" / "review-claude-config" / "references"
    if not refs_dir.exists():
        return [f"{refs_dir}: directory not found"]

    for path in sorted(refs_dir.glob("*.md")):
        fm = parse_frontmatter(path)
        if fm is None:
            errors.append(f"{path}: missing YAML frontmatter")
            continue
        for field in ("name", "description", "last_refreshed"):
            if field not in fm:
                errors.append(f"{path}: missing required field '{field}'")
        if "last_refreshed" in fm:
            errors.extend(validate_date(fm["last_refreshed"], path, "last_refreshed"))
    return errors


def validate_skill_files() -> list[str]:
    """Validate skills/*/SKILL.md files."""
    errors = []
    for path in sorted(REPO_ROOT.glob("skills/*/SKILL.md")):
        fm = parse_frontmatter(path)
        if fm is None:
            errors.append(f"{path}: missing YAML frontmatter")
            continue
        for field in ("name", "description"):
            if field not in fm:
                # description may be a block scalar (>) — check raw text
                if field == "description":
                    text = path.read_text(encoding="utf-8")
                    if "description:" in text:
                        continue
                errors.append(f"{path}: missing required field '{field}'")
    return errors


def validate_research_files() -> list[str]:
    """Validate research/**/*.md files."""
    errors = []
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
        elif "last_refreshed" in fm:
            errors.extend(validate_date(fm["last_refreshed"], path, "last_refreshed"))
    return errors


def validate_domain_cache_files() -> list[str]:
    """Validate skills/review-claude-config/references/domain-cache/*.md files."""
    errors = []
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
        elif "last_refreshed" in fm:
            errors.extend(validate_date(fm["last_refreshed"], path, "last_refreshed"))
    return errors


def validate_hooks_json() -> list[str]:
    """Validate hooks/hooks.json syntax and script path references."""
    errors = []
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


if __name__ == "__main__":
    sys.exit(main())
