"""Tests for scripts/validate_schema.py — frontmatter and hooks.json validation."""

import json
import pathlib

import pytest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import validate_schema
from validate_schema import (
    DATE_RE,
    parse_frontmatter,
    validate_date,
    validate_domain_cache_files,
    validate_hooks_json,
    validate_reference_files,
    validate_research_files,
    validate_skill_files,
)
from validate_schema import main as validate_main


@pytest.fixture
def md_file(tmp_path):
    """Create a markdown file with given content."""

    def _create(content, name="test.md"):
        p = tmp_path / name
        p.write_text(content)
        return p

    return _create


class TestDateRegex:
    @pytest.mark.parametrize("valid", ["2026-01-01", "2026-12-31", "2000-06-15"])
    def test_valid_dates(self, valid):
        assert DATE_RE.match(valid)

    @pytest.mark.parametrize(
        "invalid",
        [
            "2026-1-01",    # missing zero-pad month
            "2026-01-1",    # missing zero-pad day
            "2026-4-5",     # both missing (known TODO.md issue)
            "26-01-01",     # 2-digit year
            "2026/01/01",   # wrong separator
            "20260101",     # no separators
            "not-a-date",
            "",
        ],
    )
    def test_invalid_dates(self, invalid):
        assert not DATE_RE.match(invalid)


class TestValidateDate:
    def test_valid(self, tmp_path):
        errors = validate_date("2026-03-15", tmp_path / "f.md", "last_refreshed")
        assert errors == []

    def test_bad_format(self, tmp_path):
        errors = validate_date("2026-4-5", tmp_path / "f.md", "last_refreshed")
        assert len(errors) == 1
        assert "not strict YYYY-MM-DD" in errors[0]

    def test_impossible_date(self, tmp_path):
        errors = validate_date("2026-02-30", tmp_path / "f.md", "last_refreshed")
        assert len(errors) == 1
        assert "not a valid date" in errors[0]


class TestParseFrontmatter:
    def test_valid_frontmatter(self, md_file):
        p = md_file("---\nname: test\ndescription: a thing\nlast_refreshed: 2026-01-01\n---\n# Body\n")
        fm = parse_frontmatter(p)
        assert fm == {"name": "test", "description": "a thing", "last_refreshed": "2026-01-01"}

    def test_no_frontmatter(self, md_file):
        p = md_file("# Just a heading\n")
        assert parse_frontmatter(p) is None

    def test_empty_file(self, md_file):
        p = md_file("")
        assert parse_frontmatter(p) is None

    def test_block_scalar_skipped(self, md_file):
        p = md_file("---\nname: test\ndescription: >\n  multi\n  line\nlast_refreshed: 2026-01-01\n---\n")
        fm = parse_frontmatter(p)
        assert fm is not None
        assert "name" in fm
        assert "last_refreshed" in fm
        # block scalar description is intentionally skipped (>) in simple parser
        assert "description" not in fm

    def test_pipe_block_scalar_skipped(self, md_file):
        p = md_file("---\nname: test\ndescription: |\n  literal\n  block\nlast_refreshed: 2026-01-01\n---\n")
        fm = parse_frontmatter(p)
        assert fm is not None
        assert "name" in fm
        assert "last_refreshed" in fm
        assert "description" not in fm

    def test_nonexistent_file(self, tmp_path):
        assert parse_frontmatter(tmp_path / "nope.md") is None

    def test_domain_cache_format(self, md_file):
        p = md_file("---\ndomain: cilium\nlast_refreshed: 2026-03-24\n---\n# Content\n")
        fm = parse_frontmatter(p)
        assert fm["domain"] == "cilium"
        assert fm["last_refreshed"] == "2026-03-24"


class TestValidateSkillFiles:
    def test_includes_dotclaude_skills(self, tmp_path, monkeypatch):
        """Maintenance skills under .claude/skills/ are validated."""
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "skills" / "a").mkdir(parents=True)
        (tmp_path / "skills" / "a" / "SKILL.md").write_text(
            "---\nname: a\ndescription: desc\n---\n"
        )
        # Maintenance skill missing required 'name' field
        (tmp_path / ".claude" / "skills" / "b").mkdir(parents=True)
        (tmp_path / ".claude" / "skills" / "b" / "SKILL.md").write_text(
            "---\ndescription: desc\n---\n"
        )
        errors = validate_skill_files()
        assert any(".claude" in e and "name" in e for e in errors)

    def test_valid_skills_no_errors(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "skills" / "x").mkdir(parents=True)
        (tmp_path / "skills" / "x" / "SKILL.md").write_text(
            "---\nname: x\ndescription: desc\n---\n"
        )
        (tmp_path / ".claude" / "skills" / "y").mkdir(parents=True)
        (tmp_path / ".claude" / "skills" / "y" / "SKILL.md").write_text(
            "---\nname: y\ndescription: desc\n---\n"
        )
        assert validate_skill_files() == []

    def test_empty_repo_no_errors(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        assert validate_skill_files() == []

    def test_block_scalar_description_accepted(self, tmp_path, monkeypatch):
        """SKILL.md with description: > block scalar passes validation."""
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        (tmp_path / "skills" / "x").mkdir(parents=True)
        (tmp_path / "skills" / "x" / "SKILL.md").write_text(
            "---\nname: x\ndescription: >\n  A multi-line description.\n---\n"
        )
        assert validate_skill_files() == []


class TestValidateReferenceFiles:
    def test_covers_multiple_skill_dirs(self, tmp_path, monkeypatch):
        """Reference files under any skills/*/references/ are validated."""
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        for skill in ("review-claude-config", "check-repo-health"):
            d = tmp_path / "skills" / skill / "references"
            d.mkdir(parents=True)
            (d / "ref.md").write_text(
                "---\nname: r\ndescription: d\nlast_refreshed: 2026-01-01\n---\n"
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

    def test_does_not_recurse_into_domain_cache(self, tmp_path, monkeypatch):
        """domain-cache/*.md files are not picked up by validate_reference_files."""
        monkeypatch.setattr(validate_schema, "REPO_ROOT", tmp_path)
        d = tmp_path / "skills" / "review-claude-config" / "references"
        d.mkdir(parents=True)
        (d / "ref.md").write_text(
            "---\nname: r\ndescription: d\nlast_refreshed: 2026-01-01\n---\n"
        )
        # domain-cache file lacks name/description — should NOT trigger reference validator
        cache = d / "domain-cache"
        cache.mkdir()
        (cache / "cilium.md").write_text("---\ndomain: cilium\nlast_refreshed: 2026-01-01\n---\n")
        errors = validate_reference_files()
        assert errors == []


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
        # Reference files
        refs = tmp_path / "skills" / "review-claude-config" / "references"
        refs.mkdir(parents=True)
        (refs / "ref.md").write_text(
            "---\nname: r\ndescription: d\nlast_refreshed: 2026-01-01\n---\n"
        )
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
