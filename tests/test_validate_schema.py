"""Tests for scripts/validate_schema.py — frontmatter and hooks.json validation."""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import validate_schema
from validate_schema import (
    DESCRIPTION_MIN_LEN,
    validate_agent_files,
    validate_domain_cache_files,
    validate_hooks_json,
    validate_reference_files,
    validate_research_files,
    validate_skill_files,
)
from validate_schema import main as validate_main


class TestValidateAgainstSchema:
    """Tests for the _validate_against_schema helper."""

    # Negative test #1 (plan §Negative-test enumeration):
    # Proves the schema-driven path actually fires — catches a _validate_files no-op bug.
    def test_schema_rejects_missing_required_field(self, tmp_path, monkeypatch):
        """validate_reference_files must return 'missing required field' for
        a ref-file missing the 'name' field.

        This guards against the _validate_against_schema call being silently
        skipped or the schema having name removed from required[].
        """
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-claude-config" / "references"
        d.mkdir(parents=True)
        # Missing 'name' — required by ref-file.schema.json
        (d / "no-name.md").write_text(
            "---\ndescription: a description that meets the minimum length\nlast_refreshed: 2026-01-01\n---\n"
        )
        errors = validate_reference_files()
        assert any("missing required field 'name'" in e for e in errors), (
            f"Expected 'missing required field name' error, got: {errors}"
        )


class TestValidateSkillFiles:
    def test_includes_dotclaude_skills(self, tmp_path, monkeypatch):
        """Maintenance skills under .claude/skills/ are validated."""
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "skills" / "a").mkdir(parents=True)
        (tmp_path / "skills" / "a" / "SKILL.md").write_text(
            "---\nname: a\ndescription: a description that meets the minimum length\n---\n"
        )
        # Maintenance skill missing required 'name' field
        (tmp_path / ".claude" / "skills" / "b").mkdir(parents=True)
        (tmp_path / ".claude" / "skills" / "b" / "SKILL.md").write_text(
            "---\ndescription: a description that meets the minimum length\n---\n"
        )
        errors = validate_skill_files()
        assert any(".claude" in e and "name" in e for e in errors)

    def test_valid_skills_no_errors(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "skills" / "x").mkdir(parents=True)
        (tmp_path / "skills" / "x" / "SKILL.md").write_text(
            "---\nname: x\ndescription: a description that meets the minimum length\n---\n"
        )
        (tmp_path / ".claude" / "skills" / "y").mkdir(parents=True)
        (tmp_path / ".claude" / "skills" / "y" / "SKILL.md").write_text(
            "---\nname: y\ndescription: a description that meets the minimum length\n---\n"
        )
        assert validate_skill_files() == []

    def test_empty_repo_no_errors(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        assert validate_skill_files() == []

    def test_missing_frontmatter_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "skills" / "x").mkdir(parents=True)
        (tmp_path / "skills" / "x" / "SKILL.md").write_text("# No frontmatter\n")
        errors = validate_skill_files()
        assert any("missing YAML frontmatter" in e for e in errors)

    def test_block_scalar_description_accepted(self, tmp_path, monkeypatch):
        """SKILL.md with `description: >` block scalar passes validation —
        the content is now actually inspected, not just present-as-substring.
        """
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "skills" / "x").mkdir(parents=True)
        (tmp_path / "skills" / "x" / "SKILL.md").write_text(
            "---\nname: x\ndescription: >\n  A multi-line description that is plenty long.\n---\n"
        )
        assert validate_skill_files() == []

    def test_empty_block_scalar_description_now_flagged(self, tmp_path, monkeypatch):
        """Regression test for the migration: previously a SKILL with an
        empty ``description: >`` followed by no body would pass via the
        raw-text workaround. Now the validator inspects the parsed content.
        """
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "skills" / "x").mkdir(parents=True)
        (tmp_path / "skills" / "x" / "SKILL.md").write_text(
            "---\nname: x\ndescription: >\n---\n"
        )
        errors = validate_skill_files()
        assert any("description" in e and "too short" in e for e in errors)

    def test_short_description_flagged(self, tmp_path, monkeypatch):
        """Description shorter than DESCRIPTION_MIN_LEN must fail, regardless
        of YAML scalar style.
        """
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "skills" / "x").mkdir(parents=True)
        (tmp_path / "skills" / "x" / "SKILL.md").write_text(
            "---\nname: x\ndescription: short\n---\n"
        )
        errors = validate_skill_files()
        assert any("too short" in e for e in errors)

    def test_description_with_yaml_comment_flagged(self, tmp_path, monkeypatch):
        """Real bug class: ``description: #issue-42 explanation`` is a YAML
        comment, not a value. Must be flagged as a missing/null description
        instead of silently passing.
        """
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "skills" / "x").mkdir(parents=True)
        (tmp_path / "skills" / "x" / "SKILL.md").write_text(
            "---\nname: x\ndescription: #42 explanation\n---\n"
        )
        errors = validate_skill_files()
        assert any("description" in e for e in errors)

    # Negative test #2 (plan §Negative-test enumeration):
    # Proves _validate_description auto-wires for skill files (catches H1 regression).
    def test_description_min_length_after_strip_still_caught(self, tmp_path, monkeypatch):
        """A description of exactly 20 spaces passes schema minLength:1 but
        must be caught by _validate_description strip-aware check (≥20 chars
        of non-whitespace content).

        This guards against _validate_description being removed from the
        auto-wire path in _validate_files.
        """
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "skills" / "x").mkdir(parents=True)
        # 20 spaces: passes schema minLength:1, should fail strip-aware check
        (tmp_path / "skills" / "x" / "SKILL.md").write_text(
            "---\nname: x\ndescription: '                    '\n---\n"
        )
        errors = validate_skill_files()
        assert any("too short" in e for e in errors), (
            f"Expected 'too short' error for whitespace-only description, got: {errors}"
        )


