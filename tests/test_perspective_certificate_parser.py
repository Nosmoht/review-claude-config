"""Tests for scripts/perspective_certificate_parser.py.

The parser is the boundary between an agent's Markdown certificate and the
JSON shape consumed by ``scripts/merge_findings.py:merge_directory``. It is
exercised by ``tests/test_perspective_replay.py`` for full pipeline replay
and here for unit-level coverage of edge cases that real captures may not
exhibit.
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from perspective_certificate_parser import (  # noqa: E402
    VALID_DIMENSIONS,
    parse_certificate,
)

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "agent_outputs"
FINDING_SCHEMA = json.loads(
    (
        REPO_ROOT
        / "skills"
        / "review-claude-config"
        / "references"
        / "schemas"
        / "finding.schema.json"
    ).read_text(encoding="utf-8")
)


# ---------------------------------------------------------------------------
# Captured-fixture round trips
# ---------------------------------------------------------------------------


class TestCapturedFixtures:
    """The two pilot snapshots came from real Haiku-class dispatches; the
    parser must round-trip them without losing structure.
    """

    def test_clear_antecedent_01_parses(self):
        md = (FIXTURES / "clear_antecedent_01" / "clarity.md").read_text(encoding="utf-8")
        cert = parse_certificate(md, artifact_path="skills/scaffold-skill/SKILL.md")
        assert cert["perspective"] == "clarity"
        assert cert["error"] is None
        # All seven named dimensions captured (Overall is dropped by design).
        assert set(cert["dimensions"]) == set(VALID_DIMENSIONS)
        # Captured cert had nine findings spanning High/Medium/Low.
        assert len(cert["findings"]) == 9
        severities = {f["severity"] for f in cert["findings"]}
        assert severities == {"High", "Medium", "Low"}

    def test_clear_antecedent_02_parses(self):
        md = (FIXTURES / "clear_antecedent_02" / "clarity.md").read_text(encoding="utf-8")
        cert = parse_certificate(md, artifact_path="skills/review-skill/SKILL.md")
        assert cert["perspective"] == "clarity"
        assert len(cert["findings"]) == 6
        # Confirm specific finding ids canonicalised by parser
        first = cert["findings"][0]
        assert first["checklist_item"] == "RD-5"
        assert first["severity"] == "High"
        assert first["primary_focus"] is True
        assert first["owner_conflict"] is False
        assert first["hint_owner"] is None

    def test_artifact_path_stamps_on_every_finding(self):
        md = (FIXTURES / "clear_antecedent_01" / "clarity.md").read_text(encoding="utf-8")
        cert = parse_certificate(md, artifact_path="skills/foo/SKILL.md")
        for f in cert["findings"]:
            assert f["path"] == "skills/foo/SKILL.md"

    def test_high_findings_validate_against_schema(self):
        """Every High-severity finding emitted by the parser must satisfy the
        finding.schema.json contract for High findings (current/recommended
        required). This is the boundary contract the apply pipeline relies on.
        """
        validator = Draft202012Validator(FINDING_SCHEMA)
        for case in ("clear_antecedent_01", "clear_antecedent_02"):
            md = (FIXTURES / case / "clarity.md").read_text(encoding="utf-8")
            cert = parse_certificate(md, artifact_path=f"skills/{case}/SKILL.md")
            for f in cert["findings"]:
                if f["severity"] != "High":
                    continue
                errors = sorted(validator.iter_errors(f), key=lambda e: e.path)
                assert not errors, f"{case} finding {f.get('checklist_item')} fails schema: {errors}"

    def test_idempotent(self):
        md = (FIXTURES / "clear_antecedent_01" / "clarity.md").read_text(encoding="utf-8")
        a = parse_certificate(md, artifact_path="x.md")
        b = parse_certificate(md, artifact_path="x.md")
        assert a == b


# ---------------------------------------------------------------------------
# Synthesised structural edge cases
# ---------------------------------------------------------------------------


CERT_MINIMAL = """\
### Perspective
clarity

