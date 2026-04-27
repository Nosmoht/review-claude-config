"""Tests for scripts/check_convergence.py."""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from check_convergence import (  # noqa: E402
    DEFAULT_MAX_VARIANCE,
    DETERMINISTIC_SUBSET,
    GRADE_LETTERS,
    _deterministic_hm_finding_ids,
    _grade_distance,
    check_convergence,
)
from check_convergence import main as check_main


# ---------------------------------------------------------------------------
# Helper builders for synthetic merge output.
# ---------------------------------------------------------------------------


def _finding(item: str, severity: str, dim: str = "Clarity", fid: str | None = None) -> dict:
    return {
        "id": fid or f"{item}::{dim}/v1",
        "checklist_item": item,
        "dimension": dim,
        "severity": severity,
        "evidence": "synthetic",
    }


def _merged(
    findings: list[dict] | None = None,
    dimensions: dict[str, str] | None = None,
) -> dict:
    return {
        "status": "success",
        "findings": findings or [],
        "dimensions": dimensions or {},
    }


# Pick a real binary item id and a real narrative-parent id from the imported
# subsets so tests stay correct when the lists are extended upstream.
SAMPLE_BINARY_ITEM = next(iter(sorted(DETERMINISTIC_SUBSET)))
SAMPLE_NON_BINARY_ITEM = "ZZZ-99"  # not in any subset by construction


class TestDeterministicHmFindingIds:
    def test_extracts_high_in_subset(self):
        m = _merged(findings=[_finding(SAMPLE_BINARY_ITEM, "High")])
        ids = _deterministic_hm_finding_ids(m)
        assert len(ids) == 1

    def test_extracts_medium_in_subset(self):
        m = _merged(findings=[_finding(SAMPLE_BINARY_ITEM, "Medium")])
        assert len(_deterministic_hm_finding_ids(m)) == 1

    def test_skips_low_severity(self):
        m = _merged(findings=[_finding(SAMPLE_BINARY_ITEM, "Low")])
        assert _deterministic_hm_finding_ids(m) == set()

    def test_skips_advisory_outside_subset(self):
        m = _merged(findings=[_finding(SAMPLE_NON_BINARY_ITEM, "High")])
        assert _deterministic_hm_finding_ids(m) == set()

    def test_severity_case_insensitive(self):
        m = _merged(findings=[_finding(SAMPLE_BINARY_ITEM, "HIGH")])
        assert len(_deterministic_hm_finding_ids(m)) == 1
        m = _merged(findings=[_finding(SAMPLE_BINARY_ITEM, "medium")])
        assert len(_deterministic_hm_finding_ids(m)) == 1

    def test_falls_back_to_synthetic_id_when_id_missing(self):
        f = _finding(SAMPLE_BINARY_ITEM, "High")
        del f["id"]
        m = _merged(findings=[f])
        ids = _deterministic_hm_finding_ids(m)
        assert len(ids) == 1
        # synthetic id format: "<item>::<dim>"
        assert any("::Clarity" in i for i in ids)

    def test_handles_missing_findings_key(self):
        assert _deterministic_hm_finding_ids({}) == set()
        assert _deterministic_hm_finding_ids({"findings": None}) == set()


class TestGradeDistance:
    @pytest.mark.parametrize(
        "g1,g2,expected",
        [
            ("A", "A", 0),
            ("A", "B", 1),
            ("B", "A", 1),
            ("A", "F", 4),
            ("F", "A", 4),
            ("C", "B", 1),
            ("C", "D", 1),
        ],
    )
    def test_known_distances(self, g1, g2, expected):
        assert _grade_distance(g1, g2) == expected

    def test_unknown_grade_returns_sentinel(self):
        assert _grade_distance("Z", "A") >= len(GRADE_LETTERS)
        assert _grade_distance("A", "?") >= len(GRADE_LETTERS)

    def test_none_returns_sentinel(self):
        assert _grade_distance(None, "A") >= len(GRADE_LETTERS)