class TestValidateAgentFiles:
    def test_valid_agent_no_errors(self, tmp_path, monkeypatch):
        """A well-formed agent file with all required fields passes."""
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        agents = tmp_path / "agents"
        agents.mkdir()
        (agents / "my-agent.md").write_text(
            "---\nname: my-agent\ndescription: a description that meets the minimum length\nmodel: claude-opus-4-5\ntools: [Read, Write]\n---\n"
        )
        assert validate_agent_files() == []

    def test_missing_model_flagged(self, tmp_path, monkeypatch):
        """Agent missing 'model' field is rejected by schema."""
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        agents = tmp_path / "agents"
        agents.mkdir()
        (agents / "no-model.md").write_text(
            "---\nname: x\ndescription: a description that meets the minimum length\ntools: [Read]\n---\n"
        )
        errors = validate_agent_files()
        assert any("model" in e for e in errors)

    def test_no_agents_dir_no_errors(self, tmp_path, monkeypatch):
        """Missing agents/ directory returns no errors (optional validator)."""
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        assert validate_agent_files() == []

    # Negative test #4 (plan §Negative-test enumeration):
    # Proves SAMP raw-text inspection still runs (catches accidental schema-only mis-wiring).
    def test_samp1_samp2_regex_unchanged(self, tmp_path, monkeypatch):
        """An agent file with 'temperature: 0.7' in frontmatter must trigger
        SAMP-2 FAIL — raw-text inspection fires even though the schema does
        not enforce sampling params.

        This guards against the _samp_check being removed from extra_checks
        or against someone thinking the schema covers sampling-param detection.
        """
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        agents = tmp_path / "agents"
        agents.mkdir()
        # temperature in frontmatter: SAMP-2 FAIL
        (agents / "sampled-agent.md").write_text(
            "---\nname: x\ndescription: a description that meets the minimum length\nmodel: claude-opus-4-5\ntools: [Read]\ntemperature: 0.7\n---\n"
        )
        errors = validate_agent_files()
        assert any("SAMP-2" in e for e in errors), (
            f"Expected SAMP-2 FAIL error for temperature in frontmatter, got: {errors}"
        )


