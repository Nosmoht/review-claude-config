r"""Tests for Clarity C-test ambiguity markers (issue #66).

Extends the Clarity C-test with a binary-verifiable ambiguity marker:
- CLAR-2: pronouns referring to prior tool outputs have an explicit
  antecedent in the same clause.

Sources: arXiv:2507.11525 (ambiguity taxonomy F1=0.83 on Gemma 3 12B,
ROMAN 2025); arXiv:2512.14754 (IFEval++ / reliable@k, 61.8 % accuracy
drop on subtle constraint-wording nuances, ACL 2026).

CLAR-2 is LLM-binary in the rubric; these tests use a bare-verb+pronoun
heuristic as a deterministic proxy for unit-test purposes.

Regex constants and ``passes_clar2`` helper live in
``scripts/rubric_patterns.py`` so the deterministic runner and these
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
    passes_clar2,
)


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
    """Issue #66 explicit edge cases for the CLAR-2 proxy."""

    def test_bare_them_without_noun_phrase_fails_clar2(self):
        # Bare "process them" — verb directly followed by pronoun, no
        # intervening noun phrase → CLAR-2 proxy FAIL.
        assert not passes_clar2("process them")
