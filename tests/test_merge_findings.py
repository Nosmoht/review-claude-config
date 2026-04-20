"""Tests for scripts/merge_findings.py."""

from __future__ import annotations

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from merge_findings import (  # noqa: E402
    layer0_dedup,
    layer1_owner_weighted_grade,
    merge_directory,
    overlap_ratio,
    tokenize,
)


class TestTokenizer:
    def test_lowercase_words(self):
        assert tokenize("Hello, World!") == {"hello", "world"}

    def test_unicode_word_chars(self):
        # \w matches Unicode word chars under Python re default flags.
        assert "café" in tokenize("café au lait")

    def test_empty(self):
        assert tokenize("") == set()

    def test_deterministic(self):
        text = "The quick brown fox jumps over the lazy dog."
        assert tokenize(text) == tokenize(text)


class TestOverlap:
    def test_identical(self):
        assert overlap_ratio("a b c d e", "a b c d e") == 1.0

    def test_no_overlap(self):
        assert overlap_ratio("a b c", "d e f") == 0.0

    def test_partial(self):
        # {"a","b","c","d"} vs {"a","b","c","e"} → 3/4
        assert overlap_ratio("a b c d", "a b c e") == 0.75

    def test_empty_input(self):
        assert overlap_ratio("", "anything") == 0.0
        assert overlap_ratio("anything", "") == 0.0


class TestLayer0Dedup:
    def test_collapse_same_location_high_overlap(self):
        findings = [
            {
                "path": "skills/foo/SKILL.md",
                "line_range": "10-12",
                "evidence": "if needed, split the file",
                "dimension": "Clarity",
                "perspective": "clarity",
                "severity": "High",
            },
            {
                "path": "skills/foo/SKILL.md",
                "line_range": "10-12",
                "evidence": "if needed split the file",
                "dimension": "Context Engineering",
                "perspective": "correctness",
                "severity": "Medium",
            },
        ]
        merged = layer0_dedup(findings)
        assert len(merged) == 1
        assert set(merged[0]["dimensions"]) == {"Clarity", "Context Engineering"}
        assert set(merged[0]["perspectives"]) == {"clarity", "correctness"}
        assert merged[0]["severity"] == "High"

    def test_no_collapse_different_location(self):
        findings = [
            {"path": "a.md", "line_range": "10", "evidence": "x y z", "perspective": "clarity"},
            {"path": "b.md", "line_range": "10", "evidence": "x y z", "perspective": "correctness"},
        ]
        merged = layer0_dedup(findings)
        assert len(merged) == 2

    def test_no_collapse_low_overlap(self):
        findings = [
            {"path": "a.md", "line_range": "10", "evidence": "a b c d", "perspective": "clarity"},
            {"path": "a.md", "line_range": "10", "evidence": "w x y z", "perspective": "correctness"},
        ]
        merged = layer0_dedup(findings)
        assert len(merged) == 2


class TestOwnerWeightedGrade:
    def test_owner_dominates(self):
        certs = {
            "clarity": {"dimensions": {"Clarity": "A"}},
            "correctness": {"dimensions": {"Clarity": "C"}},
            "integration": {"dimensions": {"Clarity": "C"}},
        }
        # owner (clarity) gets weight 2: numerics = [95, 95, 75, 75] → avg 85 → B
        grade, source = layer1_owner_weighted_grade(certs, "Clarity")
        assert grade == "B"
        assert source == "clarity"

    def test_all_null_returns_F(self):
        certs = {"clarity": {"dimensions": {}}}
        grade, _ = layer1_owner_weighted_grade(certs, "Clarity")
        assert grade == "F"

    def test_safety_owner_is_integration(self):
        certs = {
            "clarity": {"dimensions": {"Safety": "F"}},
            "correctness": {"dimensions": {"Safety": "F"}},
            "integration": {"dimensions": {"Safety": "A"}},
        }
        # integration (owner, weight 2) + clarity + correctness (each weight 1)
        # numerics = [95, 95, 50, 50] → avg 72.5 → C
        grade, _ = layer1_owner_weighted_grade(certs, "Safety")
        assert grade == "C"


class TestMergeDirectory:
    def test_all_missing(self, tmp_path: pathlib.Path):
        result = merge_directory(tmp_path)
        assert result["status"] == "failure"
        assert result["degraded_mode"] is True
        assert set(result["missing_perspectives"]) == {
            "clarity",
            "correctness",
            "integration",
        }

    def test_one_missing_degraded(self, tmp_path: pathlib.Path):
        (tmp_path / "clarity.json").write_text(
            json.dumps(
                {
                    "perspective": "clarity",
                    "dimensions": {
                        "Clarity": "B",
                        "Completeness": "B",
                        "Prompt Engineering": "B",
                        "Context Engineering": "B",
                        "Goal Alignment": "B",
                        "Safety": "B",
                        "Metadata": "B",
                    },
                    "weighted_score": 85.0,
                    "artifact_frontmatter": {"allowed_tools": ["Read"]},
                    "findings": [],
                }
            )
        )
        (tmp_path / "correctness.json").write_text(
            json.dumps(
                {
                    "perspective": "correctness",
                    "dimensions": {
                        "Clarity": "A",
                        "Completeness": "B",
                        "Prompt Engineering": "B",
                        "Context Engineering": "B",
                        "Goal Alignment": "B",
                        "Safety": "B",
                        "Metadata": "B",
                    },
                    "weighted_score": 86.5,
                    "artifact_frontmatter": {"allowed_tools": ["Read"]},
                    "findings": [],
                }
            )
        )
        # integration.json intentionally missing
        result = merge_directory(tmp_path)
        assert result["status"] == "partial"
        assert result["degraded_mode"] is True
        assert result["missing_perspectives"] == ["integration"]
        # Dimensions owned by integration (Safety, Metadata) get F due to no data
        # from the owner. Clarity's B comes from clarity perspective.
        assert result["dimensions"]["Clarity"] in {"A", "B"}

    def test_deterministic_output(self, tmp_path: pathlib.Path):
        cert_body = json.dumps(
            {
                "perspective": "clarity",
                "dimensions": {
                    "Clarity": "B",
                    "Completeness": "B",
                    "Prompt Engineering": "B",
                    "Context Engineering": "B",
                    "Goal Alignment": "B",
                    "Safety": "B",
                    "Metadata": "B",
                },
                "weighted_score": 85.0,
                "artifact_frontmatter": {"allowed_tools": ["Read"]},
                "findings": [
                    {
                        "id": "WS-2:x.md:Clarity/v1",
                        "dimension": "Clarity",
                        "checklist_item": "WS-2",
                        "severity": "High",
                        "primary_focus": True,
                        "owner_conflict": False,
                        "hint_owner": None,
                        "path": "x.md",
                        "line_range": "5-6",
                        "evidence": "if needed, trim this",
                    }
                ],
            }
        )
        for name in ("clarity", "correctness", "integration"):
            (tmp_path / f"{name}.json").write_text(cert_body.replace('"clarity"', f'"{name}"'))
        r1 = merge_directory(tmp_path)
        r2 = merge_directory(tmp_path)
        assert r1 == r2
