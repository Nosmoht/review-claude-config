r"""Tests for META-4 third-person description rubric item (issue #62).

META-4 bans first-person and second-person imperative in the frontmatter
description field of skills and agents. Source: Anthropic Skills best-practices
Warning block — "Always write in third person."

Patterns flagged (from scoring-rubric.md):
- First-person (case-sensitive on I): \bI\s, \bmy\s, \bme\s
- Second-person imperative (case-insensitive): \byou can\s, \byour\s

Grade boundary: META-4 fail → Metadata capped at C.
"""

import re

import pytest


# Patterns mirror scoring-rubric.md §"META-4 Third-Person Description".
FIRST_PERSON = re.compile(r"\b(I|my|me)\s")
SECOND_PERSON = re.compile(r"\b(you can|your)\s", re.IGNORECASE)


def is_third_person(description: str) -> bool:
    """Return True when description has no META-4 anti-patterns."""
    if FIRST_PERSON.search(description):
        return False
    if SECOND_PERSON.search(description):
        return False
    return True


class TestMETA4Pass:
    """Descriptions that comply with third-person rule."""

    @pytest.mark.parametrize(
        "desc",
        [
            "Evaluates MCP server configs and produces a quality certificate.",
            "Processes Excel files and generates reports.",
            "Analyzes Excel spreadsheets, creates pivot tables, generates charts.",
            "Extracts text and tables from PDF files.",
            "Use when reviewing MCP server configs. Do NOT use for agents.",
            "Scaffolds a new skill following the repo's quality patterns.",
            "Audits memory files for poisoning and staleness signals.",
        ],
    )
    def test_third_person_passes(self, desc):
        assert is_third_person(desc), f"expected PASS: {desc!r}"


class TestMETA4FailFirstPerson:
    """Anthropic-cited anti-pattern: first-person voice."""

    @pytest.mark.parametrize(
        "desc",
        [
            "I can help you process Excel files",
            "I help review skills.",
            "This is my skill for reviewing configs.",
            "Let me handle PDF extraction for you.",
        ],
    )
    def test_first_person_fails(self, desc):
        assert not is_third_person(desc), f"expected FAIL: {desc!r}"


class TestMETA4FailSecondPersonImperative:
    """Anthropic-cited anti-pattern: second-person imperative."""

    @pytest.mark.parametrize(
        "desc",
        [
            "You can use this to process Excel files",
            "You can invoke this skill when needed.",
            "Use this with your Excel workbook.",
            "Configures your deployment pipeline.",
        ],
    )
    def test_second_person_imperative_fails(self, desc):
        assert not is_third_person(desc), f"expected FAIL: {desc!r}"


class TestMETA4EdgeCases:
    """Lowercase i in words like 'is' / 'in' must not false-trigger."""

    @pytest.mark.parametrize(
        "desc",
        [
            "Generates reports when the input is malformed.",
            "Processes files in parallel and reports errors.",
            "Iterates across directories matching a glob pattern.",
            "Invokes /review-skill on each target.",
        ],
    )
    def test_lowercase_i_pronoun_free(self, desc):
        assert is_third_person(desc), f"expected PASS (no first-person): {desc!r}"


class TestMETA4RegexScope:
    """Regex must match as whole-word, not substring."""

    def test_me_inside_another_word(self):
        # "mentions" contains "me" but not as standalone pronoun
        assert is_third_person("Mentions the failure mode and reports the error.")

    def test_my_inside_another_word(self):
        # "myopia" starts with "my" but is not the pronoun
        assert is_third_person("Corrects myopia in evaluation heuristics.")

    def test_your_at_start(self):
        # "Your" capitalised at start of sentence still fails META-4
        assert not is_third_person("Your pipeline runs the skill for you.")
