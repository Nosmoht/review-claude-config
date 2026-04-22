"""Tests for scripts/merge_findings.py."""

from __future__ import annotations

import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from merge_findings import (  # noqa: E402
    BINARY_CAPS,
    BINARY_ITEM_IDS,
    ITEM_DIMENSION,
    NARRATIVE_PARENT_IDS,
    canonicalize_perspective_ids,
    layer0_dedup,
    layer1_5_binary_boundary_cap,
    layer1_owner_weighted_grade,
    load_binary_verdicts,
    merge_directory,
    overlap_ratio,
    synthesize_binary_findings,
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


def _verdicts_doc(**item_verdicts: str) -> dict:
    """Helper: build an evaluator-shaped verdicts document.

    Call as `_verdicts_doc(CLAR_1="FAIL", META_4="PASS")`. Underscores in
    keys are converted to hyphens to match the evaluator's item IDs. A
    per-item line/match evidence stub is attached (unique across items so
    Layer-0 dedup does NOT collapse distinct synthesized findings).
    """
    verdicts: dict[str, dict] = {}
    for idx, (key, verdict) in enumerate(item_verdicts.items()):
        item_id = key.replace("_", "-")
        verdicts[item_id] = {
            "verdict": verdict,
            "evidence": {"line": 100 + idx, "match": f"stub-{item_id}"},
        }
    return {
        "schema_version": 1,
        "artifact_path": "skills/foo/SKILL.md",
        "artifact_type": "skill",
        "verdicts": verdicts,
        "stats": {"pass": 0, "fail": 0, "na": 0, "runner_error": 0},
    }


class TestSynthesizeBinaryFindings:
    def test_fail_emits_high_severity_finding(self):
        doc = _verdicts_doc(CLAR_2="FAIL")
        findings = synthesize_binary_findings(doc, "skills/foo/SKILL.md")
        assert len(findings) == 1
        f = findings[0]
        assert f["severity"] == "High"
        assert f["primary_focus"] is True
        assert f["checklist_item"] == "CLAR-2"
        assert f["dimension"] == "Clarity"
        assert f["perspective"] == "binary-evaluator"
        assert f["id"] == "CLAR-2:skills/foo/SKILL.md:Clarity/v1"
        assert f["current"]
        assert f["recommended"]
        assert f["evidence"]

    def test_pass_and_na_emit_nothing(self):
        doc = _verdicts_doc(CLAR_1="PASS", CLAR_2="NA", CLAR_3="PASS")
        findings = synthesize_binary_findings(doc, "skills/foo/SKILL.md")
        assert findings == []

    def test_missing_doc_emits_nothing(self):
        assert synthesize_binary_findings(None, "skills/foo/SKILL.md") == []
        assert synthesize_binary_findings({}, "skills/foo/SKILL.md") == []

    def test_deterministic_order(self):
        doc = _verdicts_doc(RL_9b="FAIL", CLAR_2="FAIL", META_4="FAIL")
        r1 = synthesize_binary_findings(doc, "skills/foo/SKILL.md")
        r2 = synthesize_binary_findings(doc, "skills/foo/SKILL.md")
        assert [f["id"] for f in r1] == [f["id"] for f in r2]
        # Sorted by id.
        assert [f["id"] for f in r1] == sorted(f["id"] for f in r1)

    def test_item_without_dimension_skipped(self):
        # Construct a verdict for a made-up item that's not in ITEM_DIMENSION.
        doc = {"verdicts": {"MADE-UP-1": {"verdict": "FAIL", "evidence": {}}}}
        findings = synthesize_binary_findings(doc, "skills/foo/SKILL.md")
        assert findings == []

    def test_every_binary_item_has_dimension(self):
        """Regression: every item the evaluator emits must have a dimension
        binding. Otherwise synthesize_binary_findings silently drops it."""
        for item_id in BINARY_ITEM_IDS:
            assert item_id in ITEM_DIMENSION, f"{item_id} missing from ITEM_DIMENSION"


class TestLayer1_5BoundaryCaps:
    def _baseline_grades(self) -> dict[str, str]:
        return {
            "Clarity": "A",
            "Completeness": "A",
            "Prompt Engineering": "A",
            "Context Engineering": "A",
            "Goal Alignment": "A",
            "Safety": "A",
            "Metadata": "A",
        }

    def test_no_fails_no_caps(self):
        doc = _verdicts_doc(CLAR_1="PASS", RL_1b="PASS", META_4="PASS")
        grades, caps = layer1_5_binary_boundary_cap(self._baseline_grades(), doc)
        assert grades["Clarity"] == "A"
        assert grades["Safety"] == "A"
        assert grades["Metadata"] == "A"
        assert caps == []

    def test_clar_1_fail_caps_clarity_at_c(self):
        doc = _verdicts_doc(CLAR_1="FAIL")
        grades, caps = layer1_5_binary_boundary_cap(self._baseline_grades(), doc)
        assert grades["Clarity"] == "C"
        assert any(c["item"] == "CLAR-1" and c["applied"] for c in caps)

    def test_samp_2_fail_is_hard_f(self):
        doc = _verdicts_doc(SAMP_2="FAIL")
        grades, caps = layer1_5_binary_boundary_cap(self._baseline_grades(), doc)
        assert grades["Metadata"] == "F"
        assert any(c["item"] == "SAMP-2" and c["cap_grade"] == "F" for c in caps)

    def test_multiple_safety_fails_cap_once(self):
        doc = _verdicts_doc(SP_2b="FAIL", RL_1b="FAIL", RL_9b="FAIL")
        grades, caps = layer1_5_binary_boundary_cap(self._baseline_grades(), doc)
        assert grades["Safety"] == "C"
        # All three caps are recorded; only the first one actually changed
        # the grade (subsequent already saw "C"), but all three trigger.
        cap_items = {c["item"] for c in caps}
        assert cap_items == {"SP-2b", "RL-1b", "RL-9b"}
        applied = [c for c in caps if c["applied"]]
        assert len(applied) == 1  # first cap downgraded A→C; others already-C

    def test_cap_is_monotone_never_upgrades(self):
        grades = self._baseline_grades()
        grades["Clarity"] = "F"  # already worst; cap to C must NOT upgrade
        doc = _verdicts_doc(CLAR_1="FAIL")
        grades_out, caps = layer1_5_binary_boundary_cap(grades, doc)
        assert grades_out["Clarity"] == "F"
        # Cap recorded but not applied.
        assert caps and caps[0]["applied"] is False

    def test_idempotent_under_repeated_application(self):
        doc = _verdicts_doc(META_4="FAIL", SAMP_2="FAIL")
        grades = self._baseline_grades()
        g1, _ = layer1_5_binary_boundary_cap(grades, doc)
        g2, _ = layer1_5_binary_boundary_cap(g1, doc)
        assert g1 == g2

    def test_missing_verdicts_noop(self):
        grades = self._baseline_grades()
        g_out, caps = layer1_5_binary_boundary_cap(grades, None)
        assert g_out == grades
        assert caps == []

    def test_pe_fails_cap_pe_at_c(self):
        doc = _verdicts_doc(PE_1="FAIL", SAMP_1="FAIL")
        grades, caps = layer1_5_binary_boundary_cap(self._baseline_grades(), doc)
        assert grades["Prompt Engineering"] == "C"
        cap_items = {c["item"] for c in caps}
        assert {"PE-1", "SAMP-1"} <= cap_items

    def test_comp_w_caps_completeness_at_c(self):
        doc = _verdicts_doc(COMP_W="FAIL")
        grades, _ = layer1_5_binary_boundary_cap(self._baseline_grades(), doc)
        assert grades["Completeness"] == "C"

    def test_ah_2b_caps_completeness_at_c(self):
        doc = _verdicts_doc(AH_2b="FAIL")
        grades, _ = layer1_5_binary_boundary_cap(self._baseline_grades(), doc)
        assert grades["Completeness"] == "C"


class TestLoadBinaryVerdicts:
    def test_missing_file(self, tmp_path: pathlib.Path):
        doc, status = load_binary_verdicts(tmp_path)
        assert doc is None
        assert status == "missing"

    def test_malformed_file(self, tmp_path: pathlib.Path):
        (tmp_path / "binary_verdicts.json").write_text("{ this is not json")
        doc, status = load_binary_verdicts(tmp_path)
        assert doc is None
        assert status == "malformed"

    def test_crashed_stub(self, tmp_path: pathlib.Path):
        (tmp_path / "binary_verdicts.json").write_text(
            json.dumps({"status": "crashed", "verdicts": {}})
        )
        doc, status = load_binary_verdicts(tmp_path)
        assert status == "crashed"
        assert doc == {"status": "crashed", "verdicts": {}}

    def test_runner_error_signal(self, tmp_path: pathlib.Path):
        (tmp_path / "binary_verdicts.json").write_text(
            json.dumps(
                {
                    "verdicts": {"META-4": {"verdict": "PASS", "evidence": {}}},
                    "stats": {"pass": 1, "fail": 0, "na": 0, "runner_error": 2},
                }
            )
        )
        doc, status = load_binary_verdicts(tmp_path)
        assert status == "error"
        assert doc is not None  # verdicts still usable for Layer 1.5

    def test_happy_path(self, tmp_path: pathlib.Path):
        (tmp_path / "binary_verdicts.json").write_text(
            json.dumps(
                {
                    "verdicts": {"META-4": {"verdict": "PASS", "evidence": {}}},
                    "stats": {"pass": 1, "fail": 0, "na": 0, "runner_error": 0},
                }
            )
        )
        doc, status = load_binary_verdicts(tmp_path)
        assert status == "present"
        assert doc["verdicts"]["META-4"]["verdict"] == "PASS"


class TestMergeWithBinaryVerdicts:
    def _write_baseline_certs(self, session_dir: pathlib.Path, clar_grade: str = "A") -> None:
        """Write 3 perspective certs where every dimension starts A."""
        for name in ("clarity", "correctness", "integration"):
            (session_dir / f"{name}.json").write_text(
                json.dumps(
                    {
                        "perspective": name,
                        "dimensions": {
                            "Clarity": clar_grade,
                            "Completeness": "A",
                            "Prompt Engineering": "A",
                            "Context Engineering": "A",
                            "Goal Alignment": "A",
                            "Safety": "A",
                            "Metadata": "A",
                        },
                        "weighted_score": 95.0,
                        "artifact_frontmatter": {
                            "allowed_tools": ["Read"],
                            "path": "skills/foo/SKILL.md",
                        },
                        "findings": [],
                    }
                )
            )

    def test_happy_path_with_fail_verdicts(self, tmp_path: pathlib.Path):
        self._write_baseline_certs(tmp_path)
        (tmp_path / "binary_verdicts.json").write_text(
            json.dumps(_verdicts_doc(CLAR_2="FAIL", META_4="PASS"))
        )
        result = merge_directory(tmp_path)
        assert result["binary_evaluator_status"] == "present"
        assert result["dimensions"]["Clarity"] == "C"
        # One High-severity synthesized finding.
        binary_findings = [
            f for f in result["findings"] if f.get("perspective") == "binary-evaluator"
        ]
        assert len(binary_findings) == 1
        assert binary_findings[0]["checklist_item"] == "CLAR-2"
        # boundary_caps_applied is recorded.
        assert result["boundary_caps_applied"]
        assert any(c["item"] == "CLAR-2" for c in result["boundary_caps_applied"])
        # binary_verdicts_applied echoes back verdicts.
        assert result["binary_verdicts_applied"]["CLAR-2"] == "FAIL"

    def test_missing_binary_verdicts_preserves_perspective_findings(
        self, tmp_path: pathlib.Path
    ):
        # Perspectives emit a CLAR-2 finding; with no binary_verdicts.json
        # the merge must keep it (can't trust binary evaluator gone silent).
        for name in ("clarity", "correctness", "integration"):
            (tmp_path / f"{name}.json").write_text(
                json.dumps(
                    {
                        "perspective": name,
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
                                "id": f"CLAR-2:x.md:Clarity/{name}",
                                "dimension": "Clarity",
                                "checklist_item": "CLAR-2",
                                "severity": "High",
                                "primary_focus": True,
                                "owner_conflict": False,
                                "hint_owner": None,
                                "path": "x.md",
                                "line_range": "10",
                                "evidence": "bare pronoun here",
                            }
                        ],
                    }
                )
            )
        result = merge_directory(tmp_path)
        assert result["binary_evaluator_status"] == "missing"
        # Perspective CLAR-2 findings NOT dropped (fail-safe: evaluator silent).
        clar_findings = [
            f for f in result["findings"] if f.get("checklist_item") == "CLAR-2"
        ]
        assert clar_findings  # at least one survived
        # No caps applied when verdicts missing.
        assert result["boundary_caps_applied"] == []
        assert result["dropped_perspective_findings"] == 0

    def test_malformed_binary_verdicts_preserves_perspective_findings(
        self, tmp_path: pathlib.Path
    ):
        self._write_baseline_certs(tmp_path)
        (tmp_path / "binary_verdicts.json").write_text("{ not valid json")
        result = merge_directory(tmp_path)
        assert result["binary_evaluator_status"] == "malformed"
        assert result["boundary_caps_applied"] == []

    def test_crashed_stub_no_caps(self, tmp_path: pathlib.Path):
        self._write_baseline_certs(tmp_path)
        (tmp_path / "binary_verdicts.json").write_text(
            json.dumps({"status": "crashed", "verdicts": {}})
        )
        result = merge_directory(tmp_path)
        assert result["binary_evaluator_status"] == "crashed"
        assert result["boundary_caps_applied"] == []

    def test_perspective_findings_on_binary_items_dropped(
        self, tmp_path: pathlib.Path
    ):
        # Perspective emits CLAR-2 finding; evaluator also says FAIL.
        # Expected: perspective finding dropped, only synthesized one remains.
        (tmp_path / "clarity.json").write_text(
            json.dumps(
                {
                    "perspective": "clarity",
                    "dimensions": {
                        "Clarity": "A",
                        "Completeness": "A",
                        "Prompt Engineering": "A",
                        "Context Engineering": "A",
                        "Goal Alignment": "A",
                        "Safety": "A",
                        "Metadata": "A",
                    },
                    "weighted_score": 95.0,
                    "artifact_frontmatter": {"allowed_tools": ["Read"]},
                    "findings": [
                        {
                            "id": "CLAR-2:hand-crafted/persp/v1",
                            "dimension": "Clarity",
                            "checklist_item": "CLAR-2",
                            "severity": "High",
                            "primary_focus": True,
                            "owner_conflict": False,
                            "hint_owner": None,
                            "path": "skills/foo/SKILL.md",
                            "line_range": "89",
                            "evidence": "bare pronoun perspective-side",
                        },
                        # A non-binary finding that must survive (PD-1 is not
                        # in BINARY_ITEM_IDS or NARRATIVE_PARENT_IDS).
                        {
                            "id": "PD-1:hand-crafted/pd/v1",
                            "dimension": "Context Engineering",
                            "checklist_item": "PD-1",
                            "severity": "Medium",
                            "primary_focus": True,
                            "owner_conflict": False,
                            "hint_owner": None,
                            "path": "skills/foo/SKILL.md",
                            "line_range": "120",
                            "evidence": "stable knowledge inlined in body",
                        },
                    ],
                }
            )
        )
        for name in ("correctness", "integration"):
            (tmp_path / f"{name}.json").write_text(
                json.dumps(
                    {
                        "perspective": name,
                        "dimensions": {
                            "Clarity": "A",
                            "Completeness": "A",
                            "Prompt Engineering": "A",
                            "Context Engineering": "A",
                            "Goal Alignment": "A",
                            "Safety": "A",
                            "Metadata": "A",
                        },
                        "weighted_score": 95.0,
                        "artifact_frontmatter": {
                            "allowed_tools": ["Read"],
                            "path": "skills/foo/SKILL.md",
                        },
                        "findings": [],
                    }
                )
            )
        (tmp_path / "binary_verdicts.json").write_text(
            json.dumps(_verdicts_doc(CLAR_2="FAIL"))
        )
        result = merge_directory(tmp_path)
        # Perspective CLAR-2 dropped, synthesized CLAR-2 present.
        clar2 = [f for f in result["findings"] if f.get("checklist_item") == "CLAR-2"]
        assert len(clar2) == 1
        assert clar2[0]["perspective"] == "binary-evaluator"
        # PD-1 finding (non-binary, non-narrative-parent) preserved.
        pd1 = [f for f in result["findings"] if f.get("checklist_item") == "PD-1"]
        assert len(pd1) == 1
        # Dropped count is 1 (perspective CLAR-2).
        assert result["dropped_perspective_findings"] == 1

    def test_narrative_parent_findings_also_dropped(self, tmp_path: pathlib.Path):
        # Perspective emits RL-1 (narrative parent of RL-1b). Under the new
        # wiring contract these should also be dropped in favor of the
        # deterministic RL-1b evaluation.
        (tmp_path / "integration.json").write_text(
            json.dumps(
                {
                    "perspective": "integration",
                    "dimensions": {
                        "Clarity": "A",
                        "Completeness": "A",
                        "Prompt Engineering": "A",
                        "Context Engineering": "A",
                        "Goal Alignment": "A",
                        "Safety": "A",
                        "Metadata": "A",
                    },
                    "weighted_score": 95.0,
                    "artifact_frontmatter": {"allowed_tools": ["Read"]},
                    "findings": [
                        {
                            "id": "RL-1:persp/v1",
                            "dimension": "Safety",
                            "checklist_item": "RL-1",
                            "severity": "High",
                            "primary_focus": True,
                            "owner_conflict": False,
                            "hint_owner": None,
                            "path": "skills/foo/SKILL.md",
                            "line_range": "100",
                            "evidence": "narrative parent RL-1 here",
                        }
                    ],
                }
            )
        )
        for name in ("clarity", "correctness"):
            (tmp_path / f"{name}.json").write_text(
                json.dumps(
                    {
                        "perspective": name,
                        "dimensions": {
                            "Clarity": "A",
                            "Completeness": "A",
                            "Prompt Engineering": "A",
                            "Context Engineering": "A",
                            "Goal Alignment": "A",
                            "Safety": "A",
                            "Metadata": "A",
                        },
                        "weighted_score": 95.0,
                        "artifact_frontmatter": {"allowed_tools": ["Read"]},
                        "findings": [],
                    }
                )
            )
        (tmp_path / "binary_verdicts.json").write_text(
            json.dumps(_verdicts_doc(RL_1b="PASS"))
        )
        result = merge_directory(tmp_path)
        # Narrative RL-1 perspective finding dropped.
        rl1 = [f for f in result["findings"] if f.get("checklist_item") == "RL-1"]
        assert len(rl1) == 0
        assert result["dropped_perspective_findings"] == 1

    def test_binary_finding_id_is_deterministic(self, tmp_path: pathlib.Path):
        self._write_baseline_certs(tmp_path)
        (tmp_path / "binary_verdicts.json").write_text(
            json.dumps(_verdicts_doc(CLAR_3="FAIL", COMP_W="FAIL"))
        )
        r1 = merge_directory(tmp_path)
        r2 = merge_directory(tmp_path)
        # Binary finding IDs should be identical across runs.
        ids1 = sorted(f["id"] for f in r1["findings"] if f.get("perspective") == "binary-evaluator")
        ids2 = sorted(f["id"] for f in r2["findings"] if f.get("perspective") == "binary-evaluator")
        assert ids1 == ids2
        assert "CLAR-3:skills/foo/SKILL.md:Clarity/v1" in ids1
        assert "COMP-W:skills/foo/SKILL.md:Completeness/v1" in ids1


