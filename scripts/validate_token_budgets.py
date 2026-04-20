#!/usr/bin/env python3
"""Validate reference file token budgets.

Scans skills/*/references/*.md (including domain-cache/) and checks estimated
token counts against defined budgets. Token estimation uses chars / 4.

Exit codes: 0 = all within budget, 1 = at least one file exceeds budget.
"""

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Budget in tokens (chars / 4). Matched against file name.
# Rationale: centralized budget map per ESLint/Ruff convention (not per-file
# frontmatter overrides). See research: arXiv 2603.29919, ESLint flat config,
# Ruff per-file-ignores — all use centralized config for numeric thresholds.
BUDGETS: dict[str, int] = {
    # Core review references (large by design)
    "scoring-rubric.md": 3300,  # P0.5: META/CE-X/COMP/SAMP/CLAR binary items + plugin scoring
    "engineering-baseline.md": 3500,  # P0.5 lowers to 2,600 post-refresh
    "signal-catalog.md": 1000,
    # Evaluation guides — dense checklists, legitimately >500.
    # Opus 4.7 tokenizer ~35% larger than 4.6 — bumped per plan rev4.
    "skill-evaluation-guide.md": 1000,
    "agent-evaluation-guide.md": 1800,  # P0.1: 15 fields + Opus 4.7 SAMP-1/2
    "claude-md-evaluation-guide.md": 800,
    "hook-evaluation-guide.md": 1500,  # P0.2: 26-event catalog + version-min
    "mcp-evaluation-guide.md": 1200,  # P0.3: MCP 2026 + April security disclosure
    "plugin-evaluation-guide.md": 1500,  # P0.4: PM/CL/F/IJ/MS sections
    "settings-evaluation-guide.md": 800,
    # Scaffold templates — contain full examples
    "skill-template.md": 750,
    "rule-template.md": 700,
    "agent-template.md": 600,
    "mcp-server-template.md": 800,  # P0.3: stdio + remote + 2026 schema
    # P0.6 — known-critical-bug detector rules with adversarial test cases.
    # Two files share the basename "detector-rules.md" / "detection-rules.md";
    # both encode multiple per-rule sections, justifying 1500.
    "detection-rules.md": 1500,
    "detector-rules.md": 1500,
    # Provenance map — not runtime-loaded, budget prevents unbounded growth
    "engineering-baseline-provenance.md": 1500,
    # Structured references
    "reference-patterns.md": 800,
    "cross-skill-dependencies.md": 600,
    "review-report-contract.md": 600,
    "report-template.md": 700,
    # Boundary exemplars — PASS/FAIL pairs reduce verdict variance (BARS).
    # P0.1 added 8 new exemplar pairs; P0.5 added META/CE-X/COMP-X/Y/Z;
    # P1.1 added 10 Integration-owned exemplars (IJ-1, SP-1/3/4, RL-1/4/9, RD-1/3).
    "boundary-exemplars.md": 1700,
    # P1.2 — 3-tier structured-output recovery contract
    "report-parser-contract.md": 1000,
    # P1.1 — multi-perspective review (JIT-loaded by /review-skill orchestrator only)
    # Dense protocol + merge-rules spec; 1,200 accommodates Layer-0-to-Layer-4
    # pseudocode + per-block cache-breakpoint layout without loss of fidelity.
    "perspective-dispatch-protocol.md": 1200,
    "merge-rules.md": 1200,
    # Optional extractions pre-declared (created if parent guide overflows).
    # Loaded JIT: opus-4.7 only when model: opus-4-7 detected.
    "opus-4.7-migration-checks.md": 800,  # P0.1 extraction target
    "mcp-2026-security-checklist.md": 800,  # P0.3 extraction target
    "injection-regex-library.md": 1500,  # P0.3 — 22 Tier-A patterns + procedure
}

DOMAIN_CACHE_BUDGET = 800
DEFAULT_BUDGET = 500


def estimate_tokens(path: pathlib.Path) -> int:
    """Estimate token count as character_count / 4."""
    try:
        return len(path.read_text(encoding="utf-8")) // 4
    except Exception:
        return 0


def get_budget(path: pathlib.Path) -> int:
    """Return the token budget for a given reference file."""
    if path.name in BUDGETS:
        return BUDGETS[path.name]
    if "domain-cache" in path.parts:
        return DOMAIN_CACHE_BUDGET
    return DEFAULT_BUDGET


def classify(tokens: int, budget: int) -> str:
    """Classify token usage: PASS (<80%), WARN (80-100%), FAIL (>100%)."""
    ratio = tokens / budget if budget > 0 else float("inf")
    if ratio > 1.0:
        return "FAIL"
    if ratio >= 0.8:
        return "WARN"
    return "PASS"


def validate_token_budgets() -> list[str]:
    """Check all reference files against their token budgets.

    Returns a list of error strings for files that exceed their budget (FAIL).
    Prints warnings for files approaching their budget (WARN).
    """
    errors: list[str] = []
    ref_paths = sorted(REPO_ROOT.glob("skills/*/references/**/*.md"))
    if not ref_paths:
        return ["No reference files found under skills/*/references/"]

    for path in ref_paths:
        # Skip INDEX.md in domain-cache
        if path.name == "INDEX.md" and "domain-cache" in path.parts:
            continue

        tokens = estimate_tokens(path)
        budget = get_budget(path)
        status = classify(tokens, budget)
        pct = int(tokens / budget * 100) if budget > 0 else 0
        rel = path.relative_to(REPO_ROOT)

        if status == "FAIL":
            errors.append(f"{rel}: {tokens} tokens ({pct}% of {budget} budget)")
        elif status == "WARN":
            print(f"  WARN: {rel}: {tokens} tokens ({pct}% of {budget} budget)")

    return errors


def main() -> int:
    errors = validate_token_budgets()
    if not errors:
        print("Token budgets: OK")
        return 0

    print("\nToken budgets:")
    for e in errors:
        print(f"  ERROR: {e}")

    over_budget = [e for e in errors if "No reference files" not in e]
    if over_budget:
        print(f"\n{len(over_budget)} file(s) over budget.")
    else:
        print(f"\n{len(errors)} error(s) found.")
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