class TestValidateReferenceFiles:
    def test_covers_multiple_skill_dirs(self, tmp_path, monkeypatch):
        """Reference files under any skills/*/references/ are validated."""
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        for skill in ("review-claude-config", "check-repo-health"):
            d = tmp_path / "skills" / skill / "references"
            d.mkdir(parents=True)
            (d / "ref.md").write_text(
                "---\nname: r\ndescription: a description that meets the minimum length\nlast_refreshed: 2026-01-01\n---\n"
            )
        # One with missing required fields
        bad = tmp_path / "skills" / "audit-repo" / "references"
        bad.mkdir(parents=True)
        (bad / "bad.md").write_text("---\nname: r\n---\n")
        errors = validate_reference_files()
        assert any("audit-repo" in e and "description" in e for e in errors)
        assert any("audit-repo" in e and "last_refreshed" in e for e in errors)

    def test_no_refs_returns_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        errors = validate_reference_files()
        assert len(errors) == 1
        assert "No reference files found" in errors[0]

    def test_missing_frontmatter_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-claude-config" / "references"
        d.mkdir(parents=True)
        (d / "no-fm.md").write_text("# No frontmatter\n")
        errors = validate_reference_files()
        assert any("missing YAML frontmatter" in e for e in errors)

    def test_does_not_recurse_into_domain_cache(self, tmp_path, monkeypatch):
        """domain-cache/*.md files are not picked up by validate_reference_files."""
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-claude-config" / "references"
        d.mkdir(parents=True)
        (d / "ref.md").write_text(
            "---\nname: r\ndescription: a description that meets the minimum length\nlast_refreshed: 2026-01-01\n---\n"
        )
        # domain-cache file lacks name/description — should NOT trigger reference validator
        cache = d / "domain-cache"
        cache.mkdir()
        (cache / "cilium.md").write_text("---\ndomain: cilium\nlast_refreshed: 2026-01-01\n---\n")
        errors = validate_reference_files()
        assert errors == []

    def test_invalid_date_format_in_reference(self, tmp_path, monkeypatch):
        """`last_refreshed: 2026-4-5` (no zero-pad) must be flagged. Verifies
        StrictStringsLoader keeps the string for DATE_RE inspection.
        """
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-claude-config" / "references"
        d.mkdir(parents=True)
        (d / "ref.md").write_text(
            "---\nname: r\ndescription: a description that meets the minimum length\nlast_refreshed: 2026-4-5\n---\n"
        )
        errors = validate_reference_files()
        assert any("not strict YYYY-MM-DD" in e for e in errors)


class TestValidateResearchFiles:
    def test_valid_research_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "research" / "topic").mkdir(parents=True)
        (tmp_path / "research" / "topic" / "paper.md").write_text(
            "---\nlast_refreshed: 2026-01-01\n---\n# Content\n"
        )
        assert validate_research_files() == []

    def test_missing_last_refreshed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "research" / "topic").mkdir(parents=True)
        (tmp_path / "research" / "topic" / "paper.md").write_text(
            "---\nname: paper\n---\n# Content\n"
        )
        errors = validate_research_files()
        assert any("last_refreshed" in e for e in errors)

    def test_no_research_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        assert validate_research_files() == []

    def test_missing_frontmatter(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "research" / "topic").mkdir(parents=True)
        (tmp_path / "research" / "topic" / "no-fm.md").write_text("# No frontmatter\n")
        errors = validate_research_files()
        assert any("missing YAML frontmatter" in e for e in errors)

    def test_unquoted_date_round_trips_as_string(self, tmp_path, monkeypatch):
        """Real research files use unquoted ``last_refreshed: 2026-04-03``.
        Without StrictStringsLoader these become datetime.date and break
        DATE_RE — this test pins the loader contract end-to-end.
        """
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "research" / "topic").mkdir(parents=True)
        (tmp_path / "research" / "topic" / "paper.md").write_text(
            "---\nlast_refreshed: 2026-04-03\n---\n"
        )
        assert validate_research_files() == []