class TestCanonicalizePerspectiveIds:
    """Dim-pin rewrite for perspective findings — issue #70."""

    def test_ws4_safety_rewritten_to_clarity(self):
        finding = {
            "id": "WS-4:skills/foo/SKILL.md:Safety/clarity",
            "dimension": "Safety",
            "checklist_item": "WS-4",
            "path": "skills/foo/SKILL.md",
            "severity": "High",
        }
        result = canonicalize_perspective_ids([finding])
        assert len(result) == 1
        assert result[0]["dimension"] == "Clarity"
        assert result[0]["id"] == "WS-4:skills/foo/SKILL.md:Clarity/v1"

    def test_unpinned_item_passes_through(self):
        finding = {
            "id": "PD-1:skills/foo/SKILL.md:Context Engineering/clarity",
            "dimension": "Context Engineering",
            "checklist_item": "PD-1",
            "path": "skills/foo/SKILL.md",
        }
        result = canonicalize_perspective_ids([finding])
        assert result[0]["id"] == finding["id"]
        assert result[0]["dimension"] == finding["dimension"]

    def test_finding_without_path_passes_through(self):
        finding = {
            "id": "WS-4:???/v1",
            "dimension": "Safety",
            "checklist_item": "WS-4",
            "path": "",
        }
        result = canonicalize_perspective_ids([finding])
        assert result[0]["id"] == finding["id"]  # unchanged — path empty

    def test_runa_runb_flip_converges(self):
        runA = {
            "id": "WS-4:skills/rv/SKILL.md:Clarity/rA",
            "dimension": "Clarity",
            "checklist_item": "WS-4",
            "path": "skills/rv/SKILL.md",
        }
        runB = {
            "id": "WS-4:skills/rv/SKILL.md:Safety/rB",
            "dimension": "Safety",
            "checklist_item": "WS-4",
            "path": "skills/rv/SKILL.md",
        }
        # After canonicalise, both IDs converge to the pinned form.
        A = canonicalize_perspective_ids([runA])[0]
        B = canonicalize_perspective_ids([runB])[0]
        assert A["id"] == B["id"]
        assert A["id"] == "WS-4:skills/rv/SKILL.md:Clarity/v1"