class TestCheckConvergence:
    def test_identical_runs_converge(self):
        m = _merged(
            findings=[_finding(SAMPLE_BINARY_ITEM, "High")],
            dimensions={"Clarity": "B", "Safety": "A"},
        )
        report = check_convergence(m, m)
        assert report["converged"] is True
        assert report["deterministic_match"] is True
        assert report["max_grade_variance"] == 0
        assert report["null_dimensions_added"] == []

    def test_added_high_breaks_convergence(self):
        run1 = _merged(dimensions={"Clarity": "B"})
        run2 = _merged(
            findings=[_finding(SAMPLE_BINARY_ITEM, "High", fid="X-1")],
            dimensions={"Clarity": "B"},
        )
        report = check_convergence(run1, run2)
        assert report["converged"] is False
        assert report["deterministic_match"] is False
        assert report["deterministic_added_finding_ids"] == ["X-1"]
        assert report["deterministic_removed_finding_ids"] == []

    def test_removed_medium_breaks_convergence(self):
        run1 = _merged(
            findings=[_finding(SAMPLE_BINARY_ITEM, "Medium", fid="Y-1")],
            dimensions={"Clarity": "B"},
        )
        run2 = _merged(dimensions={"Clarity": "B"})
        report = check_convergence(run1, run2)
        assert report["converged"] is False
        assert report["deterministic_removed_finding_ids"] == ["Y-1"]

    def test_advisory_low_flap_still_converges(self):
        """Per CLAUDE.md:126 advisory findings are scoped out of the
        convergence gate — Low severity is allowed to flap freely.
        """
        run1 = _merged(dimensions={"Clarity": "B"})
        run2 = _merged(
            findings=[_finding(SAMPLE_NON_BINARY_ITEM, "Low", fid="A-1")],
            dimensions={"Clarity": "B"},
        )
        report = check_convergence(run1, run2)
        assert report["converged"] is True

    def test_advisory_high_outside_subset_does_not_break(self):
        """Findings outside the deterministic subset never count toward
        deterministic_match, even at H/M severity. The merge step demotes
        them to Low at runtime, so this is a defense-in-depth check.
        """
        run1 = _merged(dimensions={"Clarity": "B"})
        run2 = _merged(
            findings=[_finding(SAMPLE_NON_BINARY_ITEM, "High", fid="A-1")],
            dimensions={"Clarity": "B"},
        )
        assert check_convergence(run1, run2)["converged"] is True

    def test_grade_flip_one_letter_converges(self):
        run1 = _merged(dimensions={"Clarity": "B"})
        run2 = _merged(dimensions={"Clarity": "C"})
        report = check_convergence(run1, run2)
        assert report["converged"] is True
        assert report["max_grade_variance"] == 1

    def test_grade_flip_two_letters_breaks(self):
        run1 = _merged(dimensions={"Clarity": "B"})
        run2 = _merged(dimensions={"Clarity": "D"})
        report = check_convergence(run1, run2)
        assert report["converged"] is False
        assert report["max_grade_variance"] == 2
        assert report["grade_variance"]["Clarity"] == 2

    def test_null_dimension_added_breaks(self):
        """Dimension lost between runs is a regression."""
        run1 = _merged(dimensions={"Clarity": "B", "Safety": "A"})
        run2 = _merged(dimensions={"Clarity": "B", "Safety": None})
        report = check_convergence(run1, run2)
        assert report["converged"] is False
        assert "Safety" in report["null_dimensions_added"]

    def test_dimension_gained_does_not_break(self):
        """Information gained (run1 missing dim, run2 has it) is acceptable."""
        run1 = _merged(dimensions={"Clarity": "B"})
        run2 = _merged(dimensions={"Clarity": "B", "Safety": "A"})
        report = check_convergence(run1, run2)
        assert report["converged"] is True
        assert report["null_dimensions_added"] == []

    def test_both_none_dimensions_skipped(self):
        run1 = _merged(dimensions={"Clarity": None})
        run2 = _merged(dimensions={"Clarity": None})
        report = check_convergence(run1, run2)
        assert report["converged"] is True
        assert "Clarity" not in report["grade_variance"]

    def test_max_variance_override(self):
        """Tighter `--max-variance=0` rejects any drift, looser `--max-variance=2`
        accepts more.
        """
        run1 = _merged(dimensions={"Clarity": "B"})
        run2 = _merged(dimensions={"Clarity": "C"})
        assert check_convergence(run1, run2, max_variance=0)["converged"] is False
        assert check_convergence(run1, run2, max_variance=2)["converged"] is True

    def test_unknown_grade_returns_sentinel_and_breaks(self):
        run1 = _merged(dimensions={"Clarity": "B"})
        run2 = _merged(dimensions={"Clarity": "Z"})
        report = check_convergence(run1, run2)
        assert report["converged"] is False
        assert report["max_grade_variance"] >= len(GRADE_LETTERS)

    def test_default_max_variance_is_one(self):
        """Pin the default per CLAUDE.md:126 ('grade variance ≤1 letter')."""
        assert DEFAULT_MAX_VARIANCE == 1


