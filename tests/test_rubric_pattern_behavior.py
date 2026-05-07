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
    _inside_hitl_cycle,
    build_peer_agent_re,
    strip_code_preserve_lines,
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


class TestInsideHitlCycle:
    """Boundary cases for ``_inside_hitl_cycle`` (issue #139). Mirrors
    the empirically-verified RL-3b residuals at:
      - skills/{develop-hooks,scaffold-agent,scaffold-rule}/SKILL.md (Adjust handler)
      - skills/scaffold-skill/SKILL.md L149 (Option list) + L209 (Adjust handler)
    """

    def test_positive_match_quoted_adjust_handler(self):
        """R1 case 1 — positive match (Adjust handler with regenerate)."""
        body = 'On "Adjust": ask what to change, regenerate, and show again.'
        offset = body.index("regenerate")
        assert _inside_hitl_cycle(body, offset) is True

    def test_negative_outside_cycle(self):
        """R1 case 2 — no handler prefix, plain regenerate."""
        body = 'The agent will regenerate the file on each invocation.'
        offset = body.index("regenerate")
        assert _inside_hitl_cycle(body, offset) is False

    def test_negative_handler_not_adjust(self):
        """R1 case 3 — handler is "Cancel"/"Failure"/"Continue" (NOT in whitelist).
        Critical for preventing Scenario-B bypass: ``On "Failure": retry`` must NOT NA.
        """
        body = 'On "Failure": retry indefinitely until success.'
        offset = body.index("retry")
        assert _inside_hitl_cycle(body, offset) is False

    def test_positive_match_multiline_preview_block(self):
        """R1 case 4 — handler on one line, trigger on later line.
        100-char window crosses newlines (intentional: bullet-list HITL flows).
        """
        body = 'On "Adjust":\n  - regenerate the spec\n  - show the preview again.'
        offset = body.index("regenerate")
        assert _inside_hitl_cycle(body, offset) is True

    def test_negative_offset_before_handler(self):
        """R1 case 5 — trigger appears before the handler prefix in text."""
        body = 'regenerate the file. On "Adjust": ask what to change.'
        offset = body.index("regenerate")
        assert _inside_hitl_cycle(body, offset) is False

    # ---- Revision-2 additions (Team-Red R1 findings) ----

    def test_negative_lowercase_on_does_not_match(self):
        """Revision 2 — `on "adjust"` (lowercase) must NOT match.
        Guards against IGNORECASE drift; `On` is hard-cased.
        """
        body = 'we rely on "adjust" mode: regenerate everything.'
        offset = body.index("regenerate")
        assert _inside_hitl_cycle(body, offset) is False

    def test_negative_paragraph_break_terminates_lookback(self):
        """Revision 2 (Team-Red Scenario C) — a `\\n\\n` paragraph break
        between handler and trigger blocks cross-paragraph contamination.
        """
        body = 'On "Adjust": confirm the spec.\n\nIf degraded, regenerate everything.'
        offset = body.index("regenerate")
        assert _inside_hitl_cycle(body, offset) is False

    # ---- Revision-3 additions (Team-Red R2 findings) ----

    def test_negative_crlf_paragraph_break_terminates_lookback(self):
        """Revision 3 (Team-Red R2 Blocker 2) — CRLF-encoded paragraph
        breaks (`\\r\\n\\r\\n`) must also terminate lookback. Guards against
        Windows-encoded SKILL.md slipping through.
        """
        body = 'On "Adjust": confirm the spec.\r\n\r\nIf degraded, regenerate everything.'
        offset = body.index("regenerate")
        assert _inside_hitl_cycle(body, offset) is False

    def test_negative_whitespace_blank_line_terminates_lookback(self):
        """Revision 3 — a blank line containing only whitespace (`\\n   \\n`)
        is also a paragraph break.
        """
        body = 'On "Adjust": confirm.\n   \nregenerate the index.'
        offset = body.index("regenerate")
        assert _inside_hitl_cycle(body, offset) is False


# ---------------------------------------------------------------------------
# SF-3 helpers: strip_code_preserve_lines + build_peer_agent_re.
# ---------------------------------------------------------------------------


