#!/usr/bin/env python3
"""Validate reference file token budgets.

Scans skills/*/references/*.md (including domain-cache/) and checks estimated
token counts against defined budgets. Token estimation uses chars / 4.

Exit codes: 0 = all within budget, 1 = at least one file exceeds budget.
"""

import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Budget in tokens (chars / 4). Pattern matched against file name.
BUDGETS: dict[str, int] = {
    "scoring-rubric.md": 1000,
    "engineering-baseline.md": 2000,
    "signal-catalog.md": 1000,
}

DOMAIN_CACHE_BUDGET = 500
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