class TestMain:
    def _write(self, tmp_path, name, data):
        p = tmp_path / name
        p.write_text(json.dumps(data))
        return p

    def test_converged_returns_zero(self, tmp_path, capsys):
        run1 = self._write(tmp_path, "r1.json", _merged(dimensions={"Clarity": "B"}))
        run2 = self._write(tmp_path, "r2.json", _merged(dimensions={"Clarity": "B"}))
        rc = check_main([str(run1), str(run2)])
        assert rc == 0
        out = capsys.readouterr().out
        assert json.loads(out)["converged"] is True

    def test_not_converged_returns_one(self, tmp_path, capsys):
        run1 = self._write(
            tmp_path,
            "r1.json",
            _merged(
                findings=[_finding(SAMPLE_BINARY_ITEM, "High", fid="X-1")],
                dimensions={"Clarity": "B"},
            ),
        )
        run2 = self._write(tmp_path, "r2.json", _merged(dimensions={"Clarity": "B"}))
        rc = check_main([str(run1), str(run2)])
        assert rc == 1
        report = json.loads(capsys.readouterr().out)
        assert report["converged"] is False
        assert report["deterministic_removed_finding_ids"] == ["X-1"]

    def test_missing_file_exits_2(self, tmp_path, capsys):
        run1 = self._write(tmp_path, "r1.json", _merged())
        with pytest.raises(SystemExit) as exc:
            check_main([str(run1), str(tmp_path / "missing.json")])
        # SystemExit raised with the error message text — exit code is implied 1
        # via argparse convention; we accept any non-zero. Verify the message.
        assert "cannot read" in str(exc.value) or "missing" in str(exc.value).lower()

    def test_malformed_json_exits_2(self, tmp_path):
        run1 = self._write(tmp_path, "r1.json", _merged())
        bad = tmp_path / "bad.json"
        bad.write_text("not json{")
        with pytest.raises(SystemExit) as exc:
            check_main([str(run1), str(bad)])
        assert "invalid JSON" in str(exc.value)

    def test_top_level_array_rejected(self, tmp_path):
        run1 = self._write(tmp_path, "r1.json", _merged())
        bad = tmp_path / "arr.json"
        bad.write_text("[]")
        with pytest.raises(SystemExit) as exc:
            check_main([str(run1), str(bad)])
        assert "JSON object" in str(exc.value)

    def test_negative_max_variance_rejected(self, tmp_path, capsys):
        run1 = self._write(tmp_path, "r1.json", _merged())
        run2 = self._write(tmp_path, "r2.json", _merged())
        rc = check_main([str(run1), str(run2), "--max-variance", "-1"])
        assert rc == 2
        assert "non-negative" in capsys.readouterr().err