class TestNarrativeParentDropExtended:
    """Issue #70: WS-2, WS-4, RD-5 perspective findings drop when binary
    evaluator is present."""

    def _baseline_certs(self, session_dir: pathlib.Path) -> None:
        for name in ("clarity", "correctness", "integration"):
            (session_dir / f"{name}.json").write_text(
                json.dumps(
                    {
                        "perspective": name,
                        "dimensions": {
                            "Clarity": "A",
                            "Completeness": "A",
                            "Prompt Engineering": "A",
                            "Context Engineering": "A",
                            "Goal Alignment": "A",
                            "Safety": "A",
                            "Metadata": "A",
                        },
                        "weighted_score": 95.0,
                        "artifact_frontmatter": {"allowed_tools": ["Read"]},
                        "findings": (
                            [
                                {
                                    "id": f"WS-2:x.md:Clarity/{name}",
                                    "dimension": "Clarity",
                                    "checklist_item": "WS-2",
                                    "severity": "Medium",
                                    "primary_focus": True,
                                    "path": "x.md",
                                    "line_range": "12",
                                    "evidence": "narrative WS-2",
                                },
                                {
                                    "id": f"WS-4:x.md:Safety/{name}",
                                    "dimension": "Safety",
                                    "checklist_item": "WS-4",
                                    "severity": "High",
                                    "primary_focus": True,
                                    "path": "x.md",
                                    "line_range": "30",
                                    "evidence": "narrative WS-4",
                                },
                                {
                                    "id": f"RD-5:x.md:Clarity/{name}",
                                    "dimension": "Clarity",
                                    "checklist_item": "RD-5",
                                    "severity": "Medium",
                                    "primary_focus": True,
                                    "path": "x.md",
                                    "line_range": "50",
                                    "evidence": "narrative RD-5",
                                },
                            ]
                            if name == "clarity"
                            else []
                        ),
                    }
                )
            )

    def test_ws2_ws4_rd5_all_dropped_when_binary_present(self, tmp_path: pathlib.Path):
        self._baseline_certs(tmp_path)
        (tmp_path / "binary_verdicts.json").write_text(
            json.dumps(_verdicts_doc())  # all-PASS verdicts
        )
        result = merge_directory(tmp_path)
        items_present = {f.get("checklist_item") for f in result["findings"]}
        assert "WS-2" not in items_present
        assert "WS-4" not in items_present
        assert "RD-5" not in items_present
        assert result["dropped_perspective_findings"] == 3

    def test_ws2_ws4_rd5_preserved_when_binary_missing(self, tmp_path: pathlib.Path):
        self._baseline_certs(tmp_path)
        # No binary_verdicts.json → apply_caps=False → narrative drop skipped.
        result = merge_directory(tmp_path)
        items_present = {f.get("checklist_item") for f in result["findings"]}
        assert "WS-2" in items_present
        assert "WS-4" in items_present
        assert "RD-5" in items_present


