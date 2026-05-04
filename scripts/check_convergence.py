#!/usr/bin/env python3
"""Programmatic convergence checker for /review-skill Phase 5.

Compares two ``merge_findings.py`` outputs ("run1" and "run2") and reports
whether the two runs converged according to the contract in CLAUDE.md:126.

Constants are loaded from
skills/review-claude-config/references/convergence-rules.yaml
(override via CONVERGENCE_RULES_YAML_PATH env var).

Exit codes:
  0 — converged (gate passes)
  1 — not converged (escalate per /review-skill ESC-5)
  2 — usage error or input parse failure

Usage:
  check_convergence.py <run1.json> <run2.json> [--max-variance N]
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import pathlib
import sys

import yaml

_DEFAULT_PATH = (
    pathlib.Path(__file__).resolve().parent.parent / "skills/review-claude-config/references/convergence-rules.yaml"
)


def _yaml_path() -> str:
    return os.environ.get("CONVERGENCE_RULES_YAML_PATH", str(_DEFAULT_PATH))


@functools.lru_cache(maxsize=4)
def _load_cached(path: str) -> dict:
    p = pathlib.Path(path)
    if not p.exists():
        raise RuntimeError(
            f"convergence-rules.yaml missing at {p} — see "
            f"skills/review-claude-config/references/schemas/convergence-rules.schema.json"
        )
    with p.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        raise RuntimeError(f"convergence-rules.yaml at {p} is empty or invalid YAML")
    return data


def _load() -> dict:
    return _load_cached(_yaml_path())


_data = _load()

# Eager-resolve at module import with type coercion — preserves test-suite imports.
DETERMINISTIC_SUBSET: frozenset[str] = frozenset(_data["DETERMINISTIC_SUBSET"])
GRADE_LETTERS: tuple[str, ...] = tuple(_data["GRADE_LETTERS"])
GRADE_RANK: dict[str, int] = {g: i for i, g in enumerate(GRADE_LETTERS)}
DEFAULT_MAX_VARIANCE: int = int(_data["DEFAULT_MAX_VARIANCE"])


def _deterministic_hm_finding_ids(merged: dict) -> set[str]:
    """Extract finding ids in the deterministic subset at High/Medium severity.

    Identity falls back to ``checklist_item::dimension`` when the merged
    finding lacks a stable ``id`` (defensive — current merge_findings.py
    populates ``id`` via the canonicaliser, but legacy or partial outputs
    may not).
    """
    out: set[str] = set()
    for f in merged.get("findings") or []:
        item = f.get("checklist_item") or ""
        if item not in DETERMINISTIC_SUBSET:
            continue
        sev = (f.get("severity") or "").strip().lower()
        if sev not in ("high", "medium"):
            continue
        fid = f.get("id") or f"{item}::{f.get('dimension') or ''}"
        out.add(fid)
    return out


def _grade_distance(g1: str | None, g2: str | None) -> int:
    """Letter distance between two grades. Unknown grades return a large
    sentinel so the caller never silently treats a typo as 'converged'.
    """
    if g1 is None or g2 is None:
        # Caller is responsible for distinguishing null cases via the
        # null-dimension tracker; this function only operates on present
        # values. Returning a large value here is a safety net.
        return 99
    if g1 not in GRADE_RANK or g2 not in GRADE_RANK:
        return 99
    return abs(GRADE_RANK[g1] - GRADE_RANK[g2])


def check_convergence(run1: dict, run2: dict, max_variance: int = DEFAULT_MAX_VARIANCE) -> dict:
    """Compare two merged outputs and produce a structured convergence report."""
    det1 = _deterministic_hm_finding_ids(run1)
    det2 = _deterministic_hm_finding_ids(run2)
    added = sorted(det2 - det1)
    removed = sorted(det1 - det2)
    deterministic_match = not added and not removed

    dims1 = run1.get("dimensions") or {}
    dims2 = run2.get("dimensions") or {}

    grade_variance: dict[str, int] = {}
    null_dimensions_added: list[str] = []

    for dim in sorted(set(dims1.keys()) | set(dims2.keys())):
        g1 = dims1.get(dim)
        g2 = dims2.get(dim)
        if g1 is not None and g2 is None:
            # Asymmetric rule: losing a dimension is a convergence regression.
            null_dimensions_added.append(dim)
            continue
        if g1 is not None and g2 is not None:
            grade_variance[dim] = _grade_distance(g1, g2)
        # g1 None and g2 None: skip
        # g1 None and g2 not None: information gained, not a regression — skip

    max_observed_variance = max(grade_variance.values()) if grade_variance else 0
    grade_variance_ok = max_observed_variance <= max_variance
    null_ok = not null_dimensions_added

    converged = deterministic_match and grade_variance_ok and null_ok

    return {
        "converged": converged,
        "deterministic_match": deterministic_match,
        "deterministic_added_finding_ids": added,
        "deterministic_removed_finding_ids": removed,
        "grade_variance": grade_variance,
        "max_grade_variance": max_observed_variance,
        "max_grade_variance_allowed": max_variance,
        "null_dimensions_added": null_dimensions_added,
    }


def _load_json(path: pathlib.Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise SystemExit(f"check_convergence: cannot read {path}: {e}")
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as e:
        raise SystemExit(f"check_convergence: invalid JSON in {path}: {e}")
    if not isinstance(loaded, dict):
        raise SystemExit(f"check_convergence: {path} must contain a JSON object")
    return loaded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check convergence between two /review-skill merge outputs.")
    parser.add_argument("run1", type=pathlib.Path, help="path to first merged.json")
    parser.add_argument("run2", type=pathlib.Path, help="path to second merged.json")
    parser.add_argument(
        "--max-variance",
        type=int,
        default=DEFAULT_MAX_VARIANCE,
        help="max allowed letter distance per dimension (default: 1)",
    )
    args = parser.parse_args(argv)

    if args.max_variance < 0:
        print("--max-variance must be non-negative", file=sys.stderr)
        return 2

    run1 = _load_json(args.run1)
    run2 = _load_json(args.run2)

    report = check_convergence(run1, run2, max_variance=args.max_variance)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["converged"] else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
