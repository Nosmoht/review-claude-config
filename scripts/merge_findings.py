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
import os
import pathlib
import re
import sys

PERSPECTIVES = ("clarity", "correctness", "integration")
OVERLAP_THRESHOLD = 0.80

GRADE_TO_NUMERIC = {"A": 95, "B": 85, "C": 75, "D": 65, "F": 50}
GRADE_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4}
SEVERITY_RANK = {"High": 3, "Medium": 2, "Low": 1}

# 28 binary-verifiable rubric items owned by scripts/rubric_binary_evaluator.py.
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
        "WS-2b",
        "RD-5b",
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

# Narrative parent items the rubric supersedes with -b variants, or items the
# rubric drops in favor of a deterministic drop-from-merge policy (WS-4).
# Perspective findings on these also drop to prevent Haiku-class agents from
# re-litigating the same surface.
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
        "WS-2",  # superseded by WS-2b (issue #70)
        "WS-4",  # dim-pinned to Clarity via ITEM_DIMENSION + dropped here
        "RD-5",  # superseded by RD-5b (issue #70)
    ]
)

# Item → dimension binding. Mirrors scoring-rubric.md section headings.
# Used for (a) finding-ID canonicalisation in canonicalize_perspective_ids()
# so Haiku agents cannot produce dim-drifted IDs (issue #70: WS-4 Clarity↔Safety flip),
# and (b) BINARY_CAPS + synthesize_binary_findings() lookups.
#
# SKILL-RUBRIC entries (below). For agent-rubric items that do not collide with
# skill IDs, see AGENT_ITEM_DIMENSION — get_item_dim() dispatches between them
# on artifact_type. Issue #76.
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
    "WS-2b": "Clarity",
    "WS-4": "Clarity",
    "RD-5b": "Clarity",
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

# Agent-rubric dimension pins for non-binary perspective-owned items. Namespace
# is DISJOINT from the skill-rubric ITEM_DIMENSION entries above by construction
# — only agent-rubric IDs that (a) do not collide with skill-rubric IDs on
# dimension, and (b) are not in NARRATIVE_PARENT_IDS, are listed here.
#
# Collisions deliberately OMITTED (same ID, different dimension per rubric —
# canonicalization on either would mis-pin the other; preserve current
# unpinned fall-through):
#   AP-2 (skill=Metadata, agent=Safety)
#   AP-3 (skill=Prompt Engineering, agent=Metadata)
#   AP-4 (skill=Completeness, agent=Prompt Engineering)
#
# Narrative-parent IDs deliberately OMITTED (dropped before canonicalize, so
# dim pinning has no effect): IJ-1, RL-1, RL-3, RL-4, RL-9.
#
# Source: skills/review-agent/references/agent-evaluation-guide.md Dim column.
# Issue #76. Extending this table to include TV-4 / AF-5 / AF-6 as binary
# items + their BINARY_CAPS entries is #74 Phase 2.
AGENT_ITEM_DIMENSION: dict[str, str] = {
    # Clarity (2)
    "SF-2": "Clarity",
    "RL-7": "Clarity",
    # Completeness (9)
    "DA-4": "Completeness",
    "TC-1": "Completeness",
    "TC-2": "Completeness",
    "TC-3": "Completeness",
    "RL-2": "Completeness",
    "RL-5": "Completeness",
    "RL-6": "Completeness",
    "RL-10": "Completeness",
    "RT-4": "Completeness",
    # Prompt Engineering (1)
    "AF-3": "Prompt Engineering",
    # Context Engineering (5)
    "DA-2a": "Context Engineering",
    "DA-2b": "Context Engineering",
    "SF-1": "Context Engineering",
    "RT-5": "Context Engineering",
    "AF-2": "Context Engineering",
    # Safety (7)
    "TV-2": "Safety",
    "TV-3": "Safety",
    "RL-8": "Safety",
    "IJ-2": "Safety",
    "GV-1": "Safety",
    "GV-2": "Safety",
    "AF-1": "Safety",
    "AF-4": "Safety",
    "AF-5": "Safety",
    # Metadata (9)
    "MS-1": "Metadata",
    "DA-1": "Metadata",
    "DA-5": "Metadata",
    "TV-1": "Metadata",
    "TV-4": "Metadata",
    "TV-5": "Metadata",
    "TV-6": "Metadata",
    "AF-6": "Metadata",
    "AF-7": "Metadata",
}