### Certificate
| Dimension | Grade | Justification |
|-----------|-------|---------------|
| Clarity | A | nothing to flag |
| Completeness | A | covers all items |
| Prompt Engineering | A | role + constraints clear |
| Context Engineering | A | JIT loads correct |
| Goal Alignment | A | scoped tightly |
| Safety | A | tools minimal |
| Metadata | A | frontmatter complete |
| Overall | A | weighted A |

### Findings

(none)
"""


class TestStructuralEdgeCases:
    def test_minimal_cert_no_findings(self):
        cert = parse_certificate(CERT_MINIMAL, artifact_path="x.md")
        assert cert["dimensions"]["Clarity"] == "A"
        assert cert["findings"] == []
        assert cert["error"] is None

    def test_prose_preamble_tolerated(self):
        cert = parse_certificate(
            "Now I'll evaluate the artifact.\n\n" + CERT_MINIMAL,
            artifact_path="x.md",
        )
        assert cert["perspective"] == "clarity"
        assert cert["dimensions"]["Clarity"] == "A"

    def test_overall_dropped_from_dimensions(self):
        cert = parse_certificate(CERT_MINIMAL, artifact_path="x.md")
        assert "Overall" not in cert["dimensions"]
        assert set(cert["dimensions"]) == set(VALID_DIMENSIONS)

    def test_off_spec_grade_dropped(self):
        # 'Critical' is not in the A-F enum and must not appear.
        broken = CERT_MINIMAL.replace("| Clarity | A |", "| Clarity | Critical |")
        cert = parse_certificate(broken, artifact_path="x.md")
        assert "Clarity" not in cert["dimensions"]

    def test_error_shortcut(self):
        text = "### ERROR\nmissing shared context"
        cert = parse_certificate(text, artifact_path="x.md")
        assert cert["error"] == "missing shared context"
        assert cert["findings"] == []
        assert cert["dimensions"] == {}

    def test_empty_markdown(self):
        cert = parse_certificate("", artifact_path="x.md")
        # No sections present — no error reported, no dimensions, no findings.
        assert cert["error"] is None
        assert cert["dimensions"] == {}
        assert cert["findings"] == []
        assert cert["perspective"] is None

    def test_perspective_override(self):
        cert = parse_certificate(
            "### ERROR\nfailed",
            artifact_path="x.md",
            perspective_override="clarity",
        )
        assert cert["perspective"] == "clarity"


# ---------------------------------------------------------------------------
# Header-metadata parsing
# ---------------------------------------------------------------------------


CERT_WITH_FINDING = """\
### Perspective
clarity

### Certificate
| Dimension | Grade | Justification |
|-----------|-------|---------------|
| Clarity | C | flagged |
| Completeness | B | ok |
| Prompt Engineering | B | ok |
| Context Engineering | B | ok |
| Goal Alignment | B | ok |
| Safety | B | ok |
| Metadata | B | ok |
| Overall | B | weighted |

### Findings

#### Finding (severity: {sev}, dimension: Clarity, checklist_item: WS-1, primary_focus: {pf}, owner_conflict: {oc}, hint_owner: {ho})
Evidence: literal quote here
Why it matters: tooling cannot infer the order
Validation: re-check after edit
Current: ambiguous step
Recommended: explicit step
"""


class TestFindingHeaderParsing:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("High", "High"),
            ("HIGH", "High"),
            ("high", "High"),
            ("Medium", "Medium"),
            ("Low", "Low"),
        ],
    )
    def test_severity_normalisation(self, raw, expected):
        text = CERT_WITH_FINDING.format(sev=raw, pf="true", oc="false", ho="null")
        cert = parse_certificate(text, artifact_path="x.md")
        assert cert["findings"][0]["severity"] == expected

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("true", True),
            ("True", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("no", False),
        ],
    )
    def test_bool_parsing(self, raw, expected):
        text = CERT_WITH_FINDING.format(sev="High", pf=raw, oc=raw, ho="null")
        cert = parse_certificate(text, artifact_path="x.md")
        f = cert["findings"][0]
        assert f["primary_focus"] is expected
        assert f["owner_conflict"] is expected

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("null", None),
            ("None", None),
            ("correctness", "correctness"),
            ("integration", "integration"),
        ],
    )
    def test_hint_owner_parsing(self, raw, expected):
        text = CERT_WITH_FINDING.format(sev="High", pf="true", oc="true", ho=raw)
        cert = parse_certificate(text, artifact_path="x.md")
        assert cert["findings"][0]["hint_owner"] == expected

    def test_id_canonicalisation(self):
        text = CERT_WITH_FINDING.format(sev="High", pf="true", oc="false", ho="null")
        cert = parse_certificate(text, artifact_path="skills/foo/SKILL.md")
        assert cert["findings"][0]["id"] == "WS-1:skills/foo/SKILL.md:Clarity/v1"


# ---------------------------------------------------------------------------
# Body-field parsing
# ---------------------------------------------------------------------------


CERT_MULTILINE_BODY = """\
### Perspective
clarity

