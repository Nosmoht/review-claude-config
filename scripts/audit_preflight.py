#!/usr/bin/env python3
"""Preflight detector for non-deterministic LLM-binary rubric items.

Items that require LLM judgment for a final verdict but whose *trigger*
is regex-detectable. This script narrows the LLM-review surface by
listing skills containing the trigger pattern — those are the only
candidates the reviewer must judge.

Items covered (regex preflight only — no PASS/FAIL verdict):
- WS-7  Lexical-Overlap-Verification (trigger: "(if|when) the (file|...)
        (contains|mentions|...)")
- WS-8  Distractor-Isolation (trigger: ≥2 reference loads in same step)
- GA-Y  Premise-Verification (trigger: body acts on user-supplied path/
        command/claim)
- GA-Z  Function-Goal-Alignment (trigger: success criteria use form-only
        proxies)
- GA-S  Anti-Gaming (trigger: review-class skill with regex criteria)
- CE-CP Critical-Instruction-Placement (trigger: ≥150 lines + Hard Rules
        section header)
- SP-IO Indirect-Output-Validation (trigger: tool-output reference in step)
- COMP-Sel Selection-Composition (trigger: ≥2 mutually-exclusive branches)

Usage:
    python3 scripts/audit_preflight.py [--show-paths]

Output: per-item count of trigger hits across skills/*/SKILL.md, with
optional path listing.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from rubric_binary_evaluator import REPO_ROOT  # noqa: E402

# Trigger patterns (regex preflight only — verdict still requires LLM).
TRIGGERS: dict[str, re.Pattern[str]] = {
    "WS-7": re.compile(
        r"(if|when)\s+the\s+(file|description|input|argument|user|content)\s+"
        r"(contains|mentions|includes|has)\s+",
        re.IGNORECASE,
    ),
    "GA-Y": re.compile(
        # Body acts on user-supplied premise — proxy: $ARGUMENTS / user-supplied
        # path/command without nearby validation/verification verb.
        r"\$ARGUMENTS|user-supplied\s+(path|command|claim|input|file)",
    ),
    "GA-Z": re.compile(
        # Success criteria using bare form-only proxies. Proxy regex: success
        # condition mentioning count/exists without function-level verb.
        r"complete\s+when[^.]{0,120}(exists|count|created|written|finished)",
        re.IGNORECASE,
    ),
    "CE-CP": re.compile(
        # Hard-Rules-class section header. Triggers only on ≥150-line bodies
        # (filtered separately below).
        r"^#{1,3}\s+(Hard\s+Rules?|Critical\s+Constraints?|Operational\s+Rules?)",
        re.MULTILINE | re.IGNORECASE,
    ),
    "SP-IO": re.compile(
        # Tool-output reference patterns.
        r"output\s+of\s+(\w+)|result\s+from\s+(\w+)|"
        r"returned\s+by\s+(\w+)|from\s+the\s+response|"
        r"Bash\s+stdout|WebFetch\s+content",
        re.IGNORECASE,
    ),
    "COMP-Sel": re.compile(
        # ≥2 if branches in body — proxy: count of "if " at line start.
        # Verdict requires LLM to judge mutual-exclusivity.
        r"^\s*(?:[-*]?\s*)?if\s+",
        re.MULTILINE | re.IGNORECASE,
    ),
}

# WS-8 needs a separate count-based check (≥2 reference-load patterns per step).
WS_8_REF_LOAD = re.compile(
    r"references/[a-z_/-]+\.md|Read\s+[`'\"]?[a-z_/-]+\.md",
    re.IGNORECASE,
)


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

        # WS-8: ≥2 reference loads in close proximity
        ref_matches = list(WS_8_REF_LOAD.finditer(body))
        if len(ref_matches) >= 2:
            hits["WS-8"].append(rel)

        # GA-S: review-class skills (review/audit/classify/evaluate/score/certify)
        name_l = path.parent.name.lower()
        if any(name_l.startswith(verb) for verb in ("review-", "audit-", "classify-", "evaluate-")):
            hits["GA-S"].append(rel)

    notes = {
        "WS-7": "lexical-overlap classification trigger; LLM verdicts schema-check presence",
        "WS-8": "≥2 reference loads; LLM verdicts isolation-marker presence",
        "GA-Y": "$ARGUMENTS or user-supplied premise; LLM verdicts validation predicate",
        "GA-Z": "form-only success criteria; LLM verdicts function-level check",
        "GA-S": "review-class skills (advisory); LLM verdicts evidence-grounding",
        "CE-CP": "Hard Rules section in ≥150-line body; LLM verdicts placement",
        "SP-IO": "tool-output → action chain; LLM verdicts sanitization",
        "COMP-Sel": "≥2 if branches; LLM verdicts mutual-exclusivity + marker",
    }

    for item in ["WS-7", "WS-8", "GA-Y", "GA-Z", "GA-S", "CE-CP", "SP-IO", "COMP-Sel"]:
        count = len(hits[item])
        flag = " ⚠️" if count > 0 else ""
        print(f"| {item}{flag} | {count} | {notes[item]} |")

    if show_paths:
        print("\n## Candidate Skills per Item\n")
        for item in ["WS-7", "WS-8", "GA-Y", "GA-Z", "GA-S", "CE-CP", "SP-IO", "COMP-Sel"]:
            if hits[item]:
                print(f"\n### {item} ({len(hits[item])} candidates)\n")
                for p in hits[item]:
                    print(f"- `{p}`")

    return 0


if __name__ == "__main__":
    show = "--show-paths" in sys.argv[1:]
    sys.exit(main(show))
