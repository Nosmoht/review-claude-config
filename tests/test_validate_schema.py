"""Tests for scripts/validate_schema.py — frontmatter and hooks.json validation."""

import json
import pathlib

import pytest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import validate_schema
from validate_schema import (
    parse_frontmatter,
    validate_date,
    validate_reference_files,
    validate_skill_files,
    DATE_RE,
)


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
