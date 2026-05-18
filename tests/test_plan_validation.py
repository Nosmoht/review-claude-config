"""Tests for bin/validate-plan-references.sh (issue #204)."""

from __future__ import annotations

import pathlib
import subprocess

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "bin" / "validate-plan-references.sh"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "plan-validation"


def _run(plan: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SCRIPT), str(plan)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )


def test_valid_plan_exits_zero():
    result = _run(FIXTURES / "valid-plan.md")
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert result.stdout.strip() == "", f"expected empty stdout, got {result.stdout!r}"


def test_invalid_plan_exits_one():
    result = _run(FIXTURES / "invalid-plan.md")
    assert result.returncode == 1, (
        f"expected exit 1, got {result.returncode}; stdout={result.stdout!r}"
    )


def test_invalid_plan_lists_each_failure_on_stdout():
    result = _run(FIXTURES / "invalid-plan.md")
    assert result.returncode == 1
    assert "MISSING-PATH: scripts/merge-policy.yaml" in result.stdout
    assert "MISSING-PATH: bin/non-existent-tool.sh" in result.stdout
    assert "MISSING-PATH: docs/missing-doc.md" in result.stdout
    assert 'MISSING-ANCHOR: §"Section That Does Not Exist" in CLAUDE.md' in result.stdout
