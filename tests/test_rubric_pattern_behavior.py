"""Behavioral tests for shared rubric regex patterns.

Replaces the prior ``TestSharedModuleParity`` byte-equality drift check with
parametrized positive / boundary / negative cases per pattern. Behavioral
tests catch refactor drift (intent change) AND semantic bugs (behavior change);
byte-equality caught only the former.

Source of truth: ``scripts/rubric_patterns.py`` (cite the exact pattern + its
scoring-rubric.md anchor in each class docstring).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from rubric_patterns import (  # noqa: E402
    AGENTIC_DISPATCH_PATTERN,
    AGENTIC_LOOP_PATTERN,
    BARE_PRONOUN_VERB,
    FIRST_PERSON,
    FUZZY_QUANTIFIER,
    LOOP_PATTERN,
    PE_1_PATTERN,
    PE_2_PATTERN,
    SECOND_PERSON,
    TERMINATION_PREDICATE,
)


class TestFirstPersonPattern:
    """META-4: ``\\b(I|my|me)\\s`` — case-sensitive on the standalone "I"
    (lowercase "i" is a common letter inside English words and would
    over-match)."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("I am the reviewer", True),
            ("my approach is", True),
            ("me first", True),
            ("Italy is a country", False),  # "I" inside word → no match
            ("It is a thing", False),  # "I" in "It" → no \s after
            ("I'm shortened", False),  # apostrophe is not \s
            ("you are nice", False),
            ("she did", False),
            ("", False),
        ],
        ids=lambda v: repr(v) if isinstance(v, str) else v,
    )
    def test_match(self, text, expected):
        assert bool(FIRST_PERSON.search(text)) is expected

    def test_lowercase_i_does_not_match(self):
        """Lowercase i appears in 'is', 'in' etc. — must not over-match."""
        assert FIRST_PERSON.search("it is in") is None


class TestSecondPersonPattern:
    """META-4: ``\\b(you can|your)\\s`` — case-INsensitive."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("you can do it", True),
            ("You Can RUN it", True),  # case-insensitive
            ("your approach is", True),
            ("YOUR responsibility", True),
            ("she said your stuff", True),
            ("youcan no space", False),  # word-boundary required
            ("your", False),  # \s required after
            ("they can do it", False),
            ("", False),
        ],
        ids=lambda v: repr(v) if isinstance(v, str) else v,
    )
    def test_match(self, text, expected):
        assert bool(SECOND_PERSON.search(text)) is expected


class TestFuzzyQuantifierPattern:
    """CLAR-1: ``\\b(slightly|a\\s+bit|roughly|somewhat|some)\\b``,
    case-INsensitive."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("fetch slightly more data", True),
            ("Slightly used", True),  # case-insensitive
            ("fetch a bit of data", True),
            ("a    bit of whitespace", True),  # \s+ allows multiple
            ("roughly 10 records", True),
            ("somewhat unusual", True),
            ("some stuff", True),
            ("fetch 10 records", False),
            ("slightlymisspelled", False),  # word boundary required
            ("abitofamatch", False),
            ("", False),
        ],
        ids=lambda v: repr(v) if isinstance(v, str) else v,
    )
    def test_match(self, text, expected):
        assert bool(FUZZY_QUANTIFIER.search(text)) is expected


class TestBarePronounVerbPattern:
    """CLAR-2 proxy: action verb directly followed by a bare pronoun.

    Pattern is case-INsensitive. ``re-?run`` allows both ``rerun`` and
    ``re-run``. The verb list is fixed and exhaustive — additions need a
    rubric change."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("process them", True),
            ("Process Them", True),  # case-insensitive
            ("store it", True),
            ("retry that", True),
            ("re-run them", True),  # hyphen allowed
            ("rerun them", True),  # hyphen optional
            ("forward this", True),
            ("fix that bug", True),
            ("commit them", True),
            ("process the data", False),  # noun, not pronoun
            ("use the API", False),
            ("output to stderr", False),  # no pronoun
            ("them is plural", False),  # no preceding verb
            ("", False),
        ],
        ids=lambda v: repr(v) if isinstance(v, str) else v,
    )
    def test_match(self, text, expected):
        assert bool(BARE_PRONOUN_VERB.search(text)) is expected


class TestLoopPattern:
    """COMP-W: ``\\b(for\\s+each|retry|iterate|while\\s+|loop)\\b``.

    Critically does NOT include ``until`` — that is a continuation /
    termination marker, not a loop trigger. The ``until``-aware sibling
    is ``AGENTIC_LOOP_PATTERN`` for is_agentic() detection."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("for each item", True),
            ("For Each item", True),  # case-insensitive
            ("retry on failure", True),
            ("iterate through results", True),
            ("while running", True),
            ("loop until done", True),
            ("until convergence", False),  # 'until' NOT in LOOP_PATTERN
            ("foreach without space", False),  # \s+ required
            ("retried in past tense", False),  # \b boundary
            ("", False),
        ],
        ids=lambda v: repr(v) if isinstance(v, str) else v,
    )
    def test_match(self, text, expected):
        assert bool(LOOP_PATTERN.search(text)) is expected

    def test_until_is_NOT_in_loop_pattern(self):
        """Anchor the documented asymmetry vs AGENTIC_LOOP_PATTERN. If a
        future refactor adds 'until' here it must also revisit
        rubric_patterns.py module-level docstring.
        """
        assert LOOP_PATTERN.search("until done") is None


