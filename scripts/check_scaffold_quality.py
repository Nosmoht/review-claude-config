#!/usr/bin/env python3
"""Scaffold-quality harness: validates scaffold fixture files and rubric-coverage matrices.

Two operating modes:

  Default — validate all fixture files in tests/fixtures/scaffold_quality/:
      Skill fixtures  (*.skill.md)  → rubric_binary_evaluator
      Agent fixtures  (*.agent.md)  → rubric_binary_evaluator
      Rule fixtures   (*.rule.md)   → structural validator (see validate_rule_fixture)

  --verify-matrix-complete — verify that every rubric-coverage.md in the
      scaffold-skill, scaffold-agent, and scaffold-rule skills covers all
      binary skill IDs parsed from scoring-rubric.md §Item Inventory.

Exit codes:
    0  — all checks pass
    1  — harness crash or rubric parse degraded (RUBRIC_PARSE_DEGRADED)
    2  — at least one fixture has a new in-scope FAIL

Usage:
    python3 scripts/check_scaffold_quality.py
    python3 scripts/check_scaffold_quality.py --verify-matrix-complete
    python3 scripts/check_scaffold_quality.py --fixture-dir <path>
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from typing import NamedTuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Defensive sentinel — fixtures start with this comment.
FIXTURE_SENTINEL = "<!-- TEST FIXTURE"

# Minimum number of binary skill IDs to accept as a valid rubric parse.
MIN_BINARY_IDS = 25

# Paths to rubric-coverage matrices to check in --verify-matrix-complete mode.
# Rules use a separate narrative rubric (Clarity/Completeness/GA), NOT the binary
# skill evaluator — the rule matrix is excluded from binary-ID completeness check.
COVERAGE_MATRIX_PATHS = [
    REPO_ROOT / "skills" / "scaffold-skill" / "references" / "rubric-coverage.md",
    REPO_ROOT / "skills" / "scaffold-agent" / "references" / "rubric-coverage.md",
]

RULE_TEMPLATE_PATH = REPO_ROOT / "skills" / "scaffold-rule" / "references" / "rule-template.md"
SCORING_RUBRIC_PATH = REPO_ROOT / "skills" / "review-claude-config" / "references" / "scoring-rubric.md"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


class CheckResult(NamedTuple):
    path: pathlib.Path
    ok: bool
    detail: str


# ---------------------------------------------------------------------------
# Rubric ID parsing
# ---------------------------------------------------------------------------


def parse_binary_skill_ids(rubric_path: pathlib.Path) -> list[str]:
    """Return list of binary skill item IDs from scoring-rubric.md §Item Inventory.

    Parses only lines inside the '### Binary-Evaluated Items' subsection of
    '## Item Inventory'. Stops at the next ### or ## heading.
    Regex: ^|  <ID>  | where ID matches [A-Z]+(-[A-Z0-9a-z]+)+
    Exits with code 1 if fewer than MIN_BINARY_IDS are found (RUBRIC_PARSE_DEGRADED).
    """
    try:
        text = rubric_path.read_text(encoding="utf-8")
    except OSError as exc:
        _halt(f"Cannot read scoring rubric: {exc}")

    in_section = False
    ids: list[str] = []
    item_re = re.compile(r"^\|\s+([A-Z]+(?:-[A-Z0-9a-z]+)+)\s+\|")
    binary_section_re = re.compile(r"^###\s+Binary-Evaluated Items")
    next_heading_re = re.compile(r"^##")

    for line in text.splitlines():
        if binary_section_re.match(line):
            in_section = True
            continue
        if in_section and next_heading_re.match(line):
            break
        if in_section:
            m = item_re.match(line)
            if m:
                ids.append(m.group(1))

    if len(ids) < MIN_BINARY_IDS:
        _halt(
            f"RUBRIC_PARSE_DEGRADED: only {len(ids)} binary IDs parsed "
            f"(expected >= {MIN_BINARY_IDS}). "
            f"Check that '### Binary-Evaluated Items' exists in {rubric_path}."
        )

    return ids


# ---------------------------------------------------------------------------
# Rule fixture structural validator
# ---------------------------------------------------------------------------


def _derive_required_rule_sections(template_path: pathlib.Path) -> list[str]:
    """Extract required H2 section names from the Canonical Rule Structure block.

    Reads the rule-template.md file, finds the fenced code block under
    '## Canonical Rule Structure', and collects all '## ' headings within it.
    Returns section names as strings without the '## ' prefix.
    """
    try:
        text = template_path.read_text(encoding="utf-8")
    except OSError as exc:
        _halt(f"Cannot read rule template: {exc}")

    canonical_re = re.compile(r"^##\s+Canonical Rule Structure")
    fence_re = re.compile(r"^```")
    h2_in_block_re = re.compile(r"^## (.+)")

    lines = text.splitlines()
    found_section = False
    in_fence = False
    fence_count = 0
    sections: list[str] = []

    for line in lines:
        if not found_section:
            if canonical_re.match(line):
                found_section = True
            continue
        # Inside the Canonical Rule Structure section.
        if fence_re.match(line):
            fence_count += 1
            if fence_count == 1:
                in_fence = True
            elif fence_count == 2:
                break  # end of the code block
            continue
        if in_fence:
            m = h2_in_block_re.match(line)
            if m:
                sections.append(m.group(1).strip())

    return sections


def _has_sentinel(text: str) -> bool:
    """Return True if the fixture sentinel appears within the first 1024 chars.

    Rule fixtures have no frontmatter, so the sentinel is at line 1.
    Skill/agent fixtures have YAML frontmatter; the sentinel follows
    the closing '---' delimiter, so it appears after the frontmatter block
    but still near the start of the file.
    """
    return FIXTURE_SENTINEL in text[:1024]


def validate_rule_fixture(path: pathlib.Path, required_sections: list[str]) -> CheckResult:
    """Validate a rule fixture against required H2 sections derived at runtime."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return CheckResult(path=path, ok=False, detail=f"Cannot read: {exc}")

    if not _has_sentinel(text):
        return CheckResult(
            path=path,
            ok=False,
            detail="Missing fixture sentinel header (expected in first 1024 chars).",
        )

    # Collect H2 headings present in the fixture (strip frontmatter if any).
    h2_re = re.compile(r"^## (.+)", re.MULTILINE)
    present = {m.group(1).strip() for m in h2_re.finditer(text)}

    missing = [s for s in required_sections if s not in present]
    if missing:
        return CheckResult(
            path=path,
            ok=False,
            detail=f"Missing required H2 section(s): {missing}",
        )

    return CheckResult(path=path, ok=True, detail="OK")


