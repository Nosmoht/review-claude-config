#!/usr/bin/env python3
"""Programmatic schema validator for frontmatter and hooks.json.
Validates reference, skill, agent, research, domain-cache, hooks.json,
hook config, and YAML reference files. Exit 0=valid, 1=errors found.
"""

from __future__ import annotations

import functools
import json
import pathlib
import re
import sys
from typing import Any, Callable

import jsonschema
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _frontmatter import (  # noqa: E402
    DATE_RE,  # noqa: F401
    DESCRIPTION_MIN_LEN,  # noqa: F401
    StrictStringsLoader,  # noqa: F401
    _validate_description,
    parse_frontmatter,
    validate_date,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCHEMAS = REPO_ROOT / "skills" / "review-claude-config" / "references" / "schemas"
_AGENTS = REPO_ROOT / "agents"
_RESEARCH = REPO_ROOT / "research"
_DC_DIR = REPO_ROOT / "skills" / "review-claude-config" / "references" / "domain-cache"
_SKILL_GLOBS = ("skills/*/SKILL.md", ".claude/skills/*/SKILL.md")


@functools.lru_cache(maxsize=16)
def _load_schema_cached(schema_path_str: str) -> dict:
    schema = json.loads(pathlib.Path(schema_path_str).read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


def _validate_against_schema(data: dict, schema_path: pathlib.Path) -> list[str]:
    schema = _load_schema_cached(str(schema_path))
    errors: list[str] = []
    for error in jsonschema.Draft202012Validator(schema).iter_errors(data):
        if error.validator == "required" and "'" in error.message:
            errors.append(f"missing required field '{error.message.split(chr(39))[1]}'")
        else:
            errors.append(f"{error.json_path or '$'}: {error.message}")
    return errors


def _validate_files(
    paths_thunk: Callable[[], list[pathlib.Path]],
    schema_name: str,
    extra_checks: tuple[Callable[[dict, pathlib.Path], list[str]], ...] = (),
) -> list[str]:
    """Generic frontmatter loop: parse → schema-validate → auto-wire → extra."""
    schema_path = _SCHEMAS / f"{schema_name}.schema.json"
    schema = _load_schema_cached(str(schema_path))
    auto_desc = "description" in schema.get("required", [])
    auto_date = "last_refreshed" in schema.get("required", [])
    errors: list[str] = []
    for path in paths_thunk():
        fm = parse_frontmatter(path)
        if fm is None:
            errors.append(f"{path}: missing YAML frontmatter")
            continue
        for e in _validate_against_schema(fm, schema_path):
            errors.append(f"{path}: {e}")
        if auto_desc:
            errors.extend(_validate_description(fm, path))
        if auto_date and "last_refreshed" in fm:
            errors.extend(validate_date(fm["last_refreshed"], path, "last_refreshed"))
        for check in extra_checks:
            errors.extend(check(fm, path))
    return errors


SAMP_REGEX = re.compile(r"\b(temperature|top_p|top_k)\s*[:=]", re.IGNORECASE)


def _samp_check(fm: dict[str, Any], path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8-sig")
    except Exception:
        return errors
    fme = text.find("---", 3)
    body = text[fme + 3 :] if fme != -1 else text
    fmt = text[3:fme] if fme != -1 else ""
    if SAMP_REGEX.search(fmt):
        errors.append(
            f"{path}: SAMP-2 FAIL — frontmatter contains removed Opus 4.7 "
            "sampling param (temperature/top_p/top_k) — runtime 400-error"
        )
    if SAMP_REGEX.search(body):
        errors.append(
            f"{path}: SAMP-1 WARN — body contains sampling-param reference "
            "(temperature/top_p/top_k); verify it is quoted example text"
        )
    return errors


def _dc_paths() -> list[pathlib.Path]:
    dc_dir = REPO_ROOT / "skills" / "review-claude-config" / "references" / "domain-cache"
    return [p for p in sorted(dc_dir.glob("*.md")) if p.name != "INDEX.md"] if dc_dir.exists() else []


def validate_reference_files() -> list[str]:
    paths = sorted(REPO_ROOT.glob("skills/*/references/*.md"))
    if not paths:
        return ["No reference files found under skills/*/references/"]
    return _validate_files(lambda: paths, "ref-file")


def validate_skill_files() -> list[str]:
    return _validate_files(lambda: sorted(p for g in _SKILL_GLOBS for p in REPO_ROOT.glob(g)), "skill")


def validate_agent_files() -> list[str]:
    agents = REPO_ROOT / "agents"
    return _validate_files(lambda: sorted(agents.glob("*.md")) if agents.exists() else [], "agent", (_samp_check,))


def validate_research_files() -> list[str]:
    research = REPO_ROOT / "research"
    return _validate_files(lambda: sorted(research.rglob("*.md")) if research.exists() else [], "research")


def validate_domain_cache_files() -> list[str]:
    return _validate_files(_dc_paths, "domain-cache")


def validate_hook_config_files() -> list[str]:
    """Validate hooks/*.json (excluding hooks.json) against their schemas."""
    errors: list[str] = []
    hooks_dir = REPO_ROOT / "hooks"
    schemas_dir = REPO_ROOT / "skills" / "review-claude-config" / "references" / "schemas"
    config_files = sorted(p for p in hooks_dir.glob("*.json") if p.name != "hooks.json")
    if not config_files:
        return []
    for config_path in config_files:
        schema_path = schemas_dir / f"{config_path.stem}.schema.json"
        if not schema_path.exists():
            errors.append(f"{config_path}: no schema found at {schema_path}")
            continue
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{config_path}: invalid JSON — {e}")
            continue
        for error in jsonschema.Draft202012Validator(schema).iter_errors(data):
            errors.append(f"{config_path}: {error.message} at {error.json_path}")
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


YAML_REF_ALLOWLIST = ("audit-triggers.yaml", "convergence-rules.yaml", "escalation-rules.yaml")


def validate_yaml_reference_files() -> list[str]:
    """Validate maintainer-edited YAML references against schemas + cross-YAML invariants.

    Distinct from merge-policy.yaml (auto-generated; validated separately by
    scripts/regenerate_merge_policy.py). Allowlist-based to prevent accidental
    inclusion of new yamls without explicit registration.

    Cross-YAML invariant: convergence-rules.yaml::DETERMINISTIC_SUBSET MUST equal
    merge-policy.yaml::binary_item_ids | narrative_parent_ids. Detects drift on
    every make validate.
    """
    errors: list[str] = []
    refs_dir = REPO_ROOT / "skills" / "review-claude-config" / "references"
    schemas_dir = refs_dir / "schemas"
    yaml_data: dict[str, dict] = {}
    for stem_yaml in YAML_REF_ALLOWLIST:
        yaml_path = refs_dir / stem_yaml
        if not yaml_path.exists():
            errors.append(f"{yaml_path}: file not found (registered in YAML_REF_ALLOWLIST)")
            continue
        schema_path = schemas_dir / f"{yaml_path.stem}.schema.json"
        if not schema_path.exists():
            errors.append(f"{yaml_path}: no schema found at {schema_path}")
            continue
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            errors.append(f"{yaml_path}: invalid — {e}")
            continue
        if data is None:
            errors.append(f"{yaml_path}: empty or invalid YAML")
            continue
        for error in jsonschema.Draft202012Validator(schema).iter_errors(data):
            errors.append(f"{yaml_path}: {error.message} at {error.json_path}")
        yaml_data[yaml_path.stem] = data
    conv = yaml_data.get("convergence-rules")
    if conv is not None and "DETERMINISTIC_SUBSET" in conv:
        merge_policy_path = REPO_ROOT / "skills" / "review-skill" / "references" / "merge-policy.yaml"
        if merge_policy_path.exists():
            try:
                mp = yaml.safe_load(merge_policy_path.read_text(encoding="utf-8"))
                expected = frozenset(mp.get("binary_item_ids", [])) | frozenset(mp.get("narrative_parent_ids", []))
                actual = frozenset(conv["DETERMINISTIC_SUBSET"])
                if actual != expected:
                    missing = sorted(expected - actual)
                    extra = sorted(actual - expected)
                    errors.append(
                        f"convergence-rules.yaml: DETERMINISTIC_SUBSET drift vs merge-policy.yaml — "
                        f"missing={missing!r}, extra={extra!r}"
                    )
            except yaml.YAMLError as e:
                errors.append(f"merge-policy.yaml: cannot read for drift check — {e}")
    return errors


def main() -> int:
    all_errors: list[str] = []
    sections: list[tuple[str, list[str]]] = [
        ("Reference files", validate_reference_files()),
        ("Skill files", validate_skill_files()),
        ("Agent files", validate_agent_files()),
        ("Research files", validate_research_files()),
        ("Domain cache files", validate_domain_cache_files()),
        ("hooks.json", validate_hooks_json()),
        ("Hook config files", validate_hook_config_files()),
        ("YAML reference files", validate_yaml_reference_files()),
    ]
    for label, errors in sections:
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