### Certificate
| Dimension | Grade | Justification |
|-----------|-------|---------------|
| Clarity | C | flagged |
| Completeness | B | ok |
| Prompt Engineering | B | ok |
| Context Engineering | B | ok |
| Goal Alignment | B | ok |
| Safety | B | ok |
| Metadata | B | ok |
| Overall | B | weighted |

### Findings

#### Finding (severity: High, dimension: Clarity, checklist_item: WS-1, primary_focus: true, owner_conflict: false, hint_owner: null)
Evidence: line one
  continued on line two
Why it matters: short
Validation: short
Current: original line one
original line two
original line three
Recommended: replacement line one

(blank line in the middle)

replacement line three

---

#### Finding (severity: Low, dimension: Metadata, checklist_item: META-1a, primary_focus: false, owner_conflict: true, hint_owner: integration)
Evidence: brief
Why it matters: brief
Validation: brief
Current: brief
Recommended: brief
"""


class TestBodyParsing:
    def test_multiline_evidence_preserved(self):
        cert = parse_certificate(CERT_MULTILINE_BODY, artifact_path="x.md")
        f = cert["findings"][0]
        assert "line one" in f["evidence"]
        assert "continued on line two" in f["evidence"]

    def test_multiline_current_preserved(self):
        cert = parse_certificate(CERT_MULTILINE_BODY, artifact_path="x.md")
        f = cert["findings"][0]
        assert "original line one" in f["current"]
        assert "original line two" in f["current"]
        assert "original line three" in f["current"]

    def test_multiline_recommended_preserved(self):
        cert = parse_certificate(CERT_MULTILINE_BODY, artifact_path="x.md")
        f = cert["findings"][0]
        assert "replacement line one" in f["recommended"]
        assert "(blank line in the middle)" in f["recommended"]
        assert "replacement line three" in f["recommended"]

    def test_separator_does_not_leak_into_body(self):
        cert = parse_certificate(CERT_MULTILINE_BODY, artifact_path="x.md")
        f = cert["findings"][0]
        # The trailing `---` must be stripped before reaching field bodies.
        assert "---" not in f["recommended"]
        assert "---" not in f["current"]

    def test_two_findings_separated(self):
        cert = parse_certificate(CERT_MULTILINE_BODY, artifact_path="x.md")
        assert len(cert["findings"]) == 2
        assert cert["findings"][0]["checklist_item"] == "WS-1"
        assert cert["findings"][1]["checklist_item"] == "META-1a"

    def test_perspective_carried_into_findings(self):
        cert = parse_certificate(CERT_MULTILINE_BODY, artifact_path="x.md")
        for f in cert["findings"]:
            assert f["perspective"] == "clarity"

    def test_indented_label_recovered_within_threshold(self):
        """Haiku occasionally indents labels under nested list items or
        post-blockquote — up to 4 spaces. Treating those as continuation
        silently swallows the field. The parser tolerates leading whitespace
        ≤4 spaces; beyond that the line is markdown code-block content and
        is preserved as continuation.
        """
        text = """\
### Perspective
clarity

