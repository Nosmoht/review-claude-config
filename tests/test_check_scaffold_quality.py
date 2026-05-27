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


# ---------------------------------------------------------------------------
# In-process unit tests (coverage)
#
# Spec source: scripts/check_scaffold_quality.py — each function's docstring
# is the behavioral spec under test. The CLI/subprocess tests above verify
# end-to-end exit codes (feature-correctness); the tests below verify
# per-function predicates by direct import (code-correctness), so coverage
# tracking can attribute lines exercised. Both styles complement each other.
# ---------------------------------------------------------------------------

import importlib.util as _il_util  # noqa: E402

_SPEC = _il_util.spec_from_file_location(
    "check_scaffold_quality",
    REPO_ROOT / "scripts" / "check_scaffold_quality.py",
)
assert _SPEC is not None and _SPEC.loader is not None, (
    "spec import: failed to load check_scaffold_quality.py for in-process tests"
)
csq = _il_util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(csq)


# --- parse_binary_skill_ids -------------------------------------------------


def test_parse_binary_skill_ids_extracts_ge_25_ids() -> None:
    """parse_binary_skill_ids returns >=25 IDs from the committed scoring-rubric.

    Spec ref: scripts/check_scaffold_quality.py:parse_binary_skill_ids docstring
    — "Exits with code 1 if fewer than MIN_BINARY_IDS are found".
    """
    ids = csq.parse_binary_skill_ids(csq.SCORING_RUBRIC_PATH)
    assert len(ids) >= csq.MIN_BINARY_IDS, (
        f"spec parse_binary_skill_ids: expected >= {csq.MIN_BINARY_IDS} IDs "
        f"from real rubric, got {len(ids)}"
    )


def test_parse_binary_skill_ids_returns_id_shape() -> None:
    """Each returned ID matches the documented shape [A-Z]+(-[A-Z0-9a-z]+)+.

    Spec ref: scripts/check_scaffold_quality.py:parse_binary_skill_ids docstring
    — "Regex: ^|  <ID>  | where ID matches [A-Z]+(-[A-Z0-9a-z]+)+".
    """
    ids = csq.parse_binary_skill_ids(csq.SCORING_RUBRIC_PATH)
    bad = [i for i in ids if "-" not in i or not i.split("-")[0].isupper()]
    assert not bad, (
        f"spec parse_binary_skill_ids: all IDs must contain '-' and start "
        f"with upper-case prefix; bad: {bad}"
    )


