"""Tests for scripts/validate_schema.py — frontmatter and hooks.json validation."""

import json
import pathlib

import pytest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from validate_schema import parse_frontmatter, validate_date, DATE_RE


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
