"""Tests for scripts/check_scaffold_quality.py.

Spec source: .work/issue-161/plan.md §Deliverable D — regression-test harness.
Each test corresponds to a named plan predicate; test name cites the predicate.

AC mapping (from plan.md §AC mapping):
  AC-1  — --verify-matrix-complete exits 0; every binary ID covered in skill/agent matrices.
  AC-2a — default mode exits 0; all 9 fixtures pass.
  AC-3  — harness exits non-zero on mutated fixture.
  R2-D  — make validate passes (covered by CI; not re-tested here).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS = REPO_ROOT / "scripts" / "check_scaffold_quality.py"
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "scaffold_quality"


def _run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    """Run the harness with the given extra arguments."""
    return subprocess.run(
        [sys.executable, str(HARNESS), *args],
        capture_output=True,
        text=True,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# AC-2a: default mode passes all clean fixtures
# ---------------------------------------------------------------------------


def test_harness_passes_on_clean_fixtures() -> None:
    """plan.md §Deliverable D: default mode exits 0 on all 9 clean fixtures.

    Spec ref: AC-2a — 'python3 scripts/check_scaffold_quality.py (exit 0)'.
    """
    result = _run(["--fixture-dir", str(FIXTURE_ROOT)])
    assert result.returncode == 0, (
        f"spec AC-2a: expected exit 0, got {result.returncode}. stdout={result.stdout!r}"
    )


# ---------------------------------------------------------------------------
# AC-3: harness exits non-zero on mutated skill fixture (CLAR-3 violation)
# ---------------------------------------------------------------------------


def test_harness_fails_on_mutated_skill_fixture(tmp_path: Path) -> None:
    """plan.md §Deliverable D: exit 2 after appending a CLAR-3 violation pattern.

    CLAR-3 binary check: if 'halt' or 'abort' appears in the body without
    recovery guidance within 200 chars, it's flagged as FAIL.
    Spec ref: AC-3 — 'test_harness_fails_on_mutated_*'.
    """
    # Copy clean fixtures to tmp_path.
    shutil.copytree(FIXTURE_ROOT, tmp_path / "scaffold_quality")
    skill_fixture = (
        tmp_path / "scaffold_quality" / "scaffold-skill" / "maintenance" / "lint-configs.skill.md"
    )
    # Append a CLAR-3 trigger: 'abort' without recovery guidance.
    content = skill_fixture.read_text(encoding="utf-8")
    # Add a bare 'abort' keyword that CLAR-3 checks for (no recovery within 200 chars).
    poisoned = content + "\n\n## Edge case\n\nIf unrecoverable, simply abort the task.\n"
    skill_fixture.write_text(poisoned, encoding="utf-8")

    result = _run(["--fixture-dir", str(tmp_path / "scaffold_quality")])
    assert result.returncode == 2, (
        f"spec AC-3: expected exit 2 on CLAR-3 violation, got {result.returncode}. "
        f"stdout={result.stdout!r}"
    )


# ---------------------------------------------------------------------------
# AC-3: harness exits non-zero on mutated rule fixture (missing H2 section)
# ---------------------------------------------------------------------------


def test_harness_fails_on_mutated_rule_fixture(tmp_path: Path) -> None:
    """plan.md §Deliverable D: exit 2 after removing a required H2 section from rule fixture.

    Spec ref: AC-3 — 'test_harness_fails_on_mutated_*'.
    """
    shutil.copytree(FIXTURE_ROOT, tmp_path / "scaffold_quality")
    rule_fixture = (
        tmp_path / "scaffold_quality" / "scaffold-rule" / "maintenance" / "no-force-push.rule.md"
    )
    content = rule_fixture.read_text(encoding="utf-8")
    # Remove the '## Scope' section (required per rule-template.md).
    lines = content.splitlines()
    filtered = [ln for ln in lines if not ln.startswith("## Scope")]
    rule_fixture.write_text("\n".join(filtered), encoding="utf-8")

    result = _run(["--fixture-dir", str(tmp_path / "scaffold_quality")])
    assert result.returncode == 2, (
        f"spec AC-3: expected exit 2 on missing H2 section, got {result.returncode}. "
        f"stdout={result.stdout!r}"
    )


# ---------------------------------------------------------------------------
# Exit 1 on missing fixture directory (harness crash)
# ---------------------------------------------------------------------------


def test_harness_crashes_on_missing_fixture_dir(tmp_path: Path) -> None:
    """plan.md §Deliverable D: exit 1 when fixture dir does not exist.

    Spec ref: AC-3 — 'test_harness_crashes_on_missing_fixture_dir'.
    """
    nonexistent = tmp_path / "no_such_dir"
    result = _run(["--fixture-dir", str(nonexistent)])
    assert result.returncode == 1, (
        f"spec crash-path: expected exit 1 on missing dir, got {result.returncode}"
    )


# ---------------------------------------------------------------------------
# AC-1: --verify-matrix-complete exits 0 on clean matrices
# ---------------------------------------------------------------------------


def test_verify_matrix_complete_independent_of_runtime() -> None:
    """plan.md §Deliverable D: --verify-matrix-complete exits 0 on clean matrices.

    Directly verifies that every binary ID from scoring-rubric.md appears in
    scaffold-skill and scaffold-agent rubric-coverage.md files.
    Spec ref: AC-1 — 'python3 scripts/check_scaffold_quality.py --verify-matrix-complete (exit 0)'.
    """
    result = _run(["--verify-matrix-complete"])
    assert result.returncode == 0, (
        f"spec AC-1: expected exit 0, got {result.returncode}. stdout={result.stdout!r}"
    )


# ---------------------------------------------------------------------------
# Parser loud-fail on rubric drift (RUBRIC_PARSE_DEGRADED)
# ---------------------------------------------------------------------------


def test_parser_fails_loud_on_rubric_drift(tmp_path: Path) -> None:
    """plan.md §Deliverable D: parser exits 1 (RUBRIC_PARSE_DEGRADED) on degraded rubric.

    Synthesises a temp scoring-rubric.md that renames '### Binary-Evaluated Items'
    to a different heading, so the parser finds zero binary IDs and must halt.
    Spec ref: 'test_parser_fails_loud_on_rubric_drift' — asserts exit 1 (loud fail).
    """
    real_rubric = REPO_ROOT / "skills" / "review-claude-config" / "references" / "scoring-rubric.md"
    real_content = real_rubric.read_text(encoding="utf-8")
    # Replace the key subheading so the parser finds no binary items.
    degraded = real_content.replace(
        "### Binary-Evaluated Items", "### Skill-Rubric Items (renamed)"
    )
    tmp_rubric = tmp_path / "scoring-rubric.md"
    tmp_rubric.write_text(degraded, encoding="utf-8")

    # Run check with the substituted rubric by patching via a tiny wrapper.
    wrapper = tmp_path / "check_wrapper.py"
    wrapper.write_text(
        textwrap.dedent(f"""\
            import sys
            sys.path.insert(0, {str(REPO_ROOT / "scripts")!r})
            import check_scaffold_quality as m
            m.SCORING_RUBRIC_PATH = m.pathlib.Path({str(tmp_rubric)!r})
            m.COVERAGE_MATRIX_PATHS = [
                m.REPO_ROOT / "skills" / "scaffold-skill" / "references" / "rubric-coverage.md",
                m.REPO_ROOT / "skills" / "scaffold-agent" / "references" / "rubric-coverage.md",
            ]
            m.main()
        """),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(wrapper), "--verify-matrix-complete"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, (
        f"spec rubric-drift: expected exit 1 (RUBRIC_PARSE_DEGRADED), got {result.returncode}. "
        f"stderr={result.stderr!r}"
    )
    assert "RUBRIC_PARSE_DEGRADED" in result.stderr, (
        f"spec rubric-drift: expected 'RUBRIC_PARSE_DEGRADED' in stderr, got {result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Rule fixture validator tracks rule-template.md source of truth
# ---------------------------------------------------------------------------


def test_validate_rule_fixture_derives_from_template(tmp_path: Path) -> None:
    """plan.md §Deliverable D: structural validator tracks rule-template.md.

    Mutates a copy of rule-template.md by adding a new '## Examples' section
    to the Canonical Rule Structure block, then runs the harness on a rule
    fixture that lacks '## Examples'. Asserts that the harness exits 2 (FAIL).

    Spec ref: 'test_validate_rule_fixture_derives_from_template'.
    """
    real_template = REPO_ROOT / "skills" / "scaffold-rule" / "references" / "rule-template.md"
    template_content = real_template.read_text(encoding="utf-8")

    # Inject '## Examples' into the fenced code block under Canonical Rule Structure.
    # The block ends with the closing ```, so we insert before it.
    injected = template_content.replace(
        "## Edge Cases\n\n",
        "## Edge Cases\n\n## Examples\n\n",
        1,
    )
    tmp_template = tmp_path / "rule-template.md"
    tmp_template.write_text(injected, encoding="utf-8")

    # Copy fixtures into tmp so we can run against the mutated template.
    shutil.copytree(FIXTURE_ROOT, tmp_path / "scaffold_quality")

    wrapper = tmp_path / "check_wrapper2.py"
    wrapper.write_text(
        textwrap.dedent(f"""\
            import sys
            sys.path.insert(0, {str(REPO_ROOT / "scripts")!r})
            import check_scaffold_quality as m
            m.RULE_TEMPLATE_PATH = m.pathlib.Path({str(tmp_template)!r})
            m.main()
        """),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(wrapper), "--fixture-dir", str(tmp_path / "scaffold_quality")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2, (
        f"spec template-sot: expected exit 2 when fixture lacks '## Examples', "
        f"got {result.returncode}. stdout={result.stdout!r}"
    )
