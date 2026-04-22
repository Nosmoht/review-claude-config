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
GRADE_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4}
SEVERITY_RANK = {"High": 3, "Medium": 2, "Low": 1}

# 26 binary-verifiable rubric items owned by scripts/rubric_binary_evaluator.py.
# Perspective findings with these checklist_items are dropped before Layer 0
# dedup; merged findings for these items come from synthesize_binary_findings().
BINARY_ITEM_IDS = frozenset(
    [
        "META-1a",
        "META-2",
        "META-3a",
        "META-3b",
        "META-4",
        "CLAR-1",
        "CLAR-2",
        "CLAR-3",
        "CLAR-4",
        "CE-X",
        "COMP-X",
        "COMP-Y",
        "COMP-Z",
        "COMP-W",
        "SAMP-1",
        "SAMP-2",
        "PE-1",
        "PE-2",
        "SP-2b",
        "SP-4b",
        "IJ-1b",
        "RL-1b",
        "RL-3b",
        "RL-4b",
        "RL-9b",
        "AH-2b",
    ]
)

# Narrative parent items the rubric supersedes with -b variants. Perspective
# findings on these also drop to prevent Haiku-class agents from re-litigating
# the same surface.
NARRATIVE_PARENT_IDS = frozenset(
    [
        "AH-2",
        "SP-2",
        "SP-4",
        "IJ-1",
        "RL-1",
        "RL-3",
        "RL-4",
        "RL-9",
        "META-1",
        "META-2",
        "META-3",
    ]
)

# Item → dimension binding. Mirrors scoring-rubric.md section headings.
ITEM_DIMENSION: dict[str, str] = {
    "META-1a": "Metadata",
    "META-2": "Metadata",
    "META-3a": "Metadata",
    "META-3b": "Metadata",
    "META-4": "Metadata",
    "CLAR-1": "Clarity",
    "CLAR-2": "Clarity",
    "CLAR-3": "Clarity",
    "CLAR-4": "Clarity",
    "CE-X": "Context Engineering",
    "COMP-X": "Completeness",
    "COMP-Y": "Completeness",
    "COMP-Z": "Completeness",
    "COMP-W": "Completeness",
    "AH-2b": "Completeness",
    "SAMP-1": "Prompt Engineering",
    "SAMP-2": "Metadata",
    "PE-1": "Prompt Engineering",
    "PE-2": "Prompt Engineering",
    "SP-2b": "Safety",
    "SP-4b": "Safety",
    "IJ-1b": "Safety",
    "RL-1b": "Safety",
    "RL-3b": "Safety",
    "RL-4b": "Safety",
    "RL-9b": "Safety",
}

# Grade-boundary cap table. Each entry: FAIL on `item` caps `dimension` at
# `cap_grade` (cannot be better). Source: scoring-rubric.md grade-boundary
# clauses. Caps are monotone — never upgrade a merged grade. Multiple caps on
# the same dimension stack (strictest wins because of GRADE_ORDER check).
BINARY_CAPS: list[tuple[str, str, str]] = [
    # Clarity (CLAR-1/2/3/4 OR → Clarity ≤ C)
    ("CLAR-1", "Clarity", "C"),
    ("CLAR-2", "Clarity", "C"),
    ("CLAR-3", "Clarity", "C"),
    ("CLAR-4", "Clarity", "C"),
    # Completeness
    ("COMP-W", "Completeness", "C"),
    ("AH-2b", "Completeness", "C"),
    # Context Engineering
    ("CE-X", "Context Engineering", "C"),
    # Prompt Engineering
    ("PE-1", "Prompt Engineering", "C"),
    ("PE-2", "Prompt Engineering", "C"),
    ("SAMP-1", "Prompt Engineering", "C"),
    # Metadata — SAMP-2 is a hard F (runtime 400 error on Opus 4.7)
    ("SAMP-2", "Metadata", "F"),
    ("META-2", "Metadata", "C"),
    ("META-4", "Metadata", "C"),
    # Safety — SP-* and IJ-1b → Safety ≤ C
    ("SP-2b", "Safety", "C"),
    ("SP-4b", "Safety", "C"),
    ("IJ-1b", "Safety", "C"),
    # Safety — any RL-b FAIL on agentic → Safety ≤ C
    ("RL-1b", "Safety", "C"),
    ("RL-3b", "Safety", "C"),
    ("RL-4b", "Safety", "C"),
    ("RL-9b", "Safety", "C"),
]


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