def get_item_dim(item_id: str, artifact_type: str = "skill") -> str | None:
    """Resolve an item's pinned dimension for the given artifact type.

    Agent artifacts consult AGENT_ITEM_DIMENSION first; if the item is not
    there (e.g., a universal binary item like SP-2b or a namespace-collision
    item like AP-3), fall back to ITEM_DIMENSION. Skill artifacts use only
    ITEM_DIMENSION. Issue #76.
    """
    if artifact_type == "agent":
        dim = AGENT_ITEM_DIMENSION.get(item_id)
        if dim is not None:
            return dim
    return ITEM_DIMENSION.get(item_id)


# Grade-boundary cap table. Each entry: FAIL on `item` caps `dimension` at
# `cap_grade` (cannot be better). Source: scoring-rubric.md grade-boundary
# clauses. Caps are monotone — never upgrade a merged grade. Multiple caps on
# the same dimension stack (strictest wins because of GRADE_ORDER check).
BINARY_CAPS: list[tuple[str, str, str]] = [
    # Clarity (CLAR-1/2/3/4 OR WS-2b OR RD-5b → Clarity ≤ C)
    ("CLAR-1", "Clarity", "C"),
    ("CLAR-2", "Clarity", "C"),
    ("CLAR-3", "Clarity", "C"),
    ("CLAR-4", "Clarity", "C"),
    ("WS-2b", "Clarity", "C"),
    ("RD-5b", "Clarity", "C"),
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


def canonicalize_perspective_ids(findings: list[dict], artifact_type: str = "skill") -> list[dict]:
    """Rewrite ``dimension`` + ``id`` on perspective findings whose
    ``checklist_item`` is pinned by :func:`get_item_dim`.

    Rewrite rule: ``id = f"{checklist_item}:{path}:{pinned_dim}/v1"`` using
    ``finding['checklist_item']`` and ``finding['path']`` as authoritative
    sources. This prevents the retest-4 flip where Haiku emitted
    ``WS-4:path:Clarity/v1`` in runA and ``WS-4:path:Safety/v1`` in runB on
    identical evidence — after rewrite both runs produce the same id and
    collapse in Layer-0 dedup. Findings without a pinned ``checklist_item``
    or without a ``path`` pass through unchanged.

    ``artifact_type`` routes the lookup: agent artifacts consult
    :data:`AGENT_ITEM_DIMENSION` first. Default ``"skill"`` preserves pre-#76
    behaviour for callers that do not thread artifact_type through.

    Issue #70; extended in #76.
    """
    rewritten: list[dict] = []
    for f in findings:
        item = f.get("checklist_item") or ""
        pinned_dim = get_item_dim(item, artifact_type)
        path = f.get("path") or ""
        if not pinned_dim or not path:
            rewritten.append(f)
            continue
        new_f = dict(f)
        new_f["dimension"] = pinned_dim
        new_f["id"] = f"{item}:{path}:{pinned_dim}/v1"
        rewritten.append(new_f)
    return rewritten


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


# Patterns for the missing-primitive false-positive filter.
# A finding is a candidate when its evidence text includes BOTH a non-existence
# claim AND a primitive name reference. We then check whether the named
# primitive actually exists in the repo and drop the finding if it does.
_MISSING_PRIMITIVE_CLAIM_RE = re.compile(
    r"(does\s+not\s+exist|not\s+found|missing|absent|doesn'?t\s+exist|"
    r"do\s+not\s+exist|are\s+not\s+registered|not\s+registered|not\s+present)",
    re.IGNORECASE,
)
# Primary extraction: any name-like token in the evidence that could be a
# primitive. Broad on purpose — false-negatives on the filter are safer than
# false-positives, since unfiltered findings still surface for reviewer triage.
_NAME_LIKE_RE = re.compile(r"[a-zA-Z][\w\-]{2,}(?::[\w\-]+)?")
# Brace-expansion: ``review-perspective-{clarity,correctness,integration}``
# expands to three concrete names. Common in agent prose when listing multiple
# subagent_types compactly.
_BRACE_EXPANSION_RE = re.compile(r"([a-zA-Z][\w\-]+)\{([^}]+)\}")
# The directories we recognise as primitive locations in the target repo.
_PRIMITIVE_DIRS = ("agents", "skills", "hooks", "scripts", ".claude/agents", ".claude/skills")


def find_repo_root(start_path: pathlib.Path, max_levels: int = 20) -> pathlib.Path | None:
    """Walk up from ``start_path`` looking for a directory that contains at
    least one of the recognised primitive subdirs. Returns None when no such
    ancestor is found within ``max_levels`` levels."""
    cur = pathlib.Path(start_path).resolve()
    for _ in range(max_levels):
        for sub in _PRIMITIVE_DIRS:
            if (cur / sub).is_dir():
                return cur
        if cur.parent == cur:
            return None
        cur = cur.parent
    return None


def primitive_exists(repo_root: pathlib.Path, raw_name: str) -> bool:
    """True iff ``raw_name`` resolves to a file under one of the primitive
    subdirectories of ``repo_root``. Strips a plugin-namespace prefix
    (``<plugin>:<name>``) and tries common file extensions / nested layouts."""
    if not raw_name:
        return False
    bare = raw_name.split(":")[-1].strip().rstrip(".,;:!?\"'`")
    if not bare:
        return False
    # Drop any explicit extension before re-trying with our canonical set.
    stem = bare.rsplit(".", 1)[0] if bare.endswith((".md", ".py")) else bare
    for sub in _PRIMITIVE_DIRS:
        base = repo_root / sub
        if not base.is_dir():
            continue
        candidates = [
            base / f"{stem}.md",
            base / f"{stem}.py",
            base / stem / "AGENT.md",
            base / stem / "SKILL.md",
        ]
        if any(p.is_file() for p in candidates):
            return True
    return False


def filter_false_positive_missing_primitive(
    findings: list[dict], repo_root: pathlib.Path | None
) -> tuple[list[dict], list[dict]]:
    """Drop findings that claim a primitive does not exist when it actually does.

    Some perspective agents (notably Haiku) emit ``RD-1`` / ``RD-3`` findings
    asserting a referenced primitive (subagent_type, skill, hook, script) is
    missing without successfully running the verification gate. When the named
    primitive resolves to a real file in the target repo, the finding is a
    false positive.

    Returns ``(kept_findings, dropped_findings)``. The dropped list preserves
    the original finding plus a synthesised ``false_positive_reason`` field for
    audit transparency.
    """
    if repo_root is None or not repo_root.is_dir():
        return list(findings), []
    kept: list[dict] = []
    dropped: list[dict] = []
    for f in findings:
        evidence = f.get("evidence") or ""
        if not _MISSING_PRIMITIVE_CLAIM_RE.search(evidence):
            kept.append(f)
            continue
        # Brace-expansion candidates first — more specific than free tokens.
        candidates: list[str] = []
        for m in _BRACE_EXPANSION_RE.finditer(evidence):
            prefix, contents = m.group(1), m.group(2)
            candidates.extend(f"{prefix}{part.strip()}" for part in contents.split(","))
        # Then generic name-like tokens (covers cases without brace shorthand).
        candidates.extend(_NAME_LIKE_RE.findall(evidence))
        verified = [name for name in candidates if primitive_exists(repo_root, name)]
        if not verified:
            kept.append(f)
            continue
        annotated = dict(f)
        # Cite the specific primitives whose existence contradicts the claim.
        # De-duplicate while preserving order; cap the citation list at 5.
        seen: set[str] = set()
        unique_verified: list[str] = []
        for name in verified:
            if name not in seen:
                seen.add(name)
                unique_verified.append(name)
            if len(unique_verified) >= 5:
                break
        annotated["false_positive_reason"] = (
            f"primitives [{', '.join(unique_verified)}] resolve to existing "
            f"files under {repo_root}; non-existence claim contradicted by repo state"
        )
        dropped.append(annotated)
    return kept, dropped


def merge_directory(session_dir: pathlib.Path, repo_root: pathlib.Path | None = None) -> dict:
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
    # Issue #76: resolve artifact_type from the binary evaluator output (source
    # of truth — written by classify_artifact(). Missing/legacy verdicts_doc →
    # default "skill" (preserves pre-#76 behaviour).
    artifact_type = (verdicts_doc or {}).get("artifact_type") or "skill"

    # Collect perspective findings with two handling rules (issue #72):
    #   1. Drop findings whose checklist_item is in the deterministic subset
    #      (BINARY_ITEM_IDS | NARRATIVE_PARENT_IDS) — prevents double-counting
    #      with synthesize_binary_findings() output and removes Haiku
    #      re-litigation of rubric-superseded narrative items.
    #   2. Demote remaining (advisory) findings from High/Medium to Low so
    #      they surface for reviewer triage but do not block convergence.
    #      Issue #71 scoped the convergence gate to the deterministic subset;
    #      #72 makes advisory H+M unreachable by construction.
    # Fail-safe: when apply_caps is False (binary evaluator missing/malformed),
    # neither drop nor demote fires — perspectives retain full authority.
    all_findings: list[dict] = []
    dropped_perspective_findings = 0
    demoted_perspective_findings = 0
    for persp, cert in available_certs.items():
        for f in cert.get("findings", []):
            item = f.get("checklist_item") or ""
            if apply_caps and (item in BINARY_ITEM_IDS or item in NARRATIVE_PARENT_IDS):
                dropped_perspective_findings += 1
                continue
            finding = dict(f)
            finding.setdefault("perspective", persp)
            # Case-insensitive match to demote off-spec severity labels too
            # (e.g. Haiku emitting "HIGH" or "high"). Canonical spec is
            # "High" / "Medium" / "Low"; other strings are treated as Low-rank
            # elsewhere (SEVERITY_RANK.get default) but should still demote.
            sev = (finding.get("severity") or "").strip().lower()
            if apply_caps and sev in ("high", "medium"):
                finding["severity"] = "Low"
                demoted_perspective_findings += 1
            all_findings.append(finding)

    # Canonicalise IDs on pinned-dim items before synthesis + dedup so
    # perspective-emitted findings share IDs across runs even if Haiku
    # reported different dimensions on identical evidence (issue #70).
    # artifact_type routing adds agent-rubric item pins (issue #76).
    all_findings = canonicalize_perspective_ids(all_findings, artifact_type)

    # Append deterministic findings synthesized from binary verdicts.
    binary_findings = synthesize_binary_findings(verdicts_doc, artifact_path) if apply_caps else []
    all_findings.extend(binary_findings)

    merged_findings = layer0_dedup(all_findings)

    # Deterministic post-filter: drop missing-primitive false positives.
    # Resolves the integration agent's verify-before-fail brittleness on Haiku.
    if repo_root is None:
        # Heuristic: walk up from the session_dir's resolved location looking
        # for a recognised repo layout. Falls back to os.getcwd() when the
        # session_dir lives outside the repo (the typical $CLAUDE_PLUGIN_DATA
        # path).
        repo_root = find_repo_root(session_dir) or find_repo_root(pathlib.Path(os.getcwd()))
    merged_findings, false_positive_dropped = filter_false_positive_missing_primitive(
        merged_findings, repo_root
    )

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
            p: round(
                cert["weighted_score"] if cert.get("weighted_score") is not None
                else compute_weighted_score(cert.get("dimensions") or {}, weights),
                2,
            )
            for p, cert in available_certs.items()
            if cert.get("weighted_score") is not None or cert.get("dimensions")
        },
        "binary_evaluator_status": binary_status,
        "binary_verdicts_applied": binary_verdicts_applied,
        "boundary_caps_applied": caps_applied,
        "dropped_perspective_findings": dropped_perspective_findings,
        "demoted_perspective_findings": demoted_perspective_findings,
        "false_positive_missing_primitive_dropped": [
            {
                "id": d.get("id"),
                "checklist_item": d.get("checklist_item"),
                "perspective": d.get("perspective"),
                "reason": d.get("false_positive_reason"),
            }
            for d in false_positive_dropped
        ],
    }


