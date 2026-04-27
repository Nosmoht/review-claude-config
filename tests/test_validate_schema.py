"""Tests for scripts/validate_schema.py — frontmatter and hooks.json validation."""

import json
import os
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import validate_schema
from validate_schema import (
    DATE_RE,
    DESCRIPTION_MIN_LEN,
    StrictStringsLoader,
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
            "2026-4-5",     # both missing
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

    def test_non_string_input_fails_gracefully(self, tmp_path):
        """Reject non-string inputs with a clear type-error message rather
        than crashing on regex match. Guards against future regressions if
        the StrictStringsLoader override is removed or new YAML coercion is
        introduced upstream.
        """
        import datetime
        errors = validate_date(
            datetime.date(2026, 1, 1), tmp_path / "f.md", "last_refreshed"
        )
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
        import datetime
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
        """Folded block scalar (``description: >``) is now parsed, not skipped.

        Previously the hand-rolled parser dropped block scalars and a raw-text
        workaround papered over the gap. After PyYAML migration the content is
        parsed correctly, which is what enables real description-quality
        checks (min-length, future structure checks).
        """
        p = md_file(
            "---\nname: test\ndescription: >\n  multi\n  line\nlast_refreshed: 2026-01-01\n---\n"
        )
        fm = parse_frontmatter(p)
        assert fm is not None
        assert fm["name"] == "test"
        assert fm["last_refreshed"] == "2026-01-01"
        # YAML folded scalar joins with single space, terminates with newline
        assert fm["description"] == "multi line\n"

    def test_block_scalar_literal_parsed(self, md_file):
        p = md_file(
            "---\nname: test\ndescription: |\n  literal\n  block\nlast_refreshed: 2026-01-01\n---\n"
        )
        fm = parse_frontmatter(p)
        assert fm is not None
        assert fm["description"] == "literal\nblock\n"

    def test_dashes_with_extra_chars(self, md_file):
        """First line must be exactly ``---``. ``---yaml`` is not a valid
        opener — preserves backwards compatibility with any non-frontmatter
        files that happen to start with `---`-prefixed content.
        """
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
        """No closing `---` on its own line → return None (treated as missing
        frontmatter rather than misparsing the entire body as YAML).
        """
        p = md_file("---\nname: test\ndescription: thing\n# body without closing\n")
        assert parse_frontmatter(p) is None

    def test_malformed_yaml_returns_none(self, md_file):
        """Tab-indented content rejected by PyYAML scanner → return None
        rather than raising. Preserves the existing 'missing YAML frontmatter'
        error path for messy inputs.
        """
        p = md_file("---\n\tname: tabbed\n\tdescription: bad indent\n---\n")
        assert parse_frontmatter(p) is None

    def test_empty_frontmatter_returns_empty_dict(self, md_file):
        """Empty `---\\n---` returns `{}` (not None) so validators emit the
        more useful 'missing required field' error rather than 'missing YAML
        frontmatter'.
        """
        p = md_file("---\n---\n# body\n")
        fm = parse_frontmatter(p)
        assert fm == {}

    def test_utf8_bom_handled(self, tmp_path):
        """Files with a UTF-8 BOM are handled — Windows editors sometimes
        emit a BOM and we should not silently treat the file as having no
        frontmatter.
        """
        p = tmp_path / "bom.md"
        # Write BOM + frontmatter explicitly in bytes
        p.write_bytes(
            b"\xef\xbb\xbf---\nname: bom\ndescription: a description that meets the min length\nlast_refreshed: 2026-01-01\n---\n"
        )
        fm = parse_frontmatter(p)
        assert fm is not None
        assert fm["name"] == "bom"

    def test_unquoted_date_kept_as_string(self, md_file):
        """Real research/domain-cache files have unquoted dates. Verify the
        Loader keeps them as strings so DATE_RE can assert strict format.
        """
        p = md_file("---\nlast_refreshed: 2026-04-03\n---\n")
        fm = parse_frontmatter(p)
        assert isinstance(fm["last_refreshed"], str)
        assert fm["last_refreshed"] == "2026-04-03"

    def test_bool_kept_as_string(self, md_file):
        """``disable-model-invocation: true`` (used in 16+ skills) must stay
        as the literal string 'true', not a Python bool.
        """
        p = md_file("---\ndisable-model-invocation: true\n---\n")
        fm = parse_frontmatter(p)
        assert isinstance(fm["disable-model-invocation"], str)
        assert fm["disable-model-invocation"] == "true"

    def test_inline_list_parsed_as_list(self, md_file):
        """JSON-style flow lists become Python lists. Documents type contract
        for downstream consumers (any code reading frontmatter must handle
        list-typed values, e.g. for ``tools: [Read, Grep]``).
        """
        p = md_file("---\ntools: [Read, Grep, Glob]\n---\n")
        fm = parse_frontmatter(p)
        assert fm["tools"] == ["Read", "Grep", "Glob"]

    def test_dash_list_parsed_as_list(self, md_file):
        p = md_file("---\nsources:\n  - one\n  - two\n---\n")
        fm = parse_frontmatter(p)
        assert fm["sources"] == ["one", "two"]

    def test_quoted_argument_hint_stays_string(self, md_file):
        """``argument-hint: "[folder] [--validation]"`` (real pattern in many
        SKILL.md files) — the outer quotes mean PyYAML treats it as a single
        string, not a list. Pin this to catch a future drift to unquoted form.
        """
        p = md_file(
            '---\nargument-hint: "[folder] [--validation]"\n---\n'
        )
        fm = parse_frontmatter(p)
        assert fm["argument-hint"] == "[folder] [--validation]"
        assert isinstance(fm["argument-hint"], str)

    def test_top_level_list_returns_none(self, md_file):
        """Frontmatter must be a mapping. A YAML list at top level is
        rejected — guards against accidental ``---\\n- item\\n---`` patterns.
        """
        p = md_file("---\n- one\n- two\n---\n")
        assert parse_frontmatter(p) is None

    def test_description_with_yaml_comment_in_value(self, md_file):
        """Real bug discovered during migration: ``description: #45551 ...``
        — YAML parses ``#`` as comment-start so description becomes None.
        Captured here so the validator catches future re-introductions.
        """
        p = md_file(
            "---\nname: x\ndescription: #45551 explanation\nlast_refreshed: 2026-01-01\n---\n"
        )
        fm = parse_frontmatter(p)
        assert fm is not None
        # PyYAML correctly treats # as comment start; description becomes None.
        assert fm["description"] is None


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
        # Reference files
        refs = tmp_path / "skills" / "review-claude-config" / "references"
        refs.mkdir(parents=True)
        (refs / "ref.md").write_text(
            "---\nname: r\ndescription: a description that meets the minimum length\nlast_refreshed: 2026-01-01\n---\n"
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


def test_description_min_len_is_reasonable():
    """Lock the threshold value so a future bump to 100 is an explicit
    decision, not a silent change.
    """
    assert DESCRIPTION_MIN_LEN == 20