def test_parse_binary_skill_ids_halts_on_degraded_rubric(tmp_path: Path) -> None:
    """Renaming the section heading triggers SystemExit(1) (RUBRIC_PARSE_DEGRADED).

    Spec ref: scripts/check_scaffold_quality.py:parse_binary_skill_ids docstring
    — "Exits with code 1 if fewer than MIN_BINARY_IDS are found".
    """
    real = csq.SCORING_RUBRIC_PATH.read_text(encoding="utf-8")
    degraded = real.replace(
        "### Binary-Evaluated Items", "### Skill-Rubric Items (renamed)"
    )
    tmp_rubric = tmp_path / "scoring-rubric.md"
    tmp_rubric.write_text(degraded, encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        csq.parse_binary_skill_ids(tmp_rubric)
    assert excinfo.value.code == 1, (
        "spec parse_binary_skill_ids: expected SystemExit(1) on degraded rubric, "
        f"got code={excinfo.value.code!r}"
    )


def test_parse_binary_skill_ids_halts_on_missing_file(tmp_path: Path) -> None:
    """OSError on rubric read path → SystemExit(1) via _halt.

    Spec ref: scripts/check_scaffold_quality.py:parse_binary_skill_ids
    — except OSError branch calls _halt.
    """
    missing = tmp_path / "nonexistent-rubric.md"
    with pytest.raises(SystemExit) as excinfo:
        csq.parse_binary_skill_ids(missing)
    assert excinfo.value.code == 1, (
        "spec parse_binary_skill_ids: expected SystemExit(1) on missing file, "
        f"got code={excinfo.value.code!r}"
    )


# --- _derive_required_rule_sections ----------------------------------------


def test_derive_required_rule_sections_returns_non_empty() -> None:
    """Real rule-template.md yields a non-empty section list.

    Spec ref: scripts/check_scaffold_quality.py:_derive_required_rule_sections
    docstring — extracts H2 headings from the Canonical Rule Structure block.
    """
    sections = csq._derive_required_rule_sections(csq.RULE_TEMPLATE_PATH)
    assert sections, (
        "spec _derive_required_rule_sections: expected non-empty H2 list "
        "from real rule-template.md"
    )


def test_derive_required_rule_sections_includes_scope() -> None:
    """Derived sections include the canonical '## Scope' heading.

    Spec ref: scripts/check_scaffold_quality.py:_derive_required_rule_sections
    — '## Scope' is the first canonical H2 in rule-template.md's fenced block.
    """
    sections = csq._derive_required_rule_sections(csq.RULE_TEMPLATE_PATH)
    assert "Scope" in sections, (
        f"spec _derive_required_rule_sections: expected 'Scope' in derived "
        f"sections, got {sections}"
    )


def test_derive_required_rule_sections_halts_on_missing_template(
    tmp_path: Path,
) -> None:
    """Missing template file → SystemExit(1) via _halt.

    Spec ref: scripts/check_scaffold_quality.py:_derive_required_rule_sections
    — except OSError branch calls _halt.
    """
    missing = tmp_path / "nonexistent-template.md"
    with pytest.raises(SystemExit) as excinfo:
        csq._derive_required_rule_sections(missing)
    assert excinfo.value.code == 1, (
        "spec _derive_required_rule_sections: expected SystemExit(1) on "
        f"missing file, got code={excinfo.value.code!r}"
    )


def test_derive_required_rule_sections_empty_when_no_canonical_block(
    tmp_path: Path,
) -> None:
    """Template without 'Canonical Rule Structure' section yields empty list.

    Spec ref: scripts/check_scaffold_quality.py:_derive_required_rule_sections
    — `found_section` remains False; loop never enters fence.
    """
    template = tmp_path / "rule-template.md"
    template.write_text("# Foo\n\n## Other Section\n\nNo canonical block.\n", encoding="utf-8")
    sections = csq._derive_required_rule_sections(template)
    assert sections == [], (
        "spec _derive_required_rule_sections: expected [] when no canonical "
        f"block exists, got {sections}"
    )


# --- _has_sentinel ----------------------------------------------------------


def test_has_sentinel_true_when_sentinel_within_1024() -> None:
    """Text starting with the sentinel returns True.

    Spec ref: scripts/check_scaffold_quality.py:_has_sentinel docstring
    — 'within the first 1024 chars'.
    """
    text = csq.FIXTURE_SENTINEL + " trailing content\n"
    assert csq._has_sentinel(text) is True, (
        "spec _has_sentinel: expected True when sentinel is at offset 0"
    )


def test_has_sentinel_false_when_absent() -> None:
    """Text without the sentinel returns False.

    Spec ref: scripts/check_scaffold_quality.py:_has_sentinel docstring.
    """
    text = "# Heading\n\nNo sentinel here.\n"
    assert csq._has_sentinel(text) is False, (
        "spec _has_sentinel: expected False when sentinel absent"
    )


def test_has_sentinel_false_when_past_1024_chars() -> None:
    """Sentinel placed after the 1024-char window returns False.

    Spec ref: scripts/check_scaffold_quality.py:_has_sentinel docstring
    — bounded read of first 1024 chars.
    """
    padding = "x" * 2000
    text = padding + csq.FIXTURE_SENTINEL
    assert csq._has_sentinel(text) is False, (
        "spec _has_sentinel: expected False when sentinel is past 1024-char window"
    )


# --- validate_rule_fixture --------------------------------------------------


def test_validate_rule_fixture_pass_on_clean_fixture() -> None:
    """Clean committed rule fixture passes validation against derived sections.

    Spec ref: scripts/check_scaffold_quality.py:validate_rule_fixture
    — returns ok=True when sentinel present and required H2s present.
    """
    required = csq._derive_required_rule_sections(csq.RULE_TEMPLATE_PATH)
    fixture = FIXTURE_ROOT / "scaffold-rule" / "maintenance" / "no-force-push.rule.md"
    result = csq.validate_rule_fixture(fixture, required)
    assert result.ok is True, (
        f"spec validate_rule_fixture: expected ok=True on clean fixture, "
        f"got detail={result.detail!r}"
    )


def test_validate_rule_fixture_fail_on_missing_sentinel(tmp_path: Path) -> None:
    """Fixture without sentinel header returns ok=False.

    Spec ref: scripts/check_scaffold_quality.py:validate_rule_fixture
    — 'Missing fixture sentinel header' detail branch.
    """
    fixture = tmp_path / "no-sentinel.rule.md"
    fixture.write_text("# Heading\n\n## Scope\n\nx\n## Edge Cases\n\ny\n", encoding="utf-8")
    result = csq.validate_rule_fixture(fixture, ["Scope", "Edge Cases"])
    assert result.ok is False and "sentinel" in result.detail.lower(), (
        "spec validate_rule_fixture: expected ok=False with sentinel detail, "
        f"got ok={result.ok}, detail={result.detail!r}"
    )


def test_validate_rule_fixture_fail_on_missing_section(tmp_path: Path) -> None:
    """Fixture missing a required H2 section returns ok=False.

    Spec ref: scripts/check_scaffold_quality.py:validate_rule_fixture
    — 'Missing required H2 section(s)' detail branch.
    """
    fixture = tmp_path / "missing-scope.rule.md"
    fixture.write_text(
        csq.FIXTURE_SENTINEL + "\n\n# Heading\n\n## Edge Cases\n\nbody\n",
        encoding="utf-8",
    )
    result = csq.validate_rule_fixture(fixture, ["Scope", "Edge Cases"])
    assert result.ok is False and "Scope" in result.detail, (
        "spec validate_rule_fixture: expected ok=False naming missing 'Scope', "
        f"got ok={result.ok}, detail={result.detail!r}"
    )


def test_validate_rule_fixture_fail_on_unreadable_path(tmp_path: Path) -> None:
    """Nonexistent fixture path returns ok=False with 'Cannot read' detail.

    Spec ref: scripts/check_scaffold_quality.py:validate_rule_fixture
    — except OSError branch.
    """
    missing = tmp_path / "nope.rule.md"
    result = csq.validate_rule_fixture(missing, ["Scope"])
    assert result.ok is False and "Cannot read" in result.detail, (
        "spec validate_rule_fixture: expected ok=False with 'Cannot read' on "
        f"missing path, got ok={result.ok}, detail={result.detail!r}"
    )


# --- validate_skill_agent_fixture ------------------------------------------


def test_validate_skill_agent_fixture_pass_on_clean_skill() -> None:
    """Clean committed skill fixture passes the binary-evaluator check.

    Spec ref: scripts/check_scaffold_quality.py:validate_skill_agent_fixture
    — returns ok=True when no FAIL verdicts emerge from rubric_binary_evaluator.
    """
    fixture = (
        FIXTURE_ROOT / "scaffold-skill" / "maintenance" / "lint-configs.skill.md"
    )
    result = csq.validate_skill_agent_fixture(fixture)
    assert result.ok is True, (
        "spec validate_skill_agent_fixture: expected ok=True on clean skill "
        f"fixture, got detail={result.detail!r}"
    )


def test_validate_skill_agent_fixture_fail_on_missing_sentinel(
    tmp_path: Path,
) -> None:
    """Skill fixture without sentinel returns ok=False before invoking evaluator.

    Spec ref: scripts/check_scaffold_quality.py:validate_skill_agent_fixture
    — 'Missing fixture sentinel header' detail branch.
    """
    fixture = tmp_path / "no-sentinel.skill.md"
    fixture.write_text("---\nname: foo\n---\n\n# Foo\n\nNo sentinel.\n", encoding="utf-8")
    result = csq.validate_skill_agent_fixture(fixture)
    assert result.ok is False and "sentinel" in result.detail.lower(), (
        "spec validate_skill_agent_fixture: expected ok=False with sentinel "
        f"detail, got ok={result.ok}, detail={result.detail!r}"
    )


def test_validate_skill_agent_fixture_fail_on_unreadable_path(
    tmp_path: Path,
) -> None:
    """Nonexistent skill fixture path returns ok=False with 'Cannot read'.

    Spec ref: scripts/check_scaffold_quality.py:validate_skill_agent_fixture
    — except OSError branch.
    """
    missing = tmp_path / "nope.skill.md"
    result = csq.validate_skill_agent_fixture(missing)
    assert result.ok is False and "Cannot read" in result.detail, (
        "spec validate_skill_agent_fixture: expected ok=False with 'Cannot read' "
        f"on missing path, got ok={result.ok}, detail={result.detail!r}"
    )


# --- check_matrix_complete --------------------------------------------------


def test_check_matrix_complete_pass_on_real_matrix() -> None:
    """Real scaffold-skill rubric-coverage.md covers all binary IDs.

    Spec ref: scripts/check_scaffold_quality.py:check_matrix_complete docstring
    — 'Verify that coverage_path's table contains every binary ID'.
    """
    ids = csq.parse_binary_skill_ids(csq.SCORING_RUBRIC_PATH)
    matrix = (
        REPO_ROOT / "skills" / "scaffold-skill" / "references" / "rubric-coverage.md"
    )
    result = csq.check_matrix_complete(matrix, ids)
    assert result.ok is True, (
        "spec check_matrix_complete: expected ok=True on real scaffold-skill "
        f"matrix, got detail={result.detail!r}"
    )


def test_check_matrix_complete_fail_on_missing_id(tmp_path: Path) -> None:
    """Matrix without a required ID returns ok=False naming the missing ID.

    Spec ref: scripts/check_scaffold_quality.py:check_matrix_complete
    — 'Missing IDs' detail branch.
    """
    matrix = tmp_path / "rubric-coverage.md"
    # Provide a matrix that covers FOO-1 but not BAR-2.
    matrix.write_text(
        "| ID | Status |\n|----|--------|\n| FOO-1 | covered |\n",
        encoding="utf-8",
    )
    result = csq.check_matrix_complete(matrix, ["FOO-1", "BAR-2"])
    assert result.ok is False and "BAR-2" in result.detail, (
        "spec check_matrix_complete: expected ok=False naming 'BAR-2', "
        f"got ok={result.ok}, detail={result.detail!r}"
    )


def test_check_matrix_complete_fail_on_unreadable_path(tmp_path: Path) -> None:
    """Nonexistent matrix path returns ok=False with 'Cannot read'.

    Spec ref: scripts/check_scaffold_quality.py:check_matrix_complete
    — except OSError branch.
    """
    missing = tmp_path / "nope.md"
    result = csq.check_matrix_complete(missing, ["FOO-1"])
    assert result.ok is False and "Cannot read" in result.detail, (
        "spec check_matrix_complete: expected ok=False with 'Cannot read' on "
        f"missing path, got ok={result.ok}, detail={result.detail!r}"
    )


# --- discover_fixtures ------------------------------------------------------


def test_discover_fixtures_empty_dir(tmp_path: Path) -> None:
    """Empty directory yields an empty fixture list.

    Spec ref: scripts/check_scaffold_quality.py:discover_fixtures docstring
    — globs for skill/agent/rule fixture suffixes.
    """
    assert csq.discover_fixtures(tmp_path) == [], (
        "spec discover_fixtures: expected [] on empty dir"
    )


def test_discover_fixtures_finds_all_three_suffixes(tmp_path: Path) -> None:
    """Populated dir returns one entry per recognised fixture suffix.

    Spec ref: scripts/check_scaffold_quality.py:discover_fixtures
    — patterns '**/*.skill.md', '**/*.agent.md', '**/*.rule.md'.
    """
    (tmp_path / "a.skill.md").write_text("x", encoding="utf-8")
    (tmp_path / "b.agent.md").write_text("x", encoding="utf-8")
    (tmp_path / "c.rule.md").write_text("x", encoding="utf-8")
    (tmp_path / "d.txt").write_text("x", encoding="utf-8")  # excluded suffix
    found = csq.discover_fixtures(tmp_path)
    names = sorted(p.name for p in found)
    assert names == ["a.skill.md", "b.agent.md", "c.rule.md"], (
        "spec discover_fixtures: expected exactly the three fixture suffixes, "
        f"got {names}"
    )


def test_discover_fixtures_on_real_fixture_tree() -> None:
    """Discovery on the committed fixture tree returns the 9 known fixtures.

    Spec ref: scripts/check_scaffold_quality.py:discover_fixtures
    — recurses via '**' glob across scaffold-skill/agent/rule subtrees.
    """
    found = csq.discover_fixtures(FIXTURE_ROOT)
    assert len(found) == 9, (
        f"spec discover_fixtures: expected 9 committed fixtures, got {len(found)}"
    )


# --- _halt / _report --------------------------------------------------------


def test_halt_exits_with_code_1(capsys: pytest.CaptureFixture[str]) -> None:
    """_halt writes ERROR-prefixed message to stderr and SystemExit(1).

    Spec ref: scripts/check_scaffold_quality.py:_halt docstring.
    """
    with pytest.raises(SystemExit) as excinfo:
        csq._halt("boom")
    captured = capsys.readouterr()
    assert excinfo.value.code == 1, (
        f"spec _halt: expected exit code 1, got {excinfo.value.code!r}"
    )
    assert "ERROR: boom" in captured.err, (
        f"spec _halt: expected 'ERROR: boom' in stderr, got {captured.err!r}"
    )


def test_report_prints_pass_and_fail_counts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """_report prints a summary line with pass/fail counts.

    Spec ref: scripts/check_scaffold_quality.py:_report docstring
    — 'Print a summary of check results to stdout'.
    """
    results = [
        csq.CheckResult(path=Path("a.md"), ok=True, detail="OK"),
        csq.CheckResult(path=Path("b.md"), ok=False, detail="boom"),
    ]
    csq._report(results)
    out = capsys.readouterr().out
    assert "1 passed, 1 failed" in out, (
        f"spec _report: expected '1 passed, 1 failed' in stdout, got {out!r}"
    )


def test_report_prints_failed_section_with_detail(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When failures exist, _report prints a 'Failed:' section listing each.

    Spec ref: scripts/check_scaffold_quality.py:_report — Failed block.
    """
    results = [
        csq.CheckResult(path=Path("/tmp/external.md"), ok=False, detail="nope"),
    ]
    csq._report(results)
    out = capsys.readouterr().out
    assert "Failed:" in out and "nope" in out, (
        f"spec _report: expected 'Failed:' + detail in stdout, got {out!r}"
    )