class TestLayer1_5ClarityCapsForIssue70:
    """WS-2b and RD-5b grade-boundary caps on Clarity — issue #70."""

    def test_ws_2b_fail_caps_clarity_at_c(self):
        graces = {"Clarity": "A"}
        doc = _verdicts_doc(WS_2b="FAIL")
        result, caps = layer1_5_binary_boundary_cap(graces, doc)
        assert result["Clarity"] == "C"
        assert any(c["item"] == "WS-2b" and c["applied"] for c in caps)

    def test_rd_5b_fail_caps_clarity_at_c(self):
        graces = {"Clarity": "A"}
        doc = _verdicts_doc(RD_5b="FAIL")
        result, caps = layer1_5_binary_boundary_cap(graces, doc)
        assert result["Clarity"] == "C"
        assert any(c["item"] == "RD-5b" and c["applied"] for c in caps)

    def test_ws_2b_pass_no_cap(self):
        graces = {"Clarity": "A"}
        doc = _verdicts_doc(WS_2b="PASS")
        result, caps = layer1_5_binary_boundary_cap(graces, doc)
        assert result["Clarity"] == "A"
        # WS-2b entry present but applied=False.
        for c in caps:
            if c["item"] == "WS-2b":
                assert c["applied"] is False


def _perspective_cert(perspective: str, findings: list[dict]) -> str:
    """Helper: build a full perspective certificate JSON body for merge tests."""
    return json.dumps(
        {
            "perspective": perspective,
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
            "findings": findings,
        }
    )


