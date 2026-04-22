"""Shared rubric regex patterns and helpers.

Single source of truth for binary rubric-item patterns consumed by both
tests/ and scripts/rubric_binary_evaluator.py. Moving these constants
into one module keeps the deterministic runner and the unit tests from
drifting: a rubric refresh that edits a pattern here is picked up by
both consumers simultaneously.

Source: skills/review-claude-config/references/scoring-rubric.md
        section "Binary-Verifiable Rubric Items" (L93-188).

IMPORTANT: ``LOOP_PATTERN`` vs ``AGENTIC_LOOP_PATTERN`` asymmetry.

``until`` is a loop-CONTINUATION marker in COMP-W (where it serves as
termination-predicate text inside ``TERMINATION_PREDICATE``), but a
loop-TRIGGER marker in ``is_agentic()`` detection. The two constants
are therefore INTENTIONALLY DIFFERENT: ``LOOP_PATTERN`` does not list
``until`` and is byte-identical to the original pattern that shipped in
tests/test_comp_w_termination.py. ``AGENTIC_LOOP_PATTERN`` adds
``until`` per scoring-rubric.md L172.

Any rubric revision that changes this semantic MUST update both
constants in the same commit. ``TestSharedModuleParity`` pins the
exact ``.pattern`` strings so silent drift is detected.
"""

from __future__ import annotations

import re

# META-4 Third-Person Description (scoring-rubric.md L107).
# First-person is case-sensitive on capital I (lowercase i appears in
# English words like "is", "in", so \bI\s only catches standalone I).
FIRST_PERSON = re.compile(r"\b(I|my|me)\s")
SECOND_PERSON = re.compile(r"\b(you can|your)\s", re.IGNORECASE)


def is_third_person(description: str) -> bool:
    """Return True when description has no META-4 anti-patterns."""
    if FIRST_PERSON.search(description):
        return False
    if SECOND_PERSON.search(description):
        return False
    return True


# CLAR-1 Fuzzy-Quantifier-Free (scoring-rubric.md L113).
FUZZY_QUANTIFIER = re.compile(
    r"\b(slightly|a\s+bit|roughly|somewhat|some)\b",
    re.IGNORECASE,
)

# CLAR-2 proxy: bare action-verb directly followed by a bare pronoun.
# Rubric labels CLAR-2 as LLM-binary; this is the deterministic proxy
# used by the existing tests and reused by the runner.
BARE_PRONOUN_VERB = re.compile(
    r"\b(process|store|save|parse|fix|use|send|handle|return|format|"
    r"output|write|log|forward|retry|re-?run|commit|check)\s+"
    r"(it|them|that|this|those)\b",
    re.IGNORECASE,
)


def passes_clar1(text: str) -> bool:
    """Return True when the text contains no fuzzy quantifier."""
    return FUZZY_QUANTIFIER.search(text) is None


def passes_clar2(text: str) -> bool:
    """Return True when the text has no bare action-verb+pronoun pattern."""
    return BARE_PRONOUN_VERB.search(text) is None


# COMP-W Termination Criteria (scoring-rubric.md L129).
# LOOP_PATTERN does NOT include `until` (see module-level asymmetry note).
LOOP_PATTERN = re.compile(
    r"\b(for\s+each|retry|iterate|while\s+|loop)\b",
    re.IGNORECASE,
)

TERMINATION_PREDICATE = re.compile(
    r"\b(stop\s+when|terminate|halt|max.*iterations?|"
    r"escalate\s+after|loop\s+until|exit\s+(if|when)|stopping\s+condition|"
    r"retry\s+up\s+to|up\s+to\s+\d+\s+(times|attempts))\b",
    re.IGNORECASE,
)


def has_loop(text: str) -> bool:
    return LOOP_PATTERN.search(text) is not None


def has_termination(text: str) -> bool:
    return TERMINATION_PREDICATE.search(text) is not None


def passes_comp_w(body: str) -> bool:
    """COMP-W passes iff the body is non-iterative OR declares termination."""
    if not has_loop(body):
        return True
    return has_termination(body)


# Agentic-detection patterns (scoring-rubric.md L172).
# Branch 1: dispatch verbs — case-sensitive (Agent/Task are Anthropic
# tool names in PascalCase; subagent is lowercase convention).
AGENTIC_DISPATCH_PATTERN = re.compile(r"\b(Agent|Task|subagent)\b")

# Branch 2: loop verbs — includes `until` per L172. Full explicit
# alternation, NOT derived from LOOP_PATTERN.pattern (re.Pattern objects
# do not support the `|` operator, and string concatenation without a
# shared word boundary produces unanchored matches inside words like
# "untiltimely").
AGENTIC_LOOP_PATTERN = re.compile(
    r"\b(for\s+each|retry|iterate|while\s+|loop|until)\b",
    re.IGNORECASE,
)

# Branch 3: tools — exact-string membership set for `allowed-tools`.
AGENTIC_WRITE_TOOLS = frozenset({"Write", "Bash", "Edit"})


# PE-1 Reasoning-Model CoT-Scaffolding (scoring-rubric.md §Reasoning-Model
# Anti-Patterns). Opus 4.7 reasons natively at higher effort; explicit
# step-by-step scaffolding underperforms. `think carefully` alone is NOT
# matched (too generic in prose — "think carefully about tool choice" is
# legitimate reviewer instruction); only scaffolding-form directives.
PE_1_PATTERN = re.compile(
    r"\b(think\s+step\s+by\s+step|"
    r"reason\s+(?:step\s+by\s+step|carefully\s+about)|"
    r"let'?s\s+think(?:\s+(?:about|through))?)\b",
    re.IGNORECASE,
)

# PE-2 Reasoning-Model Hedge-Density (scoring-rubric.md §Reasoning-Model
# Anti-Patterns). Opus 4.7 interprets prompts literally; hedges in
# directives are interpreted as permission to skip. `as needed` is
# intentionally EXCLUDED — it collides with Anthropic's progressive-
# disclosure canonical phrasing ("loaded on demand as needed").
PE_2_PATTERN = re.compile(
    r"\b(try\s+to|if\s+possible|as\s+appropriate|when\s+useful)\b",
    re.IGNORECASE,
)

# Code-fence and inline-code stripping for PE-* checks. PE-1 and PE-2
# scan prose only — anti-pattern catalogs (boundary exemplars, rule
# templates, synthetic test artifacts in run-eval-cases) legitimately
# quote these phrases inside ```code blocks``` or `inline code`, and
# should not trigger a FAIL.
CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]+`")


def strip_code(text: str) -> str:
    """Remove fenced and inline code from text before PE-* matching."""
    text = CODE_FENCE.sub("", text)
    text = INLINE_CODE.sub("", text)
    return text


__all__ = [
    "FIRST_PERSON",
    "SECOND_PERSON",
    "is_third_person",
    "FUZZY_QUANTIFIER",
    "BARE_PRONOUN_VERB",
    "passes_clar1",
    "passes_clar2",
    "LOOP_PATTERN",
    "TERMINATION_PREDICATE",
    "has_loop",
    "has_termination",
    "passes_comp_w",
    "AGENTIC_DISPATCH_PATTERN",
    "AGENTIC_LOOP_PATTERN",
    "AGENTIC_WRITE_TOOLS",
    "PE_1_PATTERN",
    "PE_2_PATTERN",
    "CODE_FENCE",
    "INLINE_CODE",
    "strip_code",
]