def load_binary_verdicts(session_dir: pathlib.Path) -> tuple[dict | None, str]:
    """Return (verdicts_dict_or_None, status_label).

    status_label is one of:
      "present"   — file exists and parses; verdicts ingested.
      "missing"   — no binary_verdicts.json in session dir; skip Layer 1.5.
      "malformed" — file exists but does not parse; skip Layer 1.5.
      "crashed"   — file present with top-level status=="crashed" stub
                    (evaluator exited 1); skip Layer 1.5.
      "error"     — verdicts parsed but stats.runner_error > 0 (evaluator exit
                    2); verdicts still usable for Layer 1.5.
    """
    path = session_dir / "binary_verdicts.json"
    if not path.exists():
        return None, "missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "malformed"
    if data.get("status") == "crashed":
        return data, "crashed"
    stats = data.get("stats") or {}
    if isinstance(stats, dict) and stats.get("runner_error", 0) > 0:
        return data, "error"
    return data, "present"


def synthesize_binary_findings(verdicts_doc: dict | None, artifact_path: str) -> list[dict]:
    """Convert FAIL verdicts into deterministic High-severity findings.

    `id` format: "{item_id}:{artifact_path}:{dimension}/v1" — byte-identical
    across runs by construction, so Jaccard=1.0 on H+M finding-ID sets for
    the binary subset.

    PASS and NA verdicts produce no finding. Missing/malformed verdicts
    document (verdicts_doc=None) produce no findings.
    """
    if not verdicts_doc:
        return []
    verdicts = verdicts_doc.get("verdicts") or {}
    findings: list[dict] = []
    for item_id, v in verdicts.items():
        if not isinstance(v, dict):
            continue
        if v.get("verdict") != "FAIL":
            continue
        dim = ITEM_DIMENSION.get(item_id)
        if dim is None:
            # Item not in dimension map — skip, do not fabricate a dimension.
            continue
        evidence = v.get("evidence") or {}
        # Compose a short evidence string from whatever keys the evaluator
        # supplied. Line + match are the most common; reason is the fallback.
        parts: list[str] = []
        if "line" in evidence:
            parts.append(f"line {evidence['line']}")
        if "match" in evidence:
            parts.append(f"match={evidence['match']!r}")
        if "trigger" in evidence:
            parts.append(f"trigger={evidence['trigger']!r}")
        if "missing" in evidence:
            parts.append(f"missing={evidence['missing']}")
        if "reason" in evidence and not parts:
            parts.append(str(evidence["reason"]))
        evidence_text = "; ".join(parts) or f"binary item {item_id} FAIL"
        line_range = str(evidence.get("line", "")) if "line" in evidence else ""

        findings.append(
            {
                "id": f"{item_id}:{artifact_path}:{dim}/v1",
                "dimension": dim,
                "checklist_item": item_id,
                "severity": "High",
                "primary_focus": True,
                "owner_conflict": False,
                "hint_owner": None,
                "path": artifact_path,
                "line_range": line_range,
                "evidence": evidence_text,
                "why": (
                    f"Binary rubric item {item_id} FAIL per "
                    f"scripts/rubric_binary_evaluator.py. See scoring-rubric.md "
                    f"§Binary-Verifiable Rubric Items for BOUNDARY PASS/FAIL "
                    f"exemplars."
                ),
                "validation": (
                    f"Re-run scripts/rubric_binary_evaluator.py on the artifact and confirm {item_id} verdict PASS."
                ),
                "current": evidence_text,
                "recommended": (f"Apply the BOUNDARY PASS exemplar for {item_id} in scoring-rubric.md."),
                "perspective": "binary-evaluator",
            }
        )
    # Stable order for byte-identical output across runs.
    findings.sort(key=lambda f: f["id"])
    return findings


