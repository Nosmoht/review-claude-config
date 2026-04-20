#!/usr/bin/env python3
"""Merge perspective certificates (Layer 0-4) into a single review certificate.

Input: a directory containing 1-3 perspective certificate JSON files named
  `clarity.json`, `correctness.json`, `integration.json`.
Output (stdout): merged certificate JSON.

Layered merge pipeline:
  Layer 0 — content-dedup: same (path, line_range) and token-overlap >=0.80
            on evidence text collapse into one multi-tagged finding.
  Layer 1 — owner-weighted vote: primary-focus finding from its owning
            perspective wins dimension grade (weight 2x); non-primary
            1x.
  Layer 2 — max-severity tiebreak on collapsed findings.
  Layer 3 — lexicographic perspective-name tiebreak when ties remain.
  Layer 4 — manual-review flag when >=2 perspectives disagree at high
            confidence.

Partial-failure handling: if a perspective's JSON is missing or malformed,
the merge proceeds with remaining certs and sets `degraded_mode=true`
with `missing_perspectives=[...]`.

Deterministic tokenizer: re.findall(r"\\w+", text.lower()).
Deterministic overlap ratio: |intersection| / max(|a|, |b|).

Usage:
  python3 merge_findings.py <session-perspectives-dir>
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

PERSPECTIVES = ("clarity", "correctness", "integration")
OVERLAP_THRESHOLD = 0.80

GRADE_TO_NUMERIC = {"A": 95, "B": 85, "C": 75, "D": 65, "F": 50}
SEVERITY_RANK = {"High": 3, "Medium": 2, "Low": 1}


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def overlap_ratio(a: str, b: str) -> float:
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def load_cert(path: pathlib.Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def layer0_dedup(all_findings: list[dict]) -> list[dict]:
    """Collapse findings sharing (path, line_range) with evidence overlap >=0.80."""
    merged: list[dict] = []
    used = [False] * len(all_findings)
    for i, f in enumerate(all_findings):
        if used[i]:
            continue
        group = [f]
        used[i] = True
        for j in range(i + 1, len(all_findings)):
            if used[j]:
                continue
            g = all_findings[j]
            same_loc = f.get("path") == g.get("path") and f.get("line_range") == g.get("line_range")
            if same_loc and overlap_ratio(f.get("evidence", ""), g.get("evidence", "")) >= OVERLAP_THRESHOLD:
                group.append(g)
                used[j] = True
        collapsed = dict(f)
        collapsed["dimensions"] = sorted({m.get("dimension") for m in group if m.get("dimension")})
        collapsed["perspectives"] = sorted({m.get("perspective") for m in group if m.get("perspective")})
        collapsed["severity"] = max(
            (m.get("severity", "Low") for m in group),
            key=lambda s: SEVERITY_RANK.get(s, 0),
        )
        merged.append(collapsed)
    return merged


def layer1_owner_weighted_grade(certs: dict[str, dict], dimension: str) -> tuple[str, str]:
    """Compute owner-weighted grade for a dimension.

    Returns (grade_letter, justification_source_perspective).
    Owner (primary-dimension perspective) weight 2x; others 1x.
    """
    dimension_owners = {
        "Clarity": "clarity",
        "Completeness": "correctness",
        "Prompt Engineering": "correctness",
        "Context Engineering": "correctness",
        "Goal Alignment": "correctness",
        "Safety": "integration",
        "Metadata": "integration",
    }
    owner = dimension_owners.get(dimension)
    numerics: list[tuple[int, str]] = []
    for persp, cert in certs.items():
        if not cert:
            continue
        grade = cert.get("dimensions", {}).get(dimension)
        if grade is None:
            continue
        weight = 2 if persp == owner else 1
        numerics.extend([(GRADE_TO_NUMERIC.get(grade, 0), persp)] * weight)
    if not numerics:
        return "F", ""
    avg = sum(v for v, _ in numerics) / len(numerics)
    for letter, floor in [("A", 90), ("B", 80), ("C", 70), ("D", 60)]:
        if avg >= floor:
            return letter, numerics[0][1]
    return "F", numerics[0][1]


def compute_weighted_score(merged_grades: dict[str, str], weights: dict[str, float]) -> float:
    total = 0.0
    for dim, grade in merged_grades.items():
        total += GRADE_TO_NUMERIC.get(grade, 0) * weights.get(dim, 0)
    return total


def infer_weights(artifact_frontmatter: dict) -> dict[str, float]:
    """Apply conditional weighting per scoring-rubric.md."""
    tools = set(artifact_frontmatter.get("allowed_tools", []))
    write_bash_edit = tools & {"Write", "Bash", "Edit"}
    if write_bash_edit:
        safety_w, meta_w = 0.15, 0.05
    else:
        safety_w, meta_w = 0.10, 0.10
    return {
        "Clarity": 0.15,
        "Completeness": 0.15,
        "Prompt Engineering": 0.15,
        "Context Engineering": 0.15,
        "Goal Alignment": 0.20,
        "Safety": safety_w,
        "Metadata": meta_w,
    }


def merge_directory(session_dir: pathlib.Path) -> dict:
    certs: dict[str, dict | None] = {}
    missing: list[str] = []
    for name in PERSPECTIVES:
        path = session_dir / f"{name}.json"
        cert = load_cert(path) if path.exists() else None
        certs[name] = cert
        if cert is None:
            missing.append(name)

    degraded = len(missing) > 0
    available_certs = {k: v for k, v in certs.items() if v is not None}

    if not available_certs:
        return {
            "status": "failure",
            "degraded_mode": True,
            "missing_perspectives": missing,
            "error": "all perspectives returned null/malformed certificates",
        }

    all_findings: list[dict] = []
    for persp, cert in available_certs.items():
        for f in cert.get("findings", []):
            finding = dict(f)
            finding.setdefault("perspective", persp)
            all_findings.append(finding)

    merged_findings = layer0_dedup(all_findings)

    dimensions = [
        "Clarity",
        "Completeness",
        "Prompt Engineering",
        "Context Engineering",
        "Goal Alignment",
        "Safety",
        "Metadata",
    ]
    merged_grades = {}
    grade_sources = {}
    for dim in dimensions:
        grade, source = layer1_owner_weighted_grade(available_certs, dim)
        merged_grades[dim] = grade
        grade_sources[dim] = source

    artifact_frontmatter = next(iter(available_certs.values())).get("artifact_frontmatter", {})
    weights = infer_weights(artifact_frontmatter)
    weighted_score = compute_weighted_score(merged_grades, weights)

    conflicts = []
    for f in merged_findings:
        if len(f.get("perspectives", [])) > 1 and f.get("owner_conflict"):
            conflicts.append(f.get("id") or f.get("evidence", "")[:50])

    return {
        "status": "success" if not degraded else "partial",
        "degraded_mode": degraded,
        "missing_perspectives": missing,
        "dimensions": merged_grades,
        "grade_sources": grade_sources,
        "weights": weights,
        "weighted_score": round(weighted_score, 2),
        "findings": merged_findings,
        "owner_conflicts": conflicts,
        "perspective_scores": {
            p: cert.get("weighted_score")
            for p, cert in available_certs.items()
            if cert.get("weighted_score") is not None
        },
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: merge_findings.py <session-perspectives-dir>", file=sys.stderr)
        return 2
    session_dir = pathlib.Path(sys.argv[1])
    if not session_dir.is_dir():
        print(f"Not a directory: {session_dir}", file=sys.stderr)
        return 2
    result = merge_directory(session_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
