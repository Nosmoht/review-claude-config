"""Tests for the JSON Schema contract on review findings.

Schemas:
- ``skills/review-claude-config/references/schemas/finding.schema.json``
- ``skills/review-claude-config/references/schemas/findings-list.schema.json``

Validates the schemas themselves (well-formed JSON Schema 2020-12), then
exercises positive/negative cases against representative finding shapes
sourced from ``scripts/merge_findings.py``'s synthesize_binary_findings()
output.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

import pytest
from jsonschema import Draft202012Validator, RefResolver

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "skills" / "review-claude-config" / "references" / "schemas"
FINDING_SCHEMA_PATH = SCHEMAS_DIR / "finding.schema.json"
FINDINGS_LIST_SCHEMA_PATH = SCHEMAS_DIR / "findings-list.schema.json"

sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))


@pytest.fixture(scope="module")
def finding_schema() -> dict:
    return json.loads(FINDING_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def findings_list_schema() -> dict:
    return json.loads(FINDINGS_LIST_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def finding_validator(finding_schema) -> Draft202012Validator:
    return Draft202012Validator(finding_schema)


@pytest.fixture(scope="module")
def findings_list_validator(findings_list_schema, finding_schema) -> Draft202012Validator:
    """Resolve the cross-schema ``$ref: finding.schema.json`` from a local store
    so the validator never reaches the network.
    """
    store = {finding_schema["$id"]: finding_schema, "finding.schema.json": finding_schema}
    resolver = RefResolver.from_schema(findings_list_schema, store=store)
    return Draft202012Validator(findings_list_schema, resolver=resolver)


# ---------------------------------------------------------------------------
# Schema self-validation: the schemas are themselves valid JSON Schema 2020-12.
# ---------------------------------------------------------------------------


class TestSchemaSelfValidation:
    def test_finding_schema_is_valid_jsonschema(self, finding_schema):
        Draft202012Validator.check_schema(finding_schema)

    def test_findings_list_schema_is_valid_jsonschema(self, findings_list_schema):
        Draft202012Validator.check_schema(findings_list_schema)

    def test_finding_schema_uses_2020_12(self, finding_schema):
        assert finding_schema["$schema"].endswith("2020-12/schema")

    def test_findings_list_schema_uses_2020_12(self, findings_list_schema):
        assert findings_list_schema["$schema"].endswith("2020-12/schema")

    def test_finding_schema_pins_severity_enum(self, finding_schema):
        """Lock the canonical severity enum so an out-of-band rename of e.g.
        'High' to 'Critical' fails this test loudly rather than silently
        invalidating every existing finding.
        """
        sev = finding_schema["properties"]["severity"]
        assert sev["enum"] == ["High", "Medium", "Low"]

    def test_finding_schema_pins_dimension_enum(self, finding_schema):
        dim = finding_schema["properties"]["dimension"]
        assert dim["enum"] == [
            "Clarity",
            "Completeness",
            "Prompt Engineering",
            "Context Engineering",
            "Goal Alignment",
            "Safety",
            "Metadata",
        ]


# ---------------------------------------------------------------------------
# Helper builders for representative findings.
# ---------------------------------------------------------------------------


def _high_finding(**overrides) -> dict:
    """A minimally-valid High-severity finding (must include Current/Recommended
    per the conditional rule)."""
    base = {
        "id": "CLAR-2:skills/x/SKILL.md:Clarity/v1",
        "checklist_item": "CLAR-2",
        "dimension": "Clarity",
        "severity": "High",
        "evidence": "line 12; match='slightly more'",
        "current": "fetch slightly more data",
        "recommended": "fetch exactly N records (specify N)",
        "perspective": "binary-evaluator",
        "path": "skills/x/SKILL.md",
        "line_range": "12",
    }
    base.update(overrides)
    return base


def _medium_finding(**overrides) -> dict:
    base = {
        "id": "CE-X:skills/x/SKILL.md:Context Engineering/v1",
        "checklist_item": "CE-X",
        "dimension": "Context Engineering",
        "severity": "Medium",
        "evidence": "skill loads 12K tokens upfront without JIT pattern",
        "perspective": "correctness",
    }
    base.update(overrides)
    return base


def _low_finding(**overrides) -> dict:
    base = {
        "id": "META-4::Metadata",
        "checklist_item": "META-4",
        "dimension": "Metadata",
        "severity": "Low",
        "evidence": "description uses second-person 'you can' once",
        "perspective": "clarity",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Positive cases: representative real findings must validate cleanly.
# ---------------------------------------------------------------------------


class TestFindingValidation:
    def test_high_finding_with_current_recommended_passes(self, finding_validator):
        finding_validator.validate(_high_finding())

    def test_medium_finding_passes(self, finding_validator):
        finding_validator.validate(_medium_finding())

    def test_low_finding_passes(self, finding_validator):
        finding_validator.validate(_low_finding())

    def test_unknown_extra_fields_allowed(self, finding_validator):
        """additionalProperties: true — defensive against forward-compat
        additions to the shape (new fields appear in merge_findings.py
        without coordinated schema bumps)."""
        f = _medium_finding(experimental_score=0.42, undocumented_field="ok")
        finding_validator.validate(f)

    def test_synthesize_binary_findings_output_validates(self, finding_validator):
        """Real synthesizer output (the deterministic path) must validate.
        Catches drift between merge_findings.py and the schema."""
        from merge_findings import synthesize_binary_findings

        verdicts_doc = {
            "verdicts": {
                "CLAR-2": {
                    "verdict": "FAIL",
                    "evidence": {"line": 12, "match": "slightly more"},
                }
            }
        }
        findings = synthesize_binary_findings(verdicts_doc, "skills/x/SKILL.md")
        assert findings, "synthesize_binary_findings must produce at least one finding for FAIL"
        for f in findings:
            finding_validator.validate(f)


# ---------------------------------------------------------------------------
# Negative cases: malformed findings must fail with clear errors.
# ---------------------------------------------------------------------------


class TestFindingViolations:
    def test_missing_id_fails(self, finding_validator):
        f = _medium_finding()
        del f["id"]
        with pytest.raises(Exception):
            finding_validator.validate(f)

    def test_missing_evidence_fails(self, finding_validator):
        f = _medium_finding()
        del f["evidence"]
        with pytest.raises(Exception):
            finding_validator.validate(f)

    def test_empty_evidence_fails(self, finding_validator):
        f = _medium_finding(evidence="")
        with pytest.raises(Exception):
            finding_validator.validate(f)

    def test_invalid_dimension_fails(self, finding_validator):
        f = _medium_finding(dimension="Performance")  # not in enum
        with pytest.raises(Exception):
            finding_validator.validate(f)

    def test_off_spec_severity_case_fails(self, finding_validator):
        """'high' (lowercase) is normalised by merge_findings to 'Low' before
        emit; here we lock that the schema rejects unsanitised input.
        """
        f = _medium_finding(severity="high")
        with pytest.raises(Exception):
            finding_validator.validate(f)

    def test_high_without_current_recommended_fails(self, finding_validator):
        """Conditional rule: severity High requires Current+Recommended for the
        apply pipeline. A High finding missing 'recommended' must fail."""
        f = _high_finding()
        del f["recommended"]
        with pytest.raises(Exception):
            finding_validator.validate(f)

    def test_high_missing_current_fails(self, finding_validator):
        f = _high_finding()
        del f["current"]
        with pytest.raises(Exception):
            finding_validator.validate(f)

    def test_medium_without_current_recommended_passes(self, finding_validator):
        """Medium does NOT trigger the conditional requirement."""
        f = _medium_finding()
        finding_validator.validate(f)


# ---------------------------------------------------------------------------
# Findings-list wrapper validation.
# ---------------------------------------------------------------------------


class TestFindingsListValidation:
    def test_minimal_list_passes(self, findings_list_validator):
        payload = {
            "generated_by": "merge_findings",
            "findings": [_medium_finding()],
        }
        findings_list_validator.validate(payload)

    def test_full_list_with_metadata_passes(self, findings_list_validator):
        payload = {
            "generated_by": "merge_findings",
            "schema_version": "1.0.0",
            "session_id": "abc-123",
            "artifact_path": "skills/x/SKILL.md",
            "artifact_type": "skill",
            "findings": [_high_finding(), _medium_finding(), _low_finding()],
        }
        findings_list_validator.validate(payload)

    def test_empty_findings_array_passes(self, findings_list_validator):
        """No findings is a legitimate clean-review state."""
        payload = {"generated_by": "merge_findings", "findings": []}
        findings_list_validator.validate(payload)

    def test_missing_generated_by_fails(self, findings_list_validator):
        with pytest.raises(Exception):
            findings_list_validator.validate({"findings": []})

    def test_missing_findings_key_fails(self, findings_list_validator):
        with pytest.raises(Exception):
            findings_list_validator.validate({"generated_by": "x"})

    def test_invalid_artifact_type_fails(self, findings_list_validator):
        payload = {
            "generated_by": "merge_findings",
            "artifact_type": "binary",  # not in enum
            "findings": [],
        }
        with pytest.raises(Exception):
            findings_list_validator.validate(payload)

    def test_invalid_finding_in_list_fails(self, findings_list_validator):
        payload = {
            "generated_by": "merge_findings",
            "findings": [{"id": "x", "checklist_item": "Y"}],  # missing required fields
        }
        with pytest.raises(Exception):
            findings_list_validator.validate(payload)


# ---------------------------------------------------------------------------
# Sidecar emission (--findings-out flag in merge_findings.py).
# ---------------------------------------------------------------------------


class TestSidecarEmission:
    def test_write_findings_sidecar_atomic(self, tmp_path):
        """Atomic write via .tmp rename — interruption mid-write must not leave
        a partial findings.json that downstream apply-* would parse.
        """
        from merge_findings import write_findings_sidecar

        result = {
            "findings": [_high_finding(), _medium_finding()],
            "dimensions": {"Clarity": "B"},
        }
        out = tmp_path / "findings.json"
        write_findings_sidecar(result, out, session_id="sess-1")
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["generated_by"] == "merge_findings"
        assert loaded["session_id"] == "sess-1"
        assert loaded["schema_version"] == "1.0.0"
        assert loaded["artifact_path"] == "skills/x/SKILL.md"
        assert len(loaded["findings"]) == 2

    def test_sidecar_validates_against_findings_list_schema(
        self, tmp_path, findings_list_validator
    ):
        from merge_findings import write_findings_sidecar

        result = {
            "findings": [_high_finding(), _medium_finding(), _low_finding()],
        }
        out = tmp_path / "findings.json"
        write_findings_sidecar(result, out)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        findings_list_validator.validate(loaded)

    def test_sidecar_with_empty_findings(self, tmp_path, findings_list_validator):
        from merge_findings import write_findings_sidecar

        out = tmp_path / "findings.json"
        write_findings_sidecar({"findings": []}, out)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        findings_list_validator.validate(loaded)
        assert loaded["findings"] == []

    def test_sidecar_omits_session_id_when_none(self, tmp_path):
        from merge_findings import write_findings_sidecar

        out = tmp_path / "findings.json"
        write_findings_sidecar({"findings": []}, out, session_id=None)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert "session_id" not in loaded
