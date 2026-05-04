"""Tests for validate_schema.validate_yaml_reference_files().

Covers: all-present+consistent → [], schema missing, yaml malformed,
schema-violation (policy_version const), and cross-YAML drift detection.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from validate_schema import validate_yaml_reference_files  # noqa: E402


MERGE_POLICY_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / "skills" / "review-skill" / "references" / "merge-policy.yaml"
)


def _make_refs_dir(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """Create skills/review-claude-config/references/schemas/ under tmp_path."""
    refs = tmp_path / "skills" / "review-claude-config" / "references"
    schemas = refs / "schemas"
    refs.mkdir(parents=True)
    schemas.mkdir()
    return refs, schemas


def test_all_present_and_consistent():
    """Real YAML + schema files pass with no errors."""
    errors = validate_yaml_reference_files()
    assert errors == [], f"Unexpected errors: {errors}"


def test_schema_missing(tmp_path, monkeypatch):
    """When a schema is absent, error contains 'no schema found'."""
    refs, schemas = _make_refs_dir(tmp_path)
    yaml_content = {
        "policy_version": "1.0",
        "GRADE_LETTERS": ["A", "B", "C", "D", "F"],
        "DEFAULT_MAX_VARIANCE": 1,
        "DETERMINISTIC_SUBSET": ["CLAR-1"],
    }
    (refs / "convergence-rules.yaml").write_text(yaml.dump(yaml_content), encoding="utf-8")
    # No convergence-rules.schema.json → "no schema found"

    import validate_schema as vs
    monkeypatch.setattr(vs, "REPO_ROOT", tmp_path)
    errors = validate_yaml_reference_files()
    assert any("no schema found" in e for e in errors), f"Expected 'no schema found' in: {errors}"


def test_yaml_malformed(tmp_path, monkeypatch):
    """When a yaml file is malformed, error contains 'invalid'."""
    refs, schemas = _make_refs_dir(tmp_path)

    esc_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["policy_version", "GRADE_BOUNDARIES", "ESC1_PROXIMITY", "ESC3_DIVERGENCE"],
        "additionalProperties": False,
        "properties": {
            "policy_version": {"type": "string", "const": "1.0"},
            "GRADE_BOUNDARIES": {"type": "array", "minItems": 1, "items": {"type": "integer"}},
            "ESC1_PROXIMITY": {"type": "number"},
            "ESC3_DIVERGENCE": {"type": "number"},
        },
    }
    (schemas / "escalation-rules.schema.json").write_text(json.dumps(esc_schema), encoding="utf-8")
    # Write YAML that will fail yaml.safe_load by using a disallowed tag
    (refs / "escalation-rules.yaml").write_text(
        "policy_version: !!python/object:os.system 'bad'", encoding="utf-8"
    )

    import validate_schema as vs
    monkeypatch.setattr(vs, "REPO_ROOT", tmp_path)
    errors = validate_yaml_reference_files()
    assert any("invalid" in e.lower() or "file not found" in e for e in errors), (
        f"Expected invalid or file-not-found error in: {errors}"
    )


def test_schema_violation_policy_version(tmp_path, monkeypatch):
    """A wrong policy_version const is rejected with the field path in the error."""
    refs, schemas = _make_refs_dir(tmp_path)

    bad_yaml = {
        "policy_version": "2.0",  # schema requires const '1.0'
        "GRADE_BOUNDARIES": [60, 70, 80, 90],
        "ESC1_PROXIMITY": 2.5,
        "ESC3_DIVERGENCE": 20.0,
    }
    esc_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["policy_version", "GRADE_BOUNDARIES", "ESC1_PROXIMITY", "ESC3_DIVERGENCE"],
        "additionalProperties": False,
        "properties": {
            "policy_version": {"type": "string", "const": "1.0"},
            "GRADE_BOUNDARIES": {"type": "array", "minItems": 1, "items": {"type": "integer"}},
            "ESC1_PROXIMITY": {"type": "number"},
            "ESC3_DIVERGENCE": {"type": "number"},
        },
    }
    (refs / "escalation-rules.yaml").write_text(yaml.dump(bad_yaml), encoding="utf-8")
    (schemas / "escalation-rules.schema.json").write_text(json.dumps(esc_schema), encoding="utf-8")

    import validate_schema as vs
    monkeypatch.setattr(vs, "REPO_ROOT", tmp_path)
    errors = validate_yaml_reference_files()
    # Should have a schema-violation error mentioning policy_version
    assert any("policy_version" in e or "$.policy_version" in e for e in errors), (
        f"Expected policy_version schema violation in: {errors}"
    )


def test_deterministic_subset_drift(tmp_path, monkeypatch):
    """When DETERMINISTIC_SUBSET diverges from merge-policy union, error contains 'DETERMINISTIC_SUBSET drift'."""
    refs, schemas = _make_refs_dir(tmp_path)

    conv_yaml = {
        "policy_version": "1.0",
        "DETERMINISTIC_SUBSET": ["FAKE-1", "FAKE-2"],  # does not match merge-policy union
        "GRADE_LETTERS": ["A", "B", "C", "D", "F"],
        "DEFAULT_MAX_VARIANCE": 1,
    }
    conv_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["policy_version", "DETERMINISTIC_SUBSET", "GRADE_LETTERS", "DEFAULT_MAX_VARIANCE"],
        "additionalProperties": False,
        "properties": {
            "policy_version": {"type": "string", "const": "1.0"},
            "DETERMINISTIC_SUBSET": {
                "type": "array", "minItems": 1, "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "GRADE_LETTERS": {
                "type": "array", "minItems": 5, "uniqueItems": True,
                "items": {"type": "string", "minLength": 1},
            },
            "DEFAULT_MAX_VARIANCE": {"type": "integer", "minimum": 0},
        },
    }
    (refs / "convergence-rules.yaml").write_text(yaml.dump(conv_yaml), encoding="utf-8")
    (schemas / "convergence-rules.schema.json").write_text(json.dumps(conv_schema), encoding="utf-8")

    # Copy the real merge-policy.yaml into tmp_path for the drift check
    review_skill_refs = tmp_path / "skills" / "review-skill" / "references"
    review_skill_refs.mkdir(parents=True)
    (review_skill_refs / "merge-policy.yaml").write_text(
        MERGE_POLICY_PATH.read_text(encoding="utf-8"), encoding="utf-8"
    )

    import validate_schema as vs
    monkeypatch.setattr(vs, "REPO_ROOT", tmp_path)
    errors = validate_yaml_reference_files()
    assert any("DETERMINISTIC_SUBSET drift" in e for e in errors), (
        f"Expected DETERMINISTIC_SUBSET drift error in: {errors}"
    )