class TestSF3PeerAgentPattern:
    """Behavioral tests for SF-3 pattern helpers.

    Source of truth: scoring-rubric.md §SF-3 (Binary-Evaluated Items) +
    rubric_patterns.py ``strip_code_preserve_lines`` / ``build_peer_agent_re``.
    """

    # ----------------------------------------------------------------
    # Dynamic discovery finds sibling agents.
    # ----------------------------------------------------------------
    def test_dynamic_discovery_finds_sibling_agents(self, tmp_path):
        """Three sibling agents → frozenset has 3 names (excluding self)."""
        import pathlib

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
        from rubric_binary_evaluator import discover_peer_agent_names, parse_frontmatter

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        subject = agents_dir / "subject.md"
        subject.write_text("---\nname: subject\n---\nbody\n", encoding="utf-8")
        for name in ("alpha", "beta", "gamma"):
            (agents_dir / f"{name}.md").write_text(
                f"---\nname: {name}\n---\nbody\n", encoding="utf-8"
            )
        names = discover_peer_agent_names(subject)
        assert names == frozenset({"alpha", "beta", "gamma"})

    # ----------------------------------------------------------------
    # Self name excluded from peer set.
    # ----------------------------------------------------------------
    def test_self_name_excluded(self, tmp_path):
        """Own `name:` not in discovery output (but sibling is)."""
        import pathlib

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
        from rubric_binary_evaluator import discover_peer_agent_names

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        subject = agents_dir / "me.md"
        subject.write_text("---\nname: me\n---\nbody\n", encoding="utf-8")
        (agents_dir / "other.md").write_text("---\nname: other\n---\nbody\n", encoding="utf-8")
        names = discover_peer_agent_names(subject)
        assert "me" not in names
        assert "other" in names

    # ----------------------------------------------------------------
    # Long names take precedence over short in alternation.
    # ----------------------------------------------------------------
    def test_long_names_take_precedence_over_short(self):
        """Regex sorts longest-first so `review-perspective-clarity` matches
        before `reviewer` in a body containing both tokens.
        """
        names = frozenset({"review-perspective-clarity", "reviewer"})
        pattern = build_peer_agent_re(names)
        assert pattern is not None
        body = "Dispatch review-perspective-clarity for analysis, then reviewer."
        m = pattern.search(body)
        assert m is not None
        assert m.group(0) == "review-perspective-clarity"

    # ----------------------------------------------------------------
    # Hyphen boundary excludes mid-word match.
    # ----------------------------------------------------------------
    def test_hyphen_boundary_excludes_in_word_match(self):
        """'pre-reviewer-mode' must NOT match 'reviewer'."""
        names = frozenset({"reviewer"})
        pattern = build_peer_agent_re(names)
        assert pattern is not None
        assert pattern.search("pre-reviewer-mode") is None

    # ----------------------------------------------------------------
    # strip_code_preserve_lines: line offsets preserved across fence.
    # ----------------------------------------------------------------
    def test_strip_code_preserve_lines_keeps_offsets(self):
        """Content outside fence has the same line number in raw and stripped."""
        raw = "line1\n```python\ncode\n```\nline5\n"
        stripped = strip_code_preserve_lines(raw)
        # "line5" must be at line 5 in both.
        raw_line = raw[: raw.index("line5")].count("\n") + 1
        stripped_line = stripped[: stripped.index("line5")].count("\n") + 1
        assert raw_line == stripped_line == 5

    # ----------------------------------------------------------------
    # strip_code_preserve_lines: tilde fence.
    # ----------------------------------------------------------------
    def test_strip_code_preserve_lines_handles_tilde_fence(self):
        """~~~ fenced block is stripped equivalently to ``` block."""
        raw = "before\n~~~\ncode\n~~~\nafter\n"
        stripped = strip_code_preserve_lines(raw)
        raw_line_after = raw[: raw.index("after")].count("\n") + 1
        stripped_line_after = stripped[: stripped.index("after")].count("\n") + 1
        assert raw_line_after == stripped_line_after

    # ----------------------------------------------------------------
    # Unclosed fence does not cascade-skip remaining content.
    # ----------------------------------------------------------------
    def test_unclosed_fence_does_not_cascade_skip(self):
        """Body with unbalanced opening fence (no closing ```).
        DOTALL+MULTILINE requires a matching closing token.
        Content after the unclosed fence remains in the stripped output.
        """
        raw = "before\n```\ncode without close\nafter\n"
        stripped = strip_code_preserve_lines(raw)
        # No match → stripped == raw (nothing removed).
        assert "after" in stripped

    # ----------------------------------------------------------------
    # Discovery skips names shorter than 3 or longer than 64.
    # ----------------------------------------------------------------
    def test_discovery_skips_short_and_long_names(self, tmp_path):
        """Name len=1 → excluded; len=3 → included; len=65 → excluded."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
        from rubric_binary_evaluator import discover_peer_agent_names

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        subject = agents_dir / "subject.md"
        subject.write_text("---\nname: subject\n---\nbody\n", encoding="utf-8")
        (agents_dir / "short.md").write_text("---\nname: a\n---\nbody\n", encoding="utf-8")
        (agents_dir / "ok.md").write_text("---\nname: abc\n---\nbody\n", encoding="utf-8")
        (agents_dir / "toolong.md").write_text(
            f"---\nname: {'x' * 65}\n---\nbody\n", encoding="utf-8"
        )
        names = discover_peer_agent_names(subject)
        assert "a" not in names
        assert "abc" in names
        assert "x" * 65 not in names

    # ----------------------------------------------------------------
    # Discovery capped at 50 siblings.
    # ----------------------------------------------------------------
    def test_discovery_capped_at_50_siblings(self, tmp_path):
        """60 siblings → frozenset has exactly 50."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
        from rubric_binary_evaluator import discover_peer_agent_names

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        subject = agents_dir / "subject.md"
        subject.write_text("---\nname: subject\n---\nbody\n", encoding="utf-8")
        for i in range(60):
            name = f"s{i:02d}"
            (agents_dir / f"sib-{i:02d}.md").write_text(
                f"---\nname: {name}\n---\nbody\n", encoding="utf-8"
            )
        names = discover_peer_agent_names(subject)
        assert len(names) == 50