# ---------------------------------------------------------------------------
# Skill / agent fixture validator (delegates to rubric_binary_evaluator.py)
# ---------------------------------------------------------------------------


def validate_skill_agent_fixture(path: pathlib.Path) -> CheckResult:
    """Run rubric_binary_evaluator on a skill or agent fixture.

    Parses the JSON output; any FAIL verdict on a binary item is a failure.
    Returns CheckResult with ok=False if any FAIL verdict is found.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return CheckResult(path=path, ok=False, detail=f"Cannot read: {exc}")

    if not _has_sentinel(text):
        return CheckResult(
            path=path,
            ok=False,
            detail="Missing fixture sentinel header (expected in first 1024 chars).",
        )

    evaluator = REPO_ROOT / "scripts" / "rubric_binary_evaluator.py"
    try:
        result = subprocess.run(
            [sys.executable, str(evaluator), str(path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(path=path, ok=False, detail="Evaluator timed out.")
    except OSError as exc:
        return CheckResult(path=path, ok=False, detail=f"Evaluator error: {exc}")

    if result.returncode == 1:
        stderr_snippet = result.stderr[:200] if result.stderr else "(no stderr)"
        return CheckResult(
            path=path,
            ok=False,
            detail=f"Evaluator crashed (exit 1). stderr: {stderr_snippet}",
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return CheckResult(
            path=path,
            ok=False,
            detail=f"Evaluator output not valid JSON: {exc}",
        )

    # Each verdict value is a dict: {"verdict": "PASS"|"FAIL"|"NA", "evidence": {...}}
    verdicts: dict[str, dict[str, object]] = data.get("verdicts", {})
    fails = [item_id for item_id, v in verdicts.items() if isinstance(v, dict) and v.get("verdict") == "FAIL"]

    if fails:
        return CheckResult(
            path=path,
            ok=False,
            detail=f"Binary FAIL on items: {', '.join(sorted(fails))}",
        )

    return CheckResult(path=path, ok=True, detail="OK")


# ---------------------------------------------------------------------------
# Matrix completeness check
# ---------------------------------------------------------------------------


def check_matrix_complete(coverage_path: pathlib.Path, binary_ids: list[str]) -> CheckResult:
    """Verify that coverage_path's table contains every binary ID."""
    try:
        text = coverage_path.read_text(encoding="utf-8")
    except OSError as exc:
        return CheckResult(path=coverage_path, ok=False, detail=f"Cannot read: {exc}")

    id_re = re.compile(r"^\|\s+([A-Z]+(?:-[A-Z0-9a-z]+)+)\s+\|")
    covered = set()
    for line in text.splitlines():
        m = id_re.match(line)
        if m:
            covered.add(m.group(1))

    missing = [id_ for id_ in binary_ids if id_ not in covered]
    if missing:
        return CheckResult(
            path=coverage_path,
            ok=False,
            detail=f"Missing IDs: {', '.join(missing)}",
        )

    return CheckResult(path=coverage_path, ok=True, detail="OK")