class TestValidateDomainCacheFiles:
    def test_valid_cache_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        cache = tmp_path / "skills" / "review-claude-config" / "references" / "domain-cache"
        cache.mkdir(parents=True)
        (cache / "cilium.md").write_text("---\ndomain: cilium\nlast_refreshed: 2026-01-01\n---\n")
        assert validate_domain_cache_files() == []

    def test_missing_domain_field(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        cache = tmp_path / "skills" / "review-claude-config" / "references" / "domain-cache"
        cache.mkdir(parents=True)
        (cache / "missing-domain.md").write_text("---\nlast_refreshed: 2026-01-01\n---\n")
        errors = validate_domain_cache_files()
        assert any("domain" in e for e in errors)

    def test_index_md_skipped(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        cache = tmp_path / "skills" / "review-claude-config" / "references" / "domain-cache"
        cache.mkdir(parents=True)
        (cache / "INDEX.md").write_text("# Index — no frontmatter needed\n")
        assert validate_domain_cache_files() == []

    def test_no_cache_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        assert validate_domain_cache_files() == []

    def test_missing_frontmatter_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        cache = tmp_path / "skills" / "review-claude-config" / "references" / "domain-cache"
        cache.mkdir(parents=True)
        (cache / "no-fm.md").write_text("# No frontmatter\n")
        errors = validate_domain_cache_files()
        assert any("missing YAML frontmatter" in e for e in errors)

    def test_missing_last_refreshed_only(self, tmp_path, monkeypatch):
        """domain field present but last_refreshed missing — covers the
        partial-frontmatter case.
        """
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        cache = tmp_path / "skills" / "review-claude-config" / "references" / "domain-cache"
        cache.mkdir(parents=True)
        (cache / "no-date.md").write_text("---\ndomain: cilium\n---\n")
        errors = validate_domain_cache_files()
        assert any("last_refreshed" in e for e in errors)


class TestValidateHooksJson:
    def test_valid_hooks_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "my_script.py").write_text("# script\n")
        data = {
            "hooks": {
                "SessionStart": [
                    {"hooks": [{"command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/my_script.py"}]}
                ]
            }
        }
        (hooks_dir / "hooks.json").write_text(json.dumps(data))
        assert validate_hooks_json() == []

    def test_invalid_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "hooks.json").write_text("not valid json{")
        errors = validate_hooks_json()
        assert any("invalid JSON" in e for e in errors)

    def test_missing_script_reference(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        data = {
            "hooks": {
                "PreToolUse": [
                    {"hooks": [{"command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/nonexistent.py"}]}
                ]
            }
        }
        (hooks_dir / "hooks.json").write_text(json.dumps(data))
        errors = validate_hooks_json()
        assert any("nonexistent.py" in e for e in errors)

    def test_missing_hooks_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        errors = validate_hooks_json()
        assert any("not found" in e or "file not found" in e.lower() for e in errors)


class TestValidateMain:
    def _setup_valid_repo(self, tmp_path):
        """Create minimal valid structure for all validators to pass."""
        import json as _json

        import yaml as _yaml

        # Reference files
        refs = tmp_path / "skills" / "review-claude-config" / "references"
        schemas = refs / "schemas"
        refs.mkdir(parents=True)
        schemas.mkdir()
        (refs / "ref.md").write_text(
            "---\nname: r\ndescription: a description that meets the minimum length\nlast_refreshed: 2026-01-01\n---\n"
        )
        # YAML reference files (validate_yaml_reference_files allowlist)
        audit_yaml = {
            "policy_version": "1.0",
            "triggers": [{"id": "WS-7", "pattern": "foo", "flags": [], "notes": "test trigger"}],
            "count_triggers": [
                {"id": "WS-8", "pattern": "bar", "flags": ["IGNORECASE"], "min_matches": 2, "notes": "count test"},
                {"id": "GA-S", "name_prefix_match": ["review-"], "notes": "ga-s test"},
            ],
            "item_order": ["WS-7", "WS-8", "GA-S"],
        }
        audit_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["policy_version", "triggers", "count_triggers", "item_order"],
            "properties": {
                "policy_version": {"type": "string", "const": "1.0"},
                "triggers": {"type": "array"},
                "count_triggers": {"type": "array"},
                "item_order": {"type": "array"},
            },
        }
        (refs / "audit-triggers.yaml").write_text(_yaml.dump(audit_yaml), encoding="utf-8")
        (schemas / "audit-triggers.schema.json").write_text(_json.dumps(audit_schema), encoding="utf-8")

        conv_yaml = {
            "policy_version": "1.0",
            "DETERMINISTIC_SUBSET": ["CLAR-1"],
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
                "DETERMINISTIC_SUBSET": {"type": "array", "minItems": 1, "uniqueItems": True,
                                         "items": {"type": "string", "minLength": 1}},
                "GRADE_LETTERS": {"type": "array", "minItems": 5, "uniqueItems": True,
                                  "items": {"type": "string", "minLength": 1}},
                "DEFAULT_MAX_VARIANCE": {"type": "integer", "minimum": 0},
            },
        }
        (refs / "convergence-rules.yaml").write_text(_yaml.dump(conv_yaml), encoding="utf-8")
        (schemas / "convergence-rules.schema.json").write_text(_json.dumps(conv_schema), encoding="utf-8")

        # Note: merge-policy.yaml not present in tmp_path → drift check is skipped gracefully
        esc_yaml = {
            "policy_version": "1.0",
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
        (refs / "escalation-rules.yaml").write_text(_yaml.dump(esc_yaml), encoding="utf-8")
        (schemas / "escalation-rules.schema.json").write_text(_json.dumps(esc_schema), encoding="utf-8")

        # Hooks json (no script refs to resolve)
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "hooks.json").write_text('{"hooks": {}}')

    def test_all_valid_returns_zero(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        self._setup_valid_repo(tmp_path)
        result = validate_main()
        assert result == 0
        assert "All validations passed" in capsys.readouterr().out

    def test_errors_return_one(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        # No reference files → validate_reference_files returns an error
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "hooks.json").write_text('{"hooks": {}}')
        result = validate_main()
        assert result == 1
        output = capsys.readouterr().out
        assert "error" in output.lower()


def test_description_min_len_is_reasonable():
    """Lock the threshold value so a future bump to 100 is an explicit
    decision, not a silent change.
    """
    assert DESCRIPTION_MIN_LEN == 20
