r"""Tests for COMP-W termination-criteria rubric item (issue #64).

COMP-W requires skills/agents with iterative or looped workflows to
declare an explicit termination predicate distinct from COMP-X success.

Verification is two-step:
1. Detect loop language (for each / retry / iterate / while / loop).
2. When detected, require a termination-predicate match.

If step 1 is negative (no loop language), COMP-W is not applicable and
the skill passes trivially.

Sources:
- arXiv:2503.13657 (MAST) — task-verification-and-termination cluster.
- arXiv:2603.29231 (Beyond pass@1) — Meltdown Onset Point reliability.
- arXiv:2509.25370 (AgentErrorTaxonomy / AgentDebug) — failure annotation.

Grade boundary: COMP-W ✗ → Completeness capped at C.

Regex constants and ``has_loop``/``has_termination``/``passes_comp_w``
helpers now live in ``scripts/rubric_patterns.py`` so the deterministic
runner and these tests share a single source of truth. COMP-W
``LOOP_PATTERN`` intentionally omits ``until`` (see the module-level
asymmetry note in rubric_patterns.py); the agentic branch uses a
separate ``AGENTIC_LOOP_PATTERN`` that includes it.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from rubric_patterns import (  # noqa: E402, F401
    LOOP_PATTERN,
    TERMINATION_PREDICATE,
    has_loop,
    has_termination,
    passes_comp_w,
)


class TestCOMPWPassNonIterative:
    """Non-iterative skills — COMP-W not applicable, pass trivially."""

    @pytest.mark.parametrize(
        "body",
        [
            "Parse the input file and produce a JSON report.",
            "Read the config; emit a summary to stdout.",
            "Take one input path; write one output path.",
            "Evaluate the skill body against the rubric.",
        ],
    )
    def test_non_iterative_passes(self, body):
        assert passes_comp_w(body), f"expected PASS (no loop): {body!r}"


class TestCOMPWPassIterativeWithPredicate:
    """Iterative skills that declare an explicit termination predicate."""

    @pytest.mark.parametrize(
        "body",
        [
            "Retry on HTTP 503 up to 3 times; escalate after 3 consecutive failures.",
            "Loop until convergence: merge two runs; stop when delta is zero.",
            "For each file, parse and validate; halt on first schema violation.",
            "Iterate over candidates with max 5 iterations, then terminate.",
            "While queue is non-empty, drain; exit when queue length reaches 0.",
        ],
    )
    def test_iterative_with_termination_passes(self, body):
        assert has_loop(body), "sanity: body must be iterative"
        assert passes_comp_w(body), f"expected PASS: {body!r}"


class TestCOMPWFailIterativeNoPredicate:
    """Iterative skills that lack an explicit termination predicate."""

    @pytest.mark.parametrize(
        "body",
        [
            "Retry on failure.",
            "For each path, process and write output.",
            "Iterate over the candidates.",
            "While there are items in the queue, dequeue and handle.",
            "Loop over the entries until the job completes.",
        ],
    )
    def test_iterative_without_termination_fails(self, body):
        assert has_loop(body), "sanity: body must be iterative"
        assert not passes_comp_w(body), f"expected FAIL: {body!r}"


class TestCOMPWEdgeCases:
    """Regex scoping and false-positive guards."""

    def test_word_boundary_retry(self):
        # "pretty" contains "retry" as substring — word boundary blocks it.
        assert passes_comp_w("Produce a pretty output summary.")

    def test_word_boundary_loop(self):
        # "loopback" and "sloop" must not trigger the loop pattern.
        assert passes_comp_w("Connect to the loopback interface and exit.")

    def test_termination_predicate_without_loop_is_noop(self):
        # "terminate" without loop language doesn't force the skill to have loops.
        assert passes_comp_w("Terminate gracefully on SIGINT.")

    def test_loop_until_counts_as_termination(self):
        # "loop until" is both loop-language and termination predicate —
        # the "until" clause self-terminates.
        text = "Loop until convergence detected."
        assert has_loop(text)
        assert passes_comp_w(text)

    def test_escalate_after_satisfies_termination(self):
        # Explicit max-attempt escalation covers COMP-W.
        text = "Retry on 503; escalate after 3 consecutive failures."
        assert not passes_comp_w("Retry on 503."), "sanity: bare retry fails"
        assert passes_comp_w(text)
