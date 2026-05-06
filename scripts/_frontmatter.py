#!/usr/bin/env python3
"""Shared frontmatter primitives extracted from validate_schema.py.

Provides DATE_RE, DESCRIPTION_MIN_LEN, StrictStringsLoader,
parse_frontmatter, validate_date, _validate_description.
Does NOT import REPO_ROOT — primitives receive path as argument.
"""

from __future__ import annotations

import re
from typing import Any

import yaml

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DESCRIPTION_MIN_LEN = 20  # chars after strip — catches empty block scalars


class StrictStringsLoader(yaml.SafeLoader):
    """SafeLoader that keeps timestamp/bool scalars as raw strings.

    Prevents PyYAML coercing 2026-01-01 to datetime.date or true/yes to bool,
    which would break validate_date (expects str) and description checks.
    Override is on the subclass only — global SafeLoader stays unchanged.
    """


def _construct_scalar_string(loader: yaml.Loader, node: yaml.Node) -> str:
    return loader.construct_scalar(node)


StrictStringsLoader.add_constructor("tag:yaml.org,2002:timestamp", _construct_scalar_string)
StrictStringsLoader.add_constructor("tag:yaml.org,2002:bool", _construct_scalar_string)


def parse_frontmatter(path: Any) -> dict[str, Any] | None:
    """Extract YAML frontmatter as a dict, or None on any parse failure.

    Returns {} for empty-but-delimited frontmatter so validators can emit
    'missing required field' rather than 'missing YAML frontmatter'.
    """
    try:
        text = path.read_text(encoding="utf-8-sig")  # strips BOM if present
    except Exception:
        return None

    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None

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


def validate_date(value: Any, path: Any, field: str) -> list[str]:
    """Validate strict YYYY-MM-DD format and real calendar date.

    Non-string input emits a type-error message instead of crashing on regex.
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


def _validate_description(fm: dict[str, Any], path: Any) -> list[str]:
    """Validate description field: must be str >= DESCRIPTION_MIN_LEN after strip.

    Short-circuits on value is None so schema owns the null/missing case and
    we don't double-report. Catches empty block scalars (description: >).
    """
    if "description" not in fm:
        return [f"{path}: missing required field 'description'"]
    value = fm["description"]
    if value is None:
        return []  # schema owns null/missing; don't double-report
    if not isinstance(value, str):
        return [f"{path}: 'description' expected str, got {type(value).__name__}"]
    if len(value.strip()) < DESCRIPTION_MIN_LEN:
        return [
            f"{path}: 'description' is too short ({len(value.strip())} chars "
            f"after strip; min {DESCRIPTION_MIN_LEN}) — likely an empty block "
            f"scalar"
        ]
    return []
