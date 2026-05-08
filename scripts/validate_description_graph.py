#!/usr/bin/env python3
"""Description-graph validator for Claude Code primitives.

Embedding model: minishlab/potion-base-8M (model2vec, static dense embeddings)
Pinned revision: bf8b056651a2c21b8d2565580b8569da283cab23  # see EMBEDDING_REVISION
Token estimator: len(text) // 4  (matches scripts/validate_token_budgets.py:60-65)
Exit codes: 0 = no findings, 1 = warnings only, 2 = errors present.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Literal

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# === Constants ===
EMBEDDING_MODEL = "minishlab/potion-base-8M"
# HuggingFace commit SHA, pre-fetched 2026-05-07
EMBEDDING_REVISION = "bf8b056651a2c21b8d2565580b8569da283cab23"
# 0.85 threshold from mcp-tef MiniLM calibration; A6.6 validates on potion-base-8M
SIMILARITY_THRESHOLD = 0.85
TOKEN_GRADE_BOUNDS = ((100, "A"), (300, "B"), (600, "C"), (1000, "D"))  # >1000=F
AGGREGATE_WARN, AGGREGATE_ERROR = 65_000, 120_000

try:
    from model2vec import StaticModel as _SM  # noqa: F401

    EMBEDDINGS_AVAILABLE: bool = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


@dataclass(frozen=True, slots=True)
class Primitive:
    kind: Literal["skill", "agent", "plugin"]
    path: str
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class Finding:
    check: str
    severity: Literal["error", "warning"]
    primitives: tuple[str, ...]
    message: str
    metadata: dict = field(default_factory=dict)


# === Discovery ===
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_NAME_RE = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
_DESC_BLOCK_RE = re.compile(r"^description:\s*>?\s*\n((?:[ \t]+.+\n?)+)", re.MULTILINE)
_DESC_INLINE_RE = re.compile(r"^description:\s*(?!>)(.+)$", re.MULTILINE)


def _parse_md(path: pathlib.Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    fm_m = _FM_RE.match(text)
    fm = fm_m.group(1) if fm_m else text
    nm = _NAME_RE.search(fm)
    name = nm.group(1).strip() if nm else path.stem
    dm = _DESC_BLOCK_RE.search(fm) or _DESC_INLINE_RE.search(fm)
    desc = " ".join(ln.strip() for ln in dm.group(1).splitlines() if ln.strip()) if dm else ""
    return name, desc


def discover_primitives(repo_root: pathlib.Path = REPO_ROOT) -> list[Primitive]:
    prims: list[Primitive] = []
    for glob in ("skills/*/SKILL.md", ".claude/skills/*/SKILL.md"):
        for p in sorted(repo_root.glob(glob)):
            n, d = _parse_md(p)
            prims.append(Primitive("skill", str(p.relative_to(repo_root)), n, d))
    for glob in ("agents/*.md", ".claude/agents/*.md"):
        for p in sorted(repo_root.glob(glob)):
            n, d = _parse_md(p)
            prims.append(Primitive("agent", str(p.relative_to(repo_root)), n, d))
    pj = repo_root / ".claude-plugin" / "plugin.json"
    if pj.exists():
        data = json.loads(pj.read_text(encoding="utf-8"))
        prims.append(
            Primitive("plugin", str(pj.relative_to(repo_root)), data.get("name", ""), data.get("description", ""))
        )
    return prims


# === Checks ===
def check_name_collision(prims: list[Primitive]) -> list[Finding]:
    by: dict[str, dict[str, list[Primitive]]] = {}
    for p in prims:
        by.setdefault(p.kind, {}).setdefault(p.name, []).append(p)
    findings = []
    for kind, names in by.items():
        for name, grp in names.items():
            if len(grp) > 1:
                paths = tuple(g.path for g in grp)
                findings.append(
                    Finding(
                        "name_collision",
                        "error",
                        paths,
                        f"Name '{name}' used by {len(grp)} {kind}s: {', '.join(paths)}",
                        {"kind": kind, "name": name},
                    )
                )
    return findings


# Case-insensitive; matches "Do NOT use for X — use /Y" and "do not use; use B"
_RECIP_RE = re.compile(
    r"(?:do\s+not\s+use[^;.—\n]*[;.—]\s*|(?<!\w))use\s+/?([A-Za-z][A-Za-z0-9_-]*)\b",
    re.IGNORECASE,
)


def _recip_targets(desc: str) -> set[str]:
    return {m.group(1).lstrip("/").lower() for m in _RECIP_RE.finditer(desc)}


def check_reciprocal_symmetry(prims: list[Primitive]) -> list[Finding]:
    name_map = {p.name.lower(): p for p in prims}
    findings = []
    for prim in prims:
        for tgt_name in _recip_targets(prim.description):
            tgt = name_map.get(tgt_name)
            if tgt and prim.name.lower() not in _recip_targets(tgt.description):
                findings.append(
                    Finding(
                        "reciprocal_asymmetry",
                        "warning",
                        (prim.path, tgt.path),
                        f"'{prim.name}' → '{tgt.name}' but no back-ref",
                        {"source": prim.name, "target": tgt.name},
                    )
                )
    return findings


def check_semantic_clusters(prims: list[Primitive]) -> list[Finding]:
    if not EMBEDDINGS_AVAILABLE:
        return [
            Finding(
                "cluster_skipped",
                "warning",
                (),
                "model2vec not installed; cluster check skipped",
                {"skipped": True, "fix": 'pip install -e ".[description-graph]"'},
            )
        ]
    from model2vec import StaticModel  # noqa: PLC0415

    # NOTE: model2vec StaticModel.from_pretrained() does not support revision= pinning.
    # EMBEDDING_REVISION is kept as a documentation anchor for the expected HF commit SHA.
    # Reproducibility relies on the HF Hub cache for the named model version.
    model = StaticModel.from_pretrained(EMBEDDING_MODEL)
    vecs = model.encode([p.description or " " for p in prims])
    n = len(prims)
    if n < 2:
        return []
    sim = vecs @ vecs.T
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        for j in range(i + 1, n):
            if float(sim[i, j]) >= SIMILARITY_THRESHOLD:
                union(i, j)
    comps: dict[int, list[int]] = {}
    for i in range(n):
        comps.setdefault(find(i), []).append(i)
    findings = []
    for members in comps.values():
        if len(members) < 2:
            continue
        paths = tuple(prims[i].path for i in members)
        max_s = max(float(sim[members[a], members[b]]) for a in range(len(members)) for b in range(a + 1, len(members)))
        findings.append(
            Finding(
                "cluster_conflict",
                "warning",
                paths,
                f"Semantic cluster: {len(members)} primitives share similar descriptions "
                f"(max cosine={max_s:.3f} ≥ {SIMILARITY_THRESHOLD})",
                {"max_similarity": round(max_s, 4), "threshold": SIMILARITY_THRESHOLD},
            )
        )
    return findings


def _grade(char_count: int) -> str:
    tokens = char_count // 4
    for upper, g in TOKEN_GRADE_BOUNDS:
        if tokens <= upper:
            return g
    return "F"


def check_token_grades(prims: list[Primitive]) -> list[Finding]:
    findings = []
    for p in prims:
        if _grade(len(p.description)) == "F":
            tokens = len(p.description) // 4
            msg = f"Description token grade F ({tokens} tokens > 1000) in '{p.name}'"
            findings.append(Finding("f_grade", "warning", (p.path,), msg, {"tokens": tokens, "grade": "F"}))
    return findings


def check_aggregate_budget(prims: list[Primitive]) -> list[Finding]:
    total = sum(len(p.description) for p in prims) // 4
    paths = tuple(p.path for p in prims)
    if total >= AGGREGATE_ERROR:
        msg = f"Aggregate description tokens {total} ≥ {AGGREGATE_ERROR} (error threshold)"
        return [
            Finding(
                "aggregate_budget_error", "error", paths, msg, {"total_tokens": total, "threshold": AGGREGATE_ERROR}
            )
        ]
    if total >= AGGREGATE_WARN:
        msg = f"Aggregate description tokens {total} ≥ {AGGREGATE_WARN} (warn threshold)"
        return [
            Finding(
                "aggregate_budget_warn", "warning", paths, msg, {"total_tokens": total, "threshold": AGGREGATE_WARN}
            )
        ]
    return []


# === Sanitization ===
# REGEX-LITERAL-BEGIN
_HOMEDIR_RE = re.compile(r"(/Users|/home)/[A-Za-z0-9_.-]+")
# REGEX-LITERAL-END
_RFC1918_RE = re.compile(r"\b(?:10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)\d+\.\d+\b")


def scrub(text: str) -> str:
    text = _HOMEDIR_RE.sub("<USER-HOME>", text)
    text = _RFC1918_RE.sub("<INTERNAL-IP>", text)
    return text


# === Output ===
def _f2d(f: Finding) -> dict:
    return {
        "check": f.check,
        "severity": f.severity,
        "primitives": list(f.primitives),
        "message": f.message,
        "metadata": f.metadata,
    }


def format_json(findings: list[Finding], total: int) -> str:
    errs = sum(1 for f in findings if f.severity == "error")
    warns = sum(1 for f in findings if f.severity == "warning")
    payload = {
        "findings": [_f2d(f) for f in findings],
        "summary": {
            "total_primitives": total,
            "findings_total": len(findings),
            "findings_error": errs,
            "findings_warning": warns,
        },
    }
    return json.dumps(payload, indent=2)


def format_text(findings: list[Finding], total: int) -> str:
    lines = [f"Description-graph validator — {total} primitives scanned"]
    if not findings:
        lines.append("No findings.")
        return "\n".join(lines) + "\n"
    for f in findings:
        tag = "ERROR" if f.severity == "error" else "WARN"
        lines.append(f"  [{tag}] {f.check}: {f.message}")
        for prim in f.primitives:
            lines.append(f"    - {prim}")
    errs = sum(1 for f in findings if f.severity == "error")
    warns = sum(1 for f in findings if f.severity == "warning")
    lines.append(f"Summary: {errs} error(s), {warns} warning(s).")
    return "\n".join(lines) + "\n"


# === Entry ===
def main() -> int:
    ap = argparse.ArgumentParser(description="Validate description graph across Claude Code primitives.")
    ap.add_argument("--repo", default=str(REPO_ROOT), help="Path to repository root")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    args = ap.parse_args()
    prims = discover_primitives(pathlib.Path(args.repo))
    findings: list[Finding] = []
    findings += check_name_collision(prims)
    findings += check_reciprocal_symmetry(prims)
    findings += check_semantic_clusters(prims)
    findings += check_token_grades(prims)
    findings += check_aggregate_budget(prims)
    out = format_json(findings, len(prims)) if args.format == "json" else format_text(findings, len(prims))
    sys.stdout.write(scrub(out))
    return 2 if any(f.severity == "error" for f in findings) else (1 if findings else 0)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
