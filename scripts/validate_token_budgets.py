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
    # Issue #69: +10 binary exemplars with full regex specs (CLAR-3/4,
    # SP-2b/4b, RL-1b/3b/4b/9b, IJ-1b) + COMP-X review-skill clause +
    # AH-2b Default-Handling-Pair (Plans/steady-distilling-runner.md Phase 0).
    # Issue #63: +PE-1 CoT-Scaffolding / PE-2 Hedge-Free-Directives binary
    # items + Opus 4.7 reasoning-model anti-pattern section + SAMP-2 hard-F
    # rationale sentence (2026-04-22 rubric refresh for Opus 4.7 GA).
    # Issue #61: +MCP source-integrity C-cap + Tier-0 F-cap + extended
    # agentic overlay R1-R11 (R4b HITL-surface-manipulation, R11 cascading
    # containment) + broadened R9 scope (memory-write poisoning, OWASP
    # ASI06). MCPTox arXiv:2508.14925 + OWASP ASI2026.
    # Issue #70: +WS-2b, WS-4 dim-pin note, RD-5b binary entries for
    # residual interpretive-flipper closure.
    # Issue #92: +GA-Y/GA-Z/GA-S Goal Alignment evidence-grounded tests
    # (sycophancy / goal-misgen / spec-gaming clusters).
    # Issue #93: +WS-6/7/8 Clarity linguistic-failure cluster
    # (oLMpics / HANS / Kassner-Ettinger).
    # Issue #96: +COMP-V/COMP-Sel Completeness benchmarks
    # (IFEval / FollowBench / ComplexBench).
    # Issue #95: +SP-IO Safety tool-misuse benchmarks
    # (ToolEmu / AgentDojo / InjecAgent).
    # Issue #94: +CE-CP Critical-Instruction-Placement (Liu et al. LiM).
    # Issue #98: +META-3c Discriminating-Keyword-Presence
    # (MetaTool / ToolLLM / Gorilla — description disambiguation).
    "scoring-rubric.md": 10100,
    # Issue #61: Tier-0 same-turn combination section (OWASP ASI02 Tool
    # Misuse; MCP Protocol Security arXiv:2601.17549, 30+ CVEs Jan-Feb
    # 2026 incl. CVSS 9.6 RCE).
    "tool-grant-decision-tree.md": 800,
    "engineering-baseline.md": 4200,  # +500 for #92 GA techniques + #93 linguistic-failure + #97 CoVe
    "signal-catalog.md": 1000,
    # Evaluation guides — dense checklists, legitimately >500.
    # Opus 4.7 tokenizer ~35% larger than 4.6 — bumped per plan rev4.
    # Issue #69: +CLAR-3/4, SP-2b/4b, RL-1b/3b/4b/9b, IJ-1b rows
    # Issue #70: +WS-2b, RD-5b rows + WS-4 dim-pin amendment.
    # Issue #93: +WS-6/7/8 rows (linguistic-failure cluster).
    "skill-evaluation-guide.md": 1700,
    # P0.1: 15 fields + Opus 4.7 SAMP-1/2.
    # Issue #69: +SP-2b/4b, RL-1b/3b/4b/9b, IJ-1b rows.
    "agent-evaluation-guide.md": 2100,
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
    # Issue #71 added §"Finding Determinism" defining the deterministic vs
    # advisory class split — load-bearing policy contract for downstream
    # consumers (apply-*, review-analytics, check-repo-health).
    # Issue #81 P0.1b added §"Sidecar Emission" defining the findings.json
    # sidecar contract (sibling naming, schema reference, emit conditions,
    # empty-vs-malformed semantics, atomicity, batch-sidecar reservation,
    # applyability-gate consumer obligation) — required surface for the
    # apply-* migration off the Markdown-heading regex parse.
    "review-report-contract.md": 1500,
    "report-template.md": 700,
    # Boundary exemplars — PASS/FAIL pairs reduce verdict variance (BARS).
    # P0.1 added 8 new exemplar pairs; P0.5 added META/CE-X/COMP-X/Y/Z;
    # P1.1 added 10 Integration-owned exemplars (IJ-1, SP-1/3/4, RL-1/4/9, RD-1/3).
    "boundary-exemplars.md": 1700,
    # P1.2 — 3-tier structured-output recovery contract
    "report-parser-contract.md": 1000,
    # P1.1 — multi-perspective review (JIT-loaded by /review-skill orchestrator only).
    # Issue #68/#69 wiring (2026-04-22): perspective-dispatch-protocol adds
    # §"Pre-Dispatch Binary Evaluation" documenting rubric_binary_evaluator
    # wiring, skip-contract, Alt-A vs Alt-B rationale. merge-rules adds
    # Layer-1.5 boundary-cap table (20 rules), binary-finding synthesis,
    # perspective-finding dropping (binary + narrative parents), and the
    # missing/malformed/crashed degradation paths. Issue #71 added the
    # §"Convergence Policy" section + scoped the Determinism Invariant
    # paragraph to the deterministic subset. Issue #72 renamed
    # §"Perspective Finding Dropping" → §"Perspective Finding Handling"
    # with the drop/demote/fail-safe contract. Both files are JIT-only
    # (not in shared prefix), so size growth costs one load per
    # /review-skill invocation, not per perspective dispatch.
    "perspective-dispatch-protocol.md": 1700,
    "merge-rules.md": 3000,
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