def write_findings_sidecar(result: dict, out_path: pathlib.Path, session_id: str | None = None) -> None:
    """Write the schema-validated findings.json sidecar.

    Format conforms to schemas/findings-list.schema.json. The sidecar is a
    machine-parsable counterpart to the human-readable report.md — apply-*
    skills consume this file rather than regex-parsing the Markdown.

    Atomic write via temp + rename to prevent partial-read by a concurrent
    consumer.
    """
    payload = {
        "generated_by": "merge_findings",
        "schema_version": "1.0.0",
        "findings": result.get("findings", []),
    }
    if session_id is not None:
        payload["session_id"] = session_id
    artifact_path = ""
    for f in result.get("findings", []):
        if isinstance(f, dict) and f.get("path"):
            artifact_path = f["path"]
            break
    if artifact_path:
        payload["artifact_path"] = artifact_path

    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(out_path)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Merge perspective certificates into a deterministic verdict.")
    parser.add_argument(
        "session_dir",
        type=pathlib.Path,
        help="directory containing <perspective>.json certificates",
    )
    parser.add_argument(
        "--findings-out",
        type=pathlib.Path,
        default=None,
        help=(
            "optional path to write a schema-validated findings.json sidecar "
            "(see schemas/findings-list.schema.json). The merged stdout JSON is "
            "always emitted regardless of this flag."
        ),
    )
    parser.add_argument(
        "--repo-root",
        type=pathlib.Path,
        default=None,
        help=(
            "repo root used by the missing-primitive false-positive filter. "
            "Defaults to walking up from the session_dir, then to os.getcwd(). "
            "Pass an explicit path when invoking from outside the target repo."
        ),
    )
    args = parser.parse_args()

    if not args.session_dir.is_dir():
        print(f"Not a directory: {args.session_dir}", file=sys.stderr)
        return 2

    result = merge_directory(args.session_dir, repo_root=args.repo_root)
    print(json.dumps(result, indent=2, sort_keys=True))

    if args.findings_out is not None:
        try:
            session_id = args.session_dir.name if args.session_dir.name else None
            write_findings_sidecar(result, args.findings_out, session_id=session_id)
        except OSError as e:
            print(f"merge_findings: failed to write {args.findings_out}: {e}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
