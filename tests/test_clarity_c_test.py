r"""Tests for Clarity C-test ambiguity markers (issue #66).

Extends the Clarity C-test with two binary-verifiable ambiguity markers:
- CLAR-1: step parameters free of fuzzy quantifiers ("slightly", "a bit",
  "some", "roughly", "somewhat").
- CLAR-2: pronouns referring to prior tool outputs have an explicit
  antecedent in the same clause.

Sources: arXiv:2507.11525 (ambiguity taxonomy F1=0.83 on Gemma 3 12B,
ROMAN 2025); arXiv:2512.14754 (IFEval++ / reliable@k, 61.8 % accuracy
drop on subtle constraint-wording nuances, ACL 2026).

CLAR-1 is regex-verifiable (tested here).
CLAR-2 is LLM-binary in the rubric; these tests use a bare-verb+pronoun
heuristic as a deterministic proxy for unit-test purposes.

Grade boundary: CLAR-1 ✗ OR CLAR-2 ✗ → Clarity capped at C.

Regex constants and ``passes_clar1``/``passes_clar2`` helpers now live
in ``scripts/rubric_patterns.py`` so the deterministic runner and these
tests share a single source of truth.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from rubric_patterns import (  # noqa: E402, F401
    BARE_PRONOUN_VERB,
    FUZZY_QUANTIFIER,
    passes_clar1,
    passes_clar2,
)


class TestCLAR1Pass:
    """Step parameters with exact numeric values — CLAR-1 passes."""

    @pytest.mark.parametrize(
        "text",
        [
            "fetch 10 entries",
            "reduce the window by 2 turns",
            "retry 3 times on HTTP 503",
            "process all files matching *.md",
            "move the cursor left by 4 pixels",
        ],
    )
    def test_exact_quantifier_passes(self, text):
        assert passes_clar1(text), f"expected PASS: {text!r}"


class TestCLAR1Fail:
    """Step parameters with fuzzy quantifiers — CLAR-1 fails."""

    @pytest.mark.parametrize(
        "text",
        [
            "fetch roughly 10 entries",
            "slightly reduce the window",
            "a bit later than the previous step",
            "process some files in the directory",
            "retry somewhat more aggressively",
        ],
    )
    def test_fuzzy_quantifier_fails(self, text):
        assert not passes_clar1(text), f"expected FAIL: {text!r}"


class TestCLAR1WordBoundary:
    """Word-boundary scoping — substrings in longer words must not false-trigger."""

    @pytest.mark.parametrize(
        "text",
        [
            "produce an awesome result",
            "something changed during the run",
            "the handsome output was clean",
            "a lonesome match remained",
        ],
    )
    def test_substring_in_longer_word_passes(self, text):
        assert passes_clar1(text), f"expected PASS (boundary): {text!r}"


class TestCLAR2Pass:
    """Pronouns with explicit antecedents in the same clause — CLAR-2 passes."""

    @pytest.mark.parametrize(
        "text",
        [
            "parse the grep output; store the matches in results.json",
            "fetch the entries; return the entries sorted by date",
            "process the raw response; save the response to disk",
        ],
    )
    def test_resolved_pronoun_passes(self, text):
        assert passes_clar2(text), f"expected PASS: {text!r}"


class TestCLAR2Fail:
    """Bare action-verb directly followed by a bare pronoun — CLAR-2 fails."""

    @pytest.mark.parametrize(
        "text",
        [
            "parse the output; then process them",
            "fetch the entries; store it in results.json",
            "run the linter; fix them in-place",
            "re-run the command; check that for errors",
        ],
    )
    def test_bare_pronoun_verb_fails(self, text):
        assert not passes_clar2(text), f"expected FAIL: {text!r}"


class TestCLARCombinedEdgeCases:
    """Issue #66 explicit edge cases: 'some' quantifier vs pronoun-adjacent."""

    def test_some_as_quantifier_fails_clar1(self):
        # "1 some file" — "some" sits between numeric counter and noun,
        # functioning as a fuzzy quantifier → CLAR-1 FAIL.
        assert not passes_clar1("1 some file should be renamed")

    def test_some_plus_them_quantifier_fails_clar1(self):
        # "fix some of them" — "some" is a fuzzy quantifier → CLAR-1 FAIL.
        # CLAR-2 (unresolved antecedent for "them") is LLM-binary in the
        # rubric; the regex proxy here does not catch verb+noun-phrase+
        # pronoun shapes. Only the deterministic CLAR-1 check is asserted.
        assert not passes_clar1("fix some of them")

    def test_bare_them_without_noun_phrase_fails_clar2(self):
        # Bare "process them" — verb directly followed by pronoun, no
        # intervening noun phrase → CLAR-2 proxy FAIL.
        assert not passes_clar2("process them")