# ---------------------------------------------------------------------------
# Fixture discovery
# ---------------------------------------------------------------------------


def discover_fixtures(fixture_dir: pathlib.Path) -> list[pathlib.Path]:
    """Return all skill, agent, and rule fixture files under fixture_dir."""
    patterns = ["**/*.skill.md", "**/*.agent.md", "**/*.rule.md"]
    fixtures: list[pathlib.Path] = []
    for pattern in patterns:
        fixtures.extend(sorted(fixture_dir.glob(pattern)))
    return fixtures


# ---------------------------------------------------------------------------
# Entry point helpers
# ---------------------------------------------------------------------------


def _halt(msg: str) -> None:
    """Print message to stderr and exit with code 1 (harness crash)."""
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def _report(results: list[CheckResult]) -> None:
    """Print a summary of check results to stdout."""
    passes = [r for r in results if r.ok]
    fails = [r for r in results if not r.ok]
    print(f"\nResults: {len(passes)} passed, {len(fails)} failed")
    if fails:
        print("\nFailed:")
        for r in fails:
            try:
                display_path = r.path.relative_to(REPO_ROOT)
            except ValueError:
                display_path = r.path
            print(f"  FAIL  {display_path}  —  {r.detail}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--verify-matrix-complete",
        action="store_true",
        help="Check rubric-coverage.md files cover all binary skill IDs.",
    )
    parser.add_argument(
        "--fixture-dir",
        type=pathlib.Path,
        default=REPO_ROOT / "tests" / "fixtures" / "scaffold_quality",
        help="Root directory containing scaffold quality fixture files.",
    )
    args = parser.parse_args()

    binary_ids = parse_binary_skill_ids(SCORING_RUBRIC_PATH)

    if args.verify_matrix_complete:
        results: list[CheckResult] = []
        for matrix_path in COVERAGE_MATRIX_PATHS:
            results.append(check_matrix_complete(matrix_path, binary_ids))
        _report(results)
        if any(not r.ok for r in results):
            sys.exit(2)
        sys.exit(0)

    # Default mode: validate fixture files.
    fixture_dir: pathlib.Path = args.fixture_dir
    if not fixture_dir.is_dir():
        _halt(f"Fixture directory not found: {fixture_dir}")

    fixtures = discover_fixtures(fixture_dir)
    if not fixtures:
        _halt(f"No fixture files found under {fixture_dir}")

    required_rule_sections = _derive_required_rule_sections(RULE_TEMPLATE_PATH)
    if not required_rule_sections:
        _halt("Could not derive required rule sections from rule-template.md.")

    results = []
    for fix_path in fixtures:
        if fix_path.name.endswith(".rule.md"):
            results.append(validate_rule_fixture(fix_path, required_rule_sections))
        else:
            results.append(validate_skill_agent_fixture(fix_path))

    _report(results)
    if any(not r.ok for r in results):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
