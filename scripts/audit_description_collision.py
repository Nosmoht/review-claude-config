#!/usr/bin/env python3
"""Audit cross-skill description-token collisions across all skills/*/SKILL.md.

One-off audit script for issue #98. Imports library functions from
rubric_binary_evaluator.py rather than duplicating logic.

Usage:
    python3 scripts/audit_description_collision.py [threshold]

Default Jaccard similarity threshold: 0.3.
"""

from __future__ import annotations

import pathlib
import sys
from itertools import combinations

# Allow running directly without setuptools install
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from rubric_binary_evaluator import (  # noqa: E402
    META_3B_COUNTER_REFERENCE,
    REPO_ROOT,
    has_sibling_counter_reference,
    parse_frontmatter,
    tokenize_description,
)


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def main(threshold: float = 0.3) -> int:
    skills_root = REPO_ROOT / "skills"
    paths = sorted(skills_root.glob("*/SKILL.md"))
    print(f"# Description-Collision Audit (threshold Jaccard >= {threshold})")
    print(f"# Total skills: {len(paths)}\n")

    entries: list[tuple[str, dict, set[str]]] = []
    for p in paths:
        try:
            fm, _ = parse_frontmatter(p)
        except Exception as e:  # noqa: BLE001
            print(f"# WARN parse-fail {p.relative_to(REPO_ROOT)}: {e}")
            continue
        desc = str(fm.get("description", ""))
        toks = tokenize_description(desc)
        entries.append((str(p.relative_to(REPO_ROOT)), fm, toks))

    # META-3b verdict per skill (current behavior, threshold = 2 shared tokens)
    print("## Per-Skill META-3b Verdict (current threshold: shared >= 2)")
    print("| Skill | Verdict | Worst sibling | Shared tokens |")
    print("|-------|---------|---------------|---------------|")
    for own_path, own_fm, own_toks in entries:
        if not own_toks:
            print(f"| {own_path} | NA | (no tokens) | - |")
            continue
        worst = None
        for sib_path, sib_fm, sib_toks in entries:
            if sib_path == own_path:
                continue
            shared = own_toks & sib_toks
            if not worst or len(shared) > len(worst[1]):
                worst = (sib_path, shared, sib_fm)
        if worst is None:
            print(f"| {own_path} | NA | (no siblings) | - |")
            continue
        sib_path, shared, sib_fm = worst
        ctr = has_sibling_counter_reference(own_fm, sib_fm)
        if len(shared) >= 2 and not ctr:
            verdict = "FAIL"
        elif len(shared) >= 2 and ctr:
            verdict = "PASS (counter-ref)"
        else:
            verdict = "PASS"
        sample = sorted(shared)[:5]
        print(f"| {own_path} | {verdict} | {sib_path} | {sample} |")

    # Pairwise Jaccard
    print(f"\n## High-Overlap Pairs (Jaccard >= {threshold})")
    print("| Pair | Jaccard | Counter-ref present? |")
    print("|------|---------|----------------------|")
    flagged = 0
    for (a_path, a_fm, a_toks), (b_path, b_fm, b_toks) in combinations(entries, 2):
        sim = jaccard(a_toks, b_toks)
        if sim >= threshold:
            ctr = has_sibling_counter_reference(a_fm, b_fm)
            print(f"| {a_path} ↔ {b_path} | {sim:.2f} | {ctr} |")
            flagged += 1
    print(f"\n# Flagged pairs: {flagged}")

    # Counter-reference regex coverage check
    print("\n## Counter-Reference Regex Coverage")
    ctr_count = sum(1 for _, fm, _ in entries if META_3B_COUNTER_REFERENCE.search(str(fm.get("description", ""))))
    print(f"# Skills with counter-ref pattern in own description: {ctr_count} / {len(entries)}")
    return 0


if __name__ == "__main__":
    th = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3
    sys.exit(main(th))