def _write_perspectives(tmp_path: pathlib.Path, findings_by_persp: dict[str, list[dict]]) -> None:
    """Helper: write three perspective certs + a present-but-empty binary verdicts doc."""
    for name in ("clarity", "correctness", "integration"):
        (tmp_path / f"{name}.json").write_text(
            _perspective_cert(name, findings_by_persp.get(name, []))
        )
    (tmp_path / "binary_verdicts.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "artifact_path": "skills/foo/SKILL.md",
                "artifact_type": "skill",
                "verdicts": {},
                "stats": {"pass": 0, "fail": 0, "na": 0, "runner_error": 0},
            }
        )
    )


class TestAdvisoryDemote:
    """Issue #72 — advisory perspective findings are demoted to Low severity.

    Deterministic-subset findings (checklist_item in BINARY_ITEM_IDS or
    NARRATIVE_PARENT_IDS) stay dropped. Advisory findings (anything outside
    the subset) at High/Medium are forced to Low so the H+M convergence
    gate is satisfiable by construction.
    """

    def _advisory_finding(self, severity: str, item: str = "WS-1") -> dict:
        return {
            "id": f"{item}:x.md:Clarity/v1",
            "dimension": "Clarity",
            "checklist_item": item,
            "severity": severity,
            "primary_focus": True,
            "owner_conflict": False,
            "hint_owner": None,
            "path": "x.md",
            "line_range": "10-12",
            "evidence": f"advisory evidence for {item} {severity}",
        }

    def test_advisory_high_demoted_to_low(self, tmp_path: pathlib.Path):
        _write_perspectives(
            tmp_path, {"clarity": [self._advisory_finding("High", "WS-1")]}
        )
        result = merge_directory(tmp_path)
        assert result["demoted_perspective_findings"] == 1
        # Finding is preserved in the merged cert, not dropped.
        kept = [f for f in result["findings"] if f.get("checklist_item") == "WS-1"]
        assert len(kept) == 1
        assert kept[0]["severity"] == "Low"

    def test_advisory_medium_demoted_to_low(self, tmp_path: pathlib.Path):
        _write_perspectives(
            tmp_path, {"correctness": [self._advisory_finding("Medium", "OF-3")]}
        )
        result = merge_directory(tmp_path)
        assert result["demoted_perspective_findings"] == 1
        kept = [f for f in result["findings"] if f.get("checklist_item") == "OF-3"]
        assert len(kept) == 1
        assert kept[0]["severity"] == "Low"

    def test_advisory_low_unchanged(self, tmp_path: pathlib.Path):
        _write_perspectives(
            tmp_path, {"integration": [self._advisory_finding("Low", "RF-1")]}
        )
        result = merge_directory(tmp_path)
        assert result["demoted_perspective_findings"] == 0
        kept = [f for f in result["findings"] if f.get("checklist_item") == "RF-1"]
        assert len(kept) == 1
        assert kept[0]["severity"] == "Low"

    def test_deterministic_still_dropped(self, tmp_path: pathlib.Path):
        # BINARY item — dropped (not demoted).
        binary_finding = self._advisory_finding("High", "META-1a")
        # NARRATIVE_PARENT item — also dropped.
        parent_finding = self._advisory_finding("High", "SP-2")
        _write_perspectives(
            tmp_path,
            {"clarity": [binary_finding], "integration": [parent_finding]},
        )
        result = merge_directory(tmp_path)
        assert result["dropped_perspective_findings"] == 2
        assert result["demoted_perspective_findings"] == 0
        items = {f.get("checklist_item") for f in result["findings"]}
        assert "META-1a" not in items
        assert "SP-2" not in items

    def test_mixed_drop_and_demote_counters(self, tmp_path: pathlib.Path):
        findings = [
            self._advisory_finding("High", "META-1a"),  # drop (binary)
            self._advisory_finding("High", "WS-2"),  # drop (narrative parent)
            self._advisory_finding("High", "WS-1"),  # demote (advisory High)
            self._advisory_finding("Medium", "OF-4"),  # demote (advisory Medium)
            self._advisory_finding("Low", "PD-1"),  # keep as-is
        ]
        _write_perspectives(tmp_path, {"clarity": findings})
        result = merge_directory(tmp_path)
        assert result["dropped_perspective_findings"] == 2
        assert result["demoted_perspective_findings"] == 2
        items = {f.get("checklist_item") for f in result["findings"]}
        assert items == {"WS-1", "OF-4", "PD-1"}
        # All kept findings end up at Low severity.
        for f in result["findings"]:
            assert f["severity"] == "Low"

    def test_fail_safe_no_demote_when_evaluator_missing(self, tmp_path: pathlib.Path):
        # Write perspectives WITHOUT binary_verdicts.json — triggers fail-safe
        # (apply_caps=False). Neither drop nor demote fires; perspective
        # severities pass through unchanged.
        for name in ("clarity", "correctness", "integration"):
            (tmp_path / f"{name}.json").write_text(
                _perspective_cert(
                    name,
                    [self._advisory_finding("High", "WS-1")] if name == "clarity" else [],
                )
            )
        result = merge_directory(tmp_path)
        assert result["binary_evaluator_status"] == "missing"
        assert result["dropped_perspective_findings"] == 0
        assert result["demoted_perspective_findings"] == 0
        kept = [f for f in result["findings"] if f.get("checklist_item") == "WS-1"]
        assert len(kept) == 1
        assert kept[0]["severity"] == "High"  # untouched under fail-safe

    def test_offspec_severity_case_insensitive_demote(self, tmp_path: pathlib.Path):
        # Haiku may emit 'HIGH' or 'high'; demote handles case-insensitively.
        findings = [
            {**self._advisory_finding("Medium", "OF-3"), "severity": "HIGH"},
            {**self._advisory_finding("Medium", "OF-4"), "severity": "high"},
            {**self._advisory_finding("Medium", "PE-4"), "severity": "Medium"},
        ]
        _write_perspectives(tmp_path, {"clarity": findings})
        result = merge_directory(tmp_path)
        assert result["demoted_perspective_findings"] == 3
        for f in result["findings"]:
            assert f["severity"] == "Low"

    def test_multi_perspective_advisory_agreement_preserved(self, tmp_path: pathlib.Path):
        # Three perspectives emit the same advisory High on the same line.
        # After demote-then-dedup the collapsed finding is Low severity, but
        # the `perspectives` list should preserve the 3-way agreement signal.
        f = {
            "id": "WS-1:x.md:Clarity/v1",
            "dimension": "Clarity",
            "checklist_item": "WS-1",
            "severity": "High",
            "primary_focus": True,
            "owner_conflict": False,
            "hint_owner": None,
            "path": "x.md",
            "line_range": "10-12",
            "evidence": "identical advisory evidence",
        }
        _write_perspectives(
            tmp_path,
            {"clarity": [dict(f)], "correctness": [dict(f)], "integration": [dict(f)]},
        )
        result = merge_directory(tmp_path)
        assert result["demoted_perspective_findings"] == 3
        kept = [g for g in result["findings"] if g.get("checklist_item") == "WS-1"]
        assert len(kept) == 1
        assert kept[0]["severity"] == "Low"
        # 3-way agreement is preserved regardless of order of demote vs dedup.
        assert len(kept[0].get("perspectives", [])) == 3

    def test_synthesized_binary_findings_not_demoted(self, tmp_path: pathlib.Path):
        # Binary verdicts producing synthesized High findings must not be
        # demoted — they are added AFTER the perspective loop.
        for name in ("clarity", "correctness", "integration"):
            (tmp_path / f"{name}.json").write_text(_perspective_cert(name, []))
        (tmp_path / "binary_verdicts.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "artifact_path": "skills/foo/SKILL.md",
                    "artifact_type": "skill",
                    "verdicts": {
                        "CLAR-1": {
                            "verdict": "FAIL",
                            "evidence": {"line": 42, "match": "ambiguous"},
                        }
                    },
                    "stats": {"pass": 0, "fail": 1, "na": 0, "runner_error": 0},
                }
            )
        )
        result = merge_directory(tmp_path)
        assert result["demoted_perspective_findings"] == 0
        high = [f for f in result["findings"] if f.get("severity") == "High"]
        assert any(f.get("checklist_item") == "CLAR-1" for f in high)
