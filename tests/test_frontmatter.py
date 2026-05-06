"""Tests for scripts/_frontmatter.py — frontmatter parsing primitives."""

from __future__ import annotations

import datetime
import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from _frontmatter import (
    DATE_RE,
    DESCRIPTION_MIN_LEN,
    StrictStringsLoader,
    _validate_description,
    parse_frontmatter,
    validate_date,
)


class TestDateRegex:
    @pytest.mark.parametrize("valid", ["2026-01-01", "2026-12-31", "2000-06-15"])
    def test_valid_dates(self, valid):
        assert DATE_RE.match(valid)

    @pytest.mark.parametrize(
        "invalid",
        [
            "2026-1-01",  # missing zero-pad month
            "2026-01-1",  # missing zero-pad day
            "2026-4-5",  # both missing
            "26-01-01",  # 2-digit year
            "2026/01/01",  # wrong separator
            "20260101",  # no separators
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

    # Negative test #3 (plan §Negative-test enumeration):
    # Proves Feb-30 path survived extraction from validate_schema.py.
    def test_validate_date_feb_30_still_caught(self, tmp_path):
        """Feb-30 must remain caught after extraction to _frontmatter.py.

        Catches accidental fall-through to schema regex only (which allows
        any syntactically-valid date string but cannot reject impossible dates).
        """
        errors = validate_date("2026-02-30", tmp_path / "f.md", "last_refreshed")
        assert len(errors) == 1
        assert "not a valid date" in errors[0]

    def test_non_string_input_fails_gracefully(self, tmp_path):
        """Reject non-string inputs with a clear type-error message rather
        than crashing on regex match.
        """
        errors = validate_date(datetime.date(2026, 1, 1), tmp_path / "f.md", "last_refreshed")
        assert len(errors) == 1
        assert "expected str" in errors[0]

    def test_non_string_int_input(self, tmp_path):
        errors = validate_date(2026, tmp_path / "f.md", "last_refreshed")
        assert len(errors) == 1
        assert "expected str" in errors[0]
        assert "int" in errors[0]


class TestStrictStringsLoader:
    """The custom Loader keeps timestamp + bool scalars as raw strings.

    Without this, PyYAML coerces ``2026-01-01`` to ``datetime.date`` and
    ``true``/``yes`` to ``bool``, which silently bypasses the strict
    YYYY-MM-DD format check and corrupts string-expecting consumers.
    """

    def test_timestamp_kept_as_string(self):
        result = yaml.load("last_refreshed: 2026-01-01", Loader=StrictStringsLoader)
        assert isinstance(result["last_refreshed"], str)
        assert result["last_refreshed"] == "2026-01-01"

    def test_bool_kept_as_string(self):
        result = yaml.load("disable-model-invocation: true", Loader=StrictStringsLoader)
        assert isinstance(result["disable-model-invocation"], str)
        assert result["disable-model-invocation"] == "true"

    def test_yes_no_kept_as_string(self):
        """YAML 1.1 treats yes/no/on/off as bool; loader must keep them str."""
        result = yaml.load("flag: yes", Loader=StrictStringsLoader)
        assert isinstance(result["flag"], str)
        assert result["flag"] == "yes"

    def test_strict_loader_does_not_pollute_default_safeloader(self):
        """Override is on the subclass, not global. SafeLoader keeps default
        coercion semantics so other consumers are unaffected.
        """
        result = yaml.load("d: 2026-01-01", Loader=yaml.SafeLoader)
        # default SafeLoader still coerces timestamps to datetime.date
        assert isinstance(result["d"], datetime.date)


class TestParseFrontmatter:
    def test_valid_frontmatter(self, md_file):
        p = md_file(
            "---\nname: test\ndescription: a thing that is at least twenty chars long\nlast_refreshed: 2026-01-01\n---\n# Body\n"
        )
        fm = parse_frontmatter(p)
        assert fm == {
            "name": "test",
            "description": "a thing that is at least twenty chars long",
            "last_refreshed": "2026-01-01",
        }

    def test_no_frontmatter(self, md_file):
        p = md_file("# Just a heading\n")
        assert parse_frontmatter(p) is None

    def test_empty_file(self, md_file):
        p = md_file("")
        assert parse_frontmatter(p) is None

    def test_block_scalar_folded_parsed(self, md_file):
        """Folded block scalar (``description: >``) is now parsed, not skipped."""
        p = md_file("---\nname: test\ndescription: >\n  multi\n  line\nlast_refreshed: 2026-01-01\n---\n")
        fm = parse_frontmatter(p)
        assert fm is not None
        assert fm["name"] == "test"
        assert fm["last_refreshed"] == "2026-01-01"
        # YAML folded scalar joins with single space, terminates with newline
        assert fm["description"] == "multi line\n"

    def test_block_scalar_literal_parsed(self, md_file):
        p = md_file("---\nname: test\ndescription: |\n  literal\n  block\nlast_refreshed: 2026-01-01\n---\n")
        fm = parse_frontmatter(p)
        assert fm is not None
        assert fm["description"] == "literal\nblock\n"

    def test_dashes_with_extra_chars(self, md_file):
        """First line must be exactly ``---``."""
        p = md_file("---yaml\nname: test\n---\n")
        assert parse_frontmatter(p) is None

    def test_nonexistent_file(self, tmp_path):
        assert parse_frontmatter(tmp_path / "nope.md") is None

    def test_domain_cache_format(self, md_file):
        p = md_file("---\ndomain: cilium\nlast_refreshed: 2026-03-24\n---\n# Content\n")
        fm = parse_frontmatter(p)
        assert fm["domain"] == "cilium"
        # Critical: timestamp must remain a string for DATE_RE downstream.
        assert isinstance(fm["last_refreshed"], str)
        assert fm["last_refreshed"] == "2026-03-24"

    def test_truncated_frontmatter_no_closing_marker(self, md_file):
        """No closing `---` on its own line → return None."""
        p = md_file("---\nname: test\ndescription: thing\n# body without closing\n")
        assert parse_frontmatter(p) is None

    def test_malformed_yaml_returns_none(self, md_file):
        """Tab-indented content rejected by PyYAML scanner → return None."""
        p = md_file("---\n\tname: tabbed\n\tdescription: bad indent\n---\n")
        assert parse_frontmatter(p) is None

    def test_empty_frontmatter_returns_empty_dict(self, md_file):
        """Empty `---\\n---` returns `{}` (not None)."""
        p = md_file("---\n---\n# body\n")
        fm = parse_frontmatter(p)
        assert fm == {}

    def test_utf8_bom_handled(self, tmp_path):
        """Files with a UTF-8 BOM are handled."""
        p = tmp_path / "bom.md"
        p.write_bytes(
            b"\xef\xbb\xbf---\nname: bom\ndescription: a description that meets the min length\nlast_refreshed: 2026-01-01\n---\n"
        )
        fm = parse_frontmatter(p)
        assert fm is not None
        assert fm["name"] == "bom"

    def test_unquoted_date_kept_as_string(self, md_file):
        """Real research/domain-cache files have unquoted dates."""
        p = md_file("---\nlast_refreshed: 2026-04-03\n---\n")
        fm = parse_frontmatter(p)
        assert isinstance(fm["last_refreshed"], str)
        assert fm["last_refreshed"] == "2026-04-03"

    def test_bool_kept_as_string(self, md_file):
        """``disable-model-invocation: true`` must stay as literal string."""
        p = md_file("---\ndisable-model-invocation: true\n---\n")
        fm = parse_frontmatter(p)
        assert isinstance(fm["disable-model-invocation"], str)
        assert fm["disable-model-invocation"] == "true"

    def test_inline_list_parsed_as_list(self, md_file):
        """JSON-style flow lists become Python lists."""
        p = md_file("---\ntools: [Read, Grep, Glob]\n---\n")
        fm = parse_frontmatter(p)
        assert fm["tools"] == ["Read", "Grep", "Glob"]

    def test_dash_list_parsed_as_list(self, md_file):
        p = md_file("---\nsources:\n  - one\n  - two\n---\n")
        fm = parse_frontmatter(p)
        assert fm["sources"] == ["one", "two"]

    def test_quoted_argument_hint_stays_string(self, md_file):
        """``argument-hint: "[folder] [--validation]"`` stays a single string."""
        p = md_file('---\nargument-hint: "[folder] [--validation]"\n---\n')
        fm = parse_frontmatter(p)
        assert fm["argument-hint"] == "[folder] [--validation]"
        assert isinstance(fm["argument-hint"], str)

    def test_top_level_list_returns_none(self, md_file):
        """Frontmatter must be a mapping. A YAML list at top level is rejected."""
        p = md_file("---\n- one\n- two\n---\n")
        assert parse_frontmatter(p) is None

    def test_description_with_yaml_comment_in_value(self, md_file):
        """Real bug: ``description: #45551 ...`` — YAML parses ``#`` as comment."""
        p = md_file("---\nname: x\ndescription: #45551 explanation\nlast_refreshed: 2026-01-01\n---\n")
        fm = parse_frontmatter(p)
        assert fm is not None
        # PyYAML correctly treats # as comment start; description becomes None.
        assert fm["description"] is None


def test_description_min_len_is_reasonable():
    """Lock the threshold value so a future bump is an explicit decision."""
    assert DESCRIPTION_MIN_LEN == 20
