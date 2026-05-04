#!/usr/bin/env python3
"""Preflight detector for non-deterministic LLM-binary rubric items.

Items covered (regex preflight only — no PASS/FAIL verdict):
WS-7, WS-8, GA-Y, GA-Z, GA-S, CE-CP, SP-IO, COMP-Sel.

Trigger patterns are read from
skills/review-claude-config/references/audit-triggers.yaml
(override via AUDIT_TRIGGERS_YAML_PATH env var).

Usage:
    python3 scripts/audit_preflight.py [--show-paths]
"""

from __future__ import annotations

import functools
import os
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from rubric_binary_evaluator import REPO_ROOT  # noqa: E402

_DEFAULT_PATH = (
    pathlib.Path(__file__).resolve().parent.parent / "skills/review-claude-config/references/audit-triggers.yaml"
)


def _yaml_path() -> str:
    return os.environ.get("AUDIT_TRIGGERS_YAML_PATH", str(_DEFAULT_PATH))


@functools.lru_cache(maxsize=4)
def _load_cached(path: str) -> dict:
    p = pathlib.Path(path)
    if not p.exists():
        raise RuntimeError(
            f"audit-triggers.yaml missing at {p} — see "
            f"skills/review-claude-config/references/schemas/audit-triggers.schema.json"
        )
    with p.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        raise RuntimeError(f"audit-triggers.yaml at {p} is empty or invalid YAML")
    return data


def _load() -> dict:
    return _load_cached(_yaml_path())


def _flags(flag_names: list[str]) -> int:
    """Convert list of flag name strings to re module flag bitmask."""
    result = 0
    for name in flag_names:
        result |= getattr(re, name, 0)
    return result


_data = _load()

# Eager-resolve at module import — preserves test-suite constant imports.
TRIGGERS: dict[str, re.Pattern[str]] = {
    t["id"]: re.compile(t["pattern"], _flags(t["flags"])) for t in _data["triggers"]
}
WS_8_REF_LOAD = re.compile(
    _data["count_triggers"][0]["pattern"],
    _flags(_data["count_triggers"][0].get("flags", [])),
)
_NOTES = {t["id"]: t["notes"] for t in (_data["triggers"] + _data["count_triggers"])}
_ITEM_ORDER: list[str] = list(_data["item_order"])
_GA_S_PREFIXES: tuple[str, ...] = tuple(_data["count_triggers"][1]["name_prefix_match"])


def line_count(body: str) -> int:
    return body.count("\n") + 1


def main(show_paths: bool = False) -> int:
    skills_root = REPO_ROOT / "skills"
    paths = sorted(skills_root.glob("*/SKILL.md"))
    print(f"# Preflight Audit — {len(paths)} skills\n")
    print("Triggers detect *candidate* skills needing LLM-binary verdict.")
    print("A trigger hit does NOT mean the skill fails — only that an LLM")
    print("reviewer must judge the verdict per the rubric iff-predicate.\n")

    print("## Per-Item Trigger Hits\n")
    print("| Item | Skills with trigger | Notes |")
    print("|------|---------------------|-------|")

    hits: dict[str, list[str]] = {item: [] for item in TRIGGERS}
    hits["WS-8"] = []
    hits["GA-S"] = []

    for path in paths:
        body = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(REPO_ROOT))

        for item, pattern in TRIGGERS.items():
            if pattern.search(body):
                if item == "CE-CP" and line_count(body) < 150:
                    continue  # NA exemption
                hits[item].append(rel)

        # WS-8: >=2 reference loads in close proximity
        ref_matches = list(WS_8_REF_LOAD.finditer(body))
        if len(ref_matches) >= 2:
            hits["WS-8"].append(rel)

        # GA-S: review-class skills (review/audit/classify/evaluate)
        name_l = path.parent.name.lower()
        if any(name_l.startswith(verb) for verb in _GA_S_PREFIXES):
            hits["GA-S"].append(rel)

    for item in _ITEM_ORDER:
        count = len(hits[item])
        flag = " ⚠️" if count > 0 else ""
        print(f"| {item}{flag} | {count} | {_NOTES[item]} |")

    if show_paths:
        print("\n## Candidate Skills per Item\n")
        for item in _ITEM_ORDER:
            if hits[item]:
                print(f"\n### {item} ({len(hits[item])} candidates)\n")
                for p in hits[item]:
                    print(f"- `{p}`")

    return 0


if __name__ == "__main__":
    show = "--show-paths" in sys.argv[1:]
    sys.exit(main(show))