class TestTerminationPredicatePattern:
    """COMP-W: long alternation of termination markers, case-INsensitive."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("stop when condition", True),
            ("Stop When Condition", True),
            ("terminate after 5", True),
            ("halt processing", True),
            ("max 5 iterations", True),
            ("max 10 iteration", True),  # ? after s allows singular
            ("escalate after 3 failures", True),
            ("loop until done", True),
            ("exit if error", True),
            ("exit when ready", True),
            ("stopping condition met", True),
            ("retry up to 3 times", True),
            ("up to 5 attempts", True),
            ("no termination signal here", False),
            ("retries forever", False),
            ("", False),
        ],
        ids=lambda v: repr(v) if isinstance(v, str) else v,
    )
    def test_match(self, text, expected):
        assert bool(TERMINATION_PREDICATE.search(text)) is expected


class TestAgenticDispatchPattern:
    """``\\b(Agent|Task|subagent)\\b`` — case-SENSITIVE.

    Anthropic's tool names are PascalCase (``Agent``, ``Task``); ``subagent``
    is the lowercase prose convention. Lowercase ``agent`` and ``task`` are
    common English nouns and would over-match."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("use the Agent tool", True),
            ("dispatch a Task", True),
            ("subagent runs", True),
            ("agent of change", False),  # lowercase intentional miss
            ("task force", False),
            ("Subagent", False),  # case-sensitive on prose form
            ("AgentSmith", False),  # \b prevents inside-word match
            ("the Agent.", True),  # \b matches before non-word char
            ("", False),
        ],
        ids=lambda v: repr(v) if isinstance(v, str) else v,
    )
    def test_match(self, text, expected):
        assert bool(AGENTIC_DISPATCH_PATTERN.search(text)) is expected


class TestAgenticLoopPattern:
    """Same as LOOP_PATTERN but ALSO includes ``until``. Asymmetry is
    intentional — see rubric_patterns.py module docstring."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("for each x", True),
            ("retry until done", True),
            ("iterate over", True),
            ("while waiting", True),
            ("loop here", True),
            ("until done", True),  # the key delta vs LOOP_PATTERN
            ("Until Done", True),  # case-insensitive
            ("untiltimely without space", False),  # \b required
            ("non-iterative code", False),
            ("", False),
        ],
        ids=lambda v: repr(v) if isinstance(v, str) else v,
    )
    def test_match(self, text, expected):
        assert bool(AGENTIC_LOOP_PATTERN.search(text)) is expected


class TestPE1Pattern:
    """Reasoning-model anti-pattern: scaffolding directives only.

    Bare ``think carefully`` does NOT match — it's a legitimate reviewer
    instruction. Only matches when paired with scaffolding form (``step by
    step``, ``carefully about X``, ``let's think about/through``)."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("think step by step", True),
            ("Think Step By Step about it", True),
            ("reason step by step", True),
            ("reason carefully about X", True),
            ("let's think about Y", True),
            ("let's think through Z", True),
            ("Let's think", True),  # bare 'let's think' matches
            ("think carefully", False),  # bare 'think carefully' must NOT match
            ("step-by-step guide", False),  # no 'think'/'reason' verb
            ("", False),
        ],
        ids=lambda v: repr(v) if isinstance(v, str) else v,
    )
    def test_match(self, text, expected):
        assert bool(PE_1_PATTERN.search(text)) is expected


class TestPE2Pattern:
    """Reasoning-model anti-pattern: hedge words in directives.

    ``as needed`` is intentionally EXCLUDED — collides with Anthropic's
    progressive-disclosure phrasing (``loaded on demand as needed``)."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("try to do this", True),
            ("Try To attempt", True),
            ("if possible, do X", True),
            ("as appropriate", True),
            ("when useful, log", True),
            ("as needed", False),  # documented exclusion
            ("loaded as needed", False),
            ("must do this", False),
            ("", False),
        ],
        ids=lambda v: repr(v) if isinstance(v, str) else v,
    )
    def test_match(self, text, expected):
        assert bool(PE_2_PATTERN.search(text)) is expected