def layer1_5_binary_boundary_cap(
    merged_grades: dict[str, str], verdicts_doc: dict | None
) -> tuple[dict[str, str], list[dict]]:
    """Apply deterministic grade caps from binary FAIL verdicts.

    Monotone: only ever downgrades, never upgrades. Idempotent under
    repeated application (converges to capped grade). When `verdicts_doc`
    is None (missing/malformed), the input grades pass through unchanged
    and an empty caps_applied list is returned.
    """
    caps_applied: list[dict] = []
    if not verdicts_doc:
        return merged_grades, caps_applied
    verdicts = verdicts_doc.get("verdicts") or {}
    for item_id, dim, cap_grade in BINARY_CAPS:
        v = verdicts.get(item_id)
        if not isinstance(v, dict) or v.get("verdict") != "FAIL":
            continue
        current = merged_grades.get(dim, "F")
        triggered = GRADE_ORDER.get(current, 4) < GRADE_ORDER.get(cap_grade, 4)
        if triggered:
            merged_grades[dim] = cap_grade
        caps_applied.append(
            {
                "item": item_id,
                "dimension": dim,
                "cap_grade": cap_grade,
                "grade_before_cap": current,
                "applied": triggered,
            }
        )
    return merged_grades, caps_applied


def _infer_artifact_path(available_certs: dict[str, dict], verdicts_doc: dict | None) -> str:
    """Derive artifact path for synthesized finding IDs.

    Prefer the evaluator's recorded `artifact_path` (authoritative). Fall
    back to `artifact_frontmatter.path` or `artifact_frontmatter.name` from
    any available perspective cert. Final fallback: empty string (findings
    still have deterministic IDs via item+dim).
    """
    if verdicts_doc and verdicts_doc.get("artifact_path"):
        return str(verdicts_doc["artifact_path"])
    for cert in available_certs.values():
        fm = cert.get("artifact_frontmatter") or {}
        if fm.get("path"):
            return str(fm["path"])
        if fm.get("name"):
            return str(fm["name"])
    return ""


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

    verdicts_doc, binary_status = load_binary_verdicts(session_dir)
    artifact_path = _infer_artifact_path(available_certs, verdicts_doc)
    apply_caps = binary_status in ("present", "error")

    # Collect perspective findings, dropping any whose checklist_item is in
    # the binary-evaluator's scope or the narrative-parent supersede set.
    # This prevents double-counting with synthesize_binary_findings() output
    # and removes Haiku re-litigation of rubric-superseded narrative items.
    all_findings: list[dict] = []
    dropped_perspective_findings = 0
    for persp, cert in available_certs.items():
        for f in cert.get("findings", []):
            item = f.get("checklist_item") or ""
            if apply_caps and (item in BINARY_ITEM_IDS or item in NARRATIVE_PARENT_IDS):
                dropped_perspective_findings += 1
                continue
            finding = dict(f)
            finding.setdefault("perspective", persp)
            all_findings.append(finding)

    # Append deterministic findings synthesized from binary verdicts.
    binary_findings = synthesize_binary_findings(verdicts_doc, artifact_path) if apply_caps else []
    all_findings.extend(binary_findings)

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

    # Layer 1.5 — binary boundary caps (after Layer 1, before weighted_score).
    caps_applied: list[dict] = []
    if apply_caps:
        merged_grades, caps_applied = layer1_5_binary_boundary_cap(merged_grades, verdicts_doc)

    artifact_frontmatter = next(iter(available_certs.values())).get("artifact_frontmatter", {})
    weights = infer_weights(artifact_frontmatter)
    weighted_score = compute_weighted_score(merged_grades, weights)

    conflicts = []
    for f in merged_findings:
        if len(f.get("perspectives", [])) > 1 and f.get("owner_conflict"):
            conflicts.append(f.get("id") or f.get("evidence", "")[:50])

    binary_verdicts_applied: dict[str, str] = {}
    if verdicts_doc and isinstance(verdicts_doc.get("verdicts"), dict):
        binary_verdicts_applied = {
            item_id: (v.get("verdict") if isinstance(v, dict) else "unknown")
            for item_id, v in verdicts_doc["verdicts"].items()
        }

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
        "binary_evaluator_status": binary_status,
        "binary_verdicts_applied": binary_verdicts_applied,
        "boundary_caps_applied": caps_applied,
        "dropped_perspective_findings": dropped_perspective_findings,
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