### Certificate
| Dimension | Grade | Justification |
|-----------|-------|---------------|
| Clarity | C | flagged |
| Completeness | B | ok |
| Prompt Engineering | B | ok |
| Context Engineering | B | ok |
| Goal Alignment | B | ok |
| Safety | B | ok |
| Metadata | B | ok |
| Overall | B | weighted |

### Findings

#### Finding (severity: High, dimension: Clarity, checklist_item: WS-1, primary_focus: true, owner_conflict: false, hint_owner: null)
Evidence: at column 0
  Why it matters: indented two spaces — must still be recognised
    Validation: indented four spaces — must still be recognised
Current: at column 0
Recommended: at column 0
"""
        cert = parse_certificate(text, artifact_path="x.md")
        f = cert["findings"][0]
        assert f["evidence"] == "at column 0"
        assert "indented two spaces" in f["why"], f["why"]
        assert "indented four spaces" in f["validation"], f["validation"]
        assert f["current"] == "at column 0"
        assert f["recommended"] == "at column 0"

    def test_deeply_indented_label_treated_as_codeblock_content(self):
        """Five-or-more leading spaces — markdown fenced-code threshold — is
        preserved verbatim as field continuation, not parsed as a new label.
        This protects code examples that legitimately quote field-label
        strings.
        """
        text = """\
### Perspective
clarity

### Certificate
| Dimension | Grade | Justification |
|-----------|-------|---------------|
| Clarity | B | ok |
| Completeness | B | ok |
| Prompt Engineering | B | ok |
| Context Engineering | B | ok |
| Goal Alignment | B | ok |
| Safety | B | ok |
| Metadata | B | ok |
| Overall | B | weighted |

### Findings

#### Finding (severity: Low, dimension: Clarity, checklist_item: WS-1, primary_focus: false, owner_conflict: false, hint_owner: null)
Evidence: cite at column 0
Why it matters: short
Validation: short
Current: original line
Recommended: replacement using a code example:
     Current: this-is-codeblock-content-not-a-label
     Recommended: nor-is-this
"""
        cert = parse_certificate(text, artifact_path="x.md")
        f = cert["findings"][0]
        # The deeply-indented `Current:` and `Recommended:` lines must be
        # preserved as part of the original Recommended block, not parsed
        # as new field labels.
        assert "this-is-codeblock-content-not-a-label" in f["recommended"]
        assert "nor-is-this" in f["recommended"]
        assert f["current"] == "original line"


# ---------------------------------------------------------------------------
# Pipeline interop — parser output flows through merge_findings.merge_directory
# ---------------------------------------------------------------------------


class TestPipelineInterop:
    """The parser output must serialise to JSON and load cleanly via
    merge_findings.merge_directory(). This is a quick interop guard before
    the heavier tests/test_perspective_replay.py exercises the same boundary.
    """

    def test_parser_output_loads_in_merge_directory(self, tmp_path: pathlib.Path):
        from merge_findings import merge_directory  # noqa: WPS433

        md = (FIXTURES / "clear_antecedent_01" / "clarity.md").read_text(encoding="utf-8")
        cert = parse_certificate(md, artifact_path="skills/scaffold-skill/SKILL.md")
        # Sibling perspectives: neutral B-grade stubs with no findings, just so
        # merge_directory does not enter degraded_mode for owner-weighted dims.
        neutral = {
            "perspective": "<placeholder>",
            "dimensions": dict.fromkeys(VALID_DIMENSIONS, "B"),
            "findings": [],
            "artifact_frontmatter": {"allowed_tools": ["Read"]},
        }
        (tmp_path / "clarity.json").write_text(json.dumps(cert), encoding="utf-8")
        for sibling in ("correctness", "integration"):
            stub = dict(neutral)
            stub["perspective"] = sibling
            (tmp_path / f"{sibling}.json").write_text(json.dumps(stub), encoding="utf-8")

        result = merge_directory(tmp_path)
        assert result["status"] == "success"
        assert result["degraded_mode"] is False
        # Clarity-perspective findings are preserved through the merge.
        # (Findings on binary items would be dropped, but WS-1 is non-binary.)
        merged_items = {f.get("checklist_item") for f in result["findings"]}
        assert "WS-1" in merged_items
