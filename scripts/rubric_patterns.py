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
``until`` per scoring-rubric.md L181.

Any rubric revision that changes this semantic MUST update both
constants in the same commit. ``TestSharedModuleParity`` pins the
exact ``.pattern`` strings so silent drift is detected.
"""

from __future__ import annotations

import re

# META-4 Third-Person Description (scoring-rubric.md L108).
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


# CLAR-1 Fuzzy-Quantifier-Free (scoring-rubric.md L114).
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
    """Return True when the text has no bare action-verb+pronoun pattern.

    Antecedent-aware (issue #104): a match is ignored when:
      * the same sentence opens with an antecedent-introducing connective
        (``If X, ... use it`` / ``Otherwise, ...`` / ``When X, ...`` /
        ``Once X, ...``) that has a top-level comma before the pair;
      * the trailing token is ``that|this|those`` used as a determiner
        (followed by a noun-like word — ``Use that contract's schema``);
      * the match falls inside a backtick-quoted span on the same line
        (option labels, illustrative code).
    """
    for match in BARE_PRONOUN_VERB.finditer(text):
        if _is_determiner_usage(text, match):
            continue
        if _has_local_antecedent(text, match.start()):
            continue
        if _inside_backticks(text, match.start()):
            continue
        return False
    return True


# A short closed-class list of common prepositions and conjunctions
# that, if they immediately follow ``that|this|those``, mean the latter
# is a pronoun, not a determiner — the next word is structural, not a
# noun head. (``check that for errors`` → pronoun, not determiner.)
_NON_NOUN_FOLLOWERS = frozenset(
    {
        "for",
        "to",
        "in",
        "of",
        "on",
        "by",
        "with",
        "from",
        "at",
        "as",
        "into",
        "onto",
        "upon",
        "and",
        "or",
        "but",
        "is",
        "are",
        "was",
        "were",
        "will",
        "can",
        "could",
        "should",
        "would",
        "must",
        "the",
        "a",
        "an",
    }
)


def _is_determiner_usage(text: str, match: "re.Match[str]") -> bool:
    """Return True when the matched pronoun is ``that|this|those`` followed
    by a lowercase noun-head token — i.e., a determiner phrase, not a
    bare pronoun reference. ``it``/``them`` are always pronouns and are
    not excluded by this check.

    Heuristic: the pronoun is treated as a determiner when the next word
    is a lowercase token AND that next word is not in
    ``_NON_NOUN_FOLLOWERS`` (prepositions, conjunctions, copulas, modals,
    articles), since those introduce a structural continuation rather
    than a noun head.
    """
    pronoun = match.group(2).lower()
    if pronoun not in {"that", "this", "those"}:
        return False
    next_token_match = re.match(
        r"\s+(?:[`\"']?)([a-z][\w-]*)",
        text[match.end() : match.end() + 24],
    )
    if not next_token_match:
        return False
    next_token = next_token_match.group(1).lower()
    return next_token not in _NON_NOUN_FOLLOWERS


# Sentence boundary: previous `.`, `!`, `?`, newline, or string start.
_SENTENCE_START = re.compile(r"[\.!?\n]|\Z")


def _sentence_window_start(text: str, offset: int) -> int:
    """Return the index of the start of the sentence containing ``offset``.

    Only treat ``.``/``!``/``?`` as terminators when followed by whitespace
    + capital letter (skips abbreviations like ``e.g.``, ``i.e.``, ``cf.``).
    Newlines remain unconditional terminators."""
    start = 0
    # Newlines are unconditional sentence terminators.
    for m in re.finditer(r"\n", text[:offset]):
        start = m.end()
    # Period/!/? followed by whitespace + capital letter (or end of string).
    for m in re.finditer(r"[\.!?]\s+(?=[A-Z])", text[:offset]):
        if m.end() > start:
            start = m.end()
    return start


def _has_local_antecedent(text: str, offset: int) -> bool:
    """Return True when the sentence containing ``offset`` opens with an
    antecedent-introducing connective (``If X, ...`` / ``Otherwise, ...``
    / ``When X, ...`` / ``Once X, ...``) that precedes the verb+pronoun
    pair — providing a clear antecedent.

    Detection is two-stage to tolerate commas inside parenthetical
    examples (``e.g., "A", "B"``):
      1. The sentence-opening connective is one of ``if|when|otherwise|once``.
      2. A comma occurs between the connective and the verb+pronoun pair
         that is NOT inside parentheses or brackets.

    Also accepts em-dash separators (``INCOMPLETE — re-run that category``)
    when the segment before the dash names a clear noun-phrase subject.
    """
    sentence_start = _sentence_window_start(text, offset)
    window = text[sentence_start:offset]
    # Stage 1: match a sentence-opening connective in the prefix window.
    if re.search(
        r"^\s*(?:[-*#`>\s]+)?\b(if|when|otherwise|once)\b",
        window,
        re.IGNORECASE,
    ):
        # Stage 2: require a top-level comma between connective and offset.
        if _has_top_level_comma(window):
            return True
    # Em-dash construct: ``... — verb pronoun`` after a noun-phrase
    # subject in the same line. We accept any em-dash (``—`` U+2014) or
    # double-hyphen ``--`` separator preceded by a word ending in a noun
    # within the current sentence.
    if re.search(r"[—–]|--", window):
        if re.search(
            r"\b\w+\s*(?:[—–]|--)\s*\S{0,40}$",
            window,
        ):
            return True
    return False


def _has_top_level_comma(window: str) -> bool:
    """Return True when ``window`` contains a comma outside of ()/[] depth."""
    depth = 0
    for ch in window:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            return True
    return False


def _inside_backticks(text: str, offset: int) -> bool:
    """Return True when ``offset`` falls inside a backtick-quoted span on
    the same line. Counts unescaped backticks before ``offset`` on the
    current line; an odd count means we are inside a span."""
    line_start = text.rfind("\n", 0, offset) + 1
    line_prefix = text[line_start:offset]
    return line_prefix.count("`") % 2 == 1


# Issue #139 — RL-3b NA filter for HITL preview-confirm cycles.
#
# Conservative whitelist approach: only matches option-handler prefixes whose
# label is in the adjust-class set OR the "Option <list>" pattern. This
# prevents false-negative bypass on labels like ``On "Failure":`` that
# wrap genuine autonomous retry loops.
HITL_OPTION_HANDLER = re.compile(
    r"On\s+(?:"
    # Branch 1: quoted adjust-class label (whitelist). Curly + ASCII quotes.
    # Inline (?i:...) flag scopes case-insensitivity to the label only — `On`
    # itself is hard-cased so prose-internal `on` does not match.
    r"[\"“'](?i:Adjust|Modify|Edit|Change|Refine)[\"”']"
    r"|"
    # Branch 2: unquoted "Option <N>[, <N>]*[, or <Word>]?" list pattern.
    # Mirrors scaffold-skill L149: ``On Option 2, 3, or Other:``.
    r"Option\s+\d+(?:\s*,\s*\d+)*(?:\s*,?\s*or\s+\w+)?"
    r")\s*:\s*",
)  # NB: NO global re.IGNORECASE — keeps `On`/`Option` case-sensitive.


# Paragraph-break detection — handles LF, CRLF, and whitespace-only blank lines.
_PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\r?\n")


def _inside_hitl_cycle(text: str, offset: int) -> bool:
    """Return True when ``offset`` is preceded within 100 characters by an
    option-handler prefix matching ``HITL_OPTION_HANDLER`` — indicating the
    surrounding directive is a user-driven preview-confirm branch
    (Apply / Adjust / Cancel) rather than an autonomous retry loop.

    Mirrors the architectural pattern of issue #105's ``_inside_backticks``
    filter (same module, L229–235) and #103's table-cell pattern.

    Whitelist (issue #139): the accepted handler labels are exactly
        Branch 1 (quoted): {Adjust, Modify, Edit, Change, Refine}
        Branch 2 (unquoted Option list): ``Option <N>[, <N>]*[, or <Word>]?``
    A handler with ANY OTHER label (e.g., ``On "Failure":``, ``On "Tweak":``)
    is NOT treated as HITL. To extend the whitelist, edit
    ``HITL_OPTION_HANDLER`` and add a regression test for the new label
    against an autonomous-retry counter-example (mirroring
    ``test_RL_3b_hitl_filter_does_NOT_bypass_failure_handler``).

    Window calibration: 100 chars gives ~75% margin over the empirically
    longest gap (57 chars at scaffold-skill L209, verified 2026-05-02).
    A paragraph break (LF-LF, CRLF-CRLF, or blank-line-with-whitespace)
    inside the window terminates the lookback so cross-paragraph
    contamination cannot smuggle a HITL prefix into an unrelated retry
    directive. Two consecutive blank lines (``\\n\\n\\n``) are treated as
    a deliberate section break and also terminate lookback.
    """
    window_start = max(0, offset - 100)
    window = text[window_start:offset]
    # Last paragraph-break inside the window terminates lookback. Handles
    # LF-LF, CRLF-CRLF, and blank-line-with-whitespace forms.
    last_break_end = -1
    for m in _PARAGRAPH_BREAK.finditer(window):
        last_break_end = m.end()
    if last_break_end != -1:
        window = window[last_break_end:]
    return HITL_OPTION_HANDLER.search(window) is not None


# COMP-W Termination Criteria (scoring-rubric.md L133).
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


# Agentic-detection patterns (scoring-rubric.md L181).
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


# WS-2b Conditional-Specificity-with-Marker (scoring-rubric.md — issue #70).
# `If present / If absent` within 500 chars AFTER a block marker must have a
# preceding prose predicate within 400 chars BEFORE the marker that names the
# marker context.
WS_2B_BLOCK_MARKER = re.compile(r"^---[a-z_-]+---$", re.MULTILINE)
WS_2B_IF_CLAUSE = re.compile(r"\bIf\s+(present|absent)\b", re.IGNORECASE)
WS_2B_PROSE_PREDICATE = re.compile(
    r"(check|test|determine|examine|inspect|look\s+for|see\s+whether)"
    r"\s+(whether|if|for)\s+[^.]{0,120}?"
    r"(block|marker|fence|section|metadata|prompt|frontmatter)",
    re.IGNORECASE,
)
WS_2B_MARKER_WINDOW = 500  # chars from block marker end to If clause start
WS_2B_PREDICATE_WINDOW = 400  # chars before marker for prose predicate

# WS-5b Negation + Positive-Whitelist binary check (issue #89, promoted from
# WS-5 narrative). Truong et al. arXiv:2306.08189 — LLMs are negation-insensitive;
# pair every prohibition with an adjacent positive whitelist within 200 chars.
# Step 1 trigger: NEVER / DO NOT / MUST NOT followed by an optional verb-class
# token, then a colon-or-space-separated comma-list (≥2 items).
WS_5B_NEGATIVE_LIST = re.compile(
    r"\b(NEVER|DO NOT|MUST NOT)\b\s+"
    r"(use|run|invoke|execute|call|include|emit|write|read|allow|permit)?"
    r"[:\s]+\S+(?:\s*,\s*\S+)+"
)
# Step 2 whitelist signal within ±200 chars of the trigger match.
WS_5B_POSITIVE_WHITELIST = re.compile(
    r"\b(ALLOWED|allowed|permitted|use\s+only|read[-\s]?only|operations\s+only|whitelist)\b[:\s]"
    r"|\b(only|exclusively)\s+(read|allow|permit|use)\b",
    re.IGNORECASE,
)
WS_5B_WINDOW = 200  # chars before AND after the negative-list match

# WS-6 Quantifier-Range-Anchor (issue #93). Talmor oLMpics arXiv:1912.13283 —
# context-dependent quantifier reasoning. Comparators must be paired with
# a numeric value or unit within 80 chars after the match.
WS_6_COMPARATOR = re.compile(
    r"\b(more|fewer|older|newer|larger|smaller|less|greater|higher|lower)\s+than\b",
    re.IGNORECASE,
)
WS_6_ANCHOR = re.compile(
    r"\d+"
    r"|\bdays?\b|\bhours?\b|\bfiles?\b|\blines?\b|\btokens?\b|\bbytes?\b|\bMB\b|\bKB\b|\bchars?\b"
    r"|exceeds|below|above\s+\d+|threshold",
    re.IGNORECASE,
)
WS_6_ANCHOR_WINDOW = 80

# COMP-V Verifiable-Predicate (issue #96). IFEval arXiv:2311.07911 — verifiable
# instruction types. Each success/completion criterion must contain a
# programmatically-verifiable component within 200 chars.
COMP_V_TRIGGER = re.compile(
    r"\b(complete|success|done|valid|pass(?:es|ing)?)\s+when\b",
    re.IGNORECASE,
)
COMP_V_ANCHOR = re.compile(
    r"\b\d+\b"
    r"|\bregex\b|matches?\s+\^|matches\s+pattern"
    r"|exit(?:\s+code)?\s*[=:]?\s*0|exit(?:s)?\s+0|returns?\s+0|\bnon[-\s]?zero\b"
    r"|\bschema\b|\bfrontmatter\b|required\s+field|JSON\s+valid"
    r"|`make\s+\w+`\s+(passes|succeeds|exits)|`\w+`\s+returns?",
    re.IGNORECASE,
)
COMP_V_WINDOW = 200


def passes_ws_2b(body: str) -> bool:
    """Return True when every `If present / If absent` occurrence in body is
    either (a) not within 500 chars after a block marker (NA per-occurrence) or
    (b) preceded by a prose predicate within 400 chars before the marker.

    Operates on raw body (no ``strip_code``) because block markers often live
    inside fenced YAML examples and must remain discoverable. Inline-code
    matches are filtered via marker-adjacency: a bare ``If present`` inside
    backticks is only flagged if it also happens to sit within 500 chars of a
    real block marker, which is vanishingly unusual.

    Returns True when the body contains NO `If present / If absent` in-scope
    occurrences (empty-set universal quantifier). Callers that need to
    distinguish NA from PASS should inspect ``check_WS_2b`` in
    ``rubric_binary_evaluator.py``.
    """
    markers = list(WS_2B_BLOCK_MARKER.finditer(body))
    if not markers:
        return True
    for m in WS_2B_IF_CLAUSE.finditer(body):
        preceding_markers = [mk for mk in markers if mk.end() <= m.start()]
        if not preceding_markers:
            continue
        nearest = preceding_markers[-1]
        if m.start() - nearest.end() > WS_2B_MARKER_WINDOW:
            continue
        window_start = max(0, nearest.start() - WS_2B_PREDICATE_WINDOW)
        window_end = nearest.start()
        if not WS_2B_PROSE_PREDICATE.search(body[window_start:window_end]):
            return False
    return True


# RD-5b Step-Naming-Consistency (scoring-rubric.md — issue #70).
# Detect step-naming schemes and require a mapping clause with mapping verb
# + 2+ scheme tokens when ≥2 schemes are present.
RD_5B_PHASE = re.compile(r"^#+\s+Phase\s+\d+\b", re.MULTILINE | re.IGNORECASE)
RD_5B_STEP_LETTER = re.compile(r"^#+\s+Step\s+[A-Z]", re.MULTILINE)
# heading depth ≤ 3 to exclude certificate-template `#### 1. [Title]` subsections.
RD_5B_STEP_NUMBER = re.compile(r"^#{1,3}\s+\d+(\.\d+)?\.\s+", re.MULTILINE)
RD_5B_DOTTED = re.compile(r"\*\*[a-z]\.\d+")
RD_5B_MAPPING_VERB = re.compile(
    r"(contains|within|inside|decomposes\s+into|maps\s+to|→|->|"
    r"composed\s+of|consists\s+of|broken\s+into)",
    re.IGNORECASE,
)
RD_5B_SCHEME_TOKENS = [
    re.compile(r"Phase\s+\d+", re.IGNORECASE),
    re.compile(r"Step\s+[A-Z]"),
    re.compile(r"Step\s+\d+", re.IGNORECASE),
    re.compile(r"\bb\.\d+"),
]
RD_5B_MAPPING_WINDOW = 200  # chars for mapping-clause scan


def rd_5b_schemes_present(body: str) -> list[str]:
    """Return names of scheme patterns found in body."""
    schemes: list[str] = []
    if RD_5B_PHASE.search(body):
        schemes.append("PHASE")
    if RD_5B_STEP_LETTER.search(body):
        schemes.append("STEP_LETTER")
    if RD_5B_STEP_NUMBER.search(body):
        schemes.append("STEP_NUMBER")
    if RD_5B_DOTTED.search(body):
        schemes.append("DOTTED")
    return schemes


def rd_5b_has_mapping_clause(body: str) -> bool:
    """Return True when body contains a sentence with a mapping verb AND 2+
    distinct scheme tokens within ``RD_5B_MAPPING_WINDOW`` chars.
    """
    for verb_match in RD_5B_MAPPING_VERB.finditer(body):
        window_start = max(0, verb_match.start() - RD_5B_MAPPING_WINDOW)
        window_end = min(len(body), verb_match.end() + RD_5B_MAPPING_WINDOW)
        window = body[window_start:window_end]
        schemes_in_window = sum(1 for p in RD_5B_SCHEME_TOKENS if p.search(window))
        if schemes_in_window >= 2:
            return True
    return False


def passes_rd_5b(body: str) -> bool:
    """Return True when body uses a single step scheme OR has a mapping clause
    when multiple schemes are present.
    """
    schemes = rd_5b_schemes_present(body)
    if len(schemes) <= 1:
        return True
    return rd_5b_has_mapping_clause(body)


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
    "WS_2B_BLOCK_MARKER",
    "WS_2B_IF_CLAUSE",
    "WS_2B_PROSE_PREDICATE",
    "WS_2B_MARKER_WINDOW",
    "WS_2B_PREDICATE_WINDOW",
    "passes_ws_2b",
    "RD_5B_PHASE",
    "RD_5B_STEP_LETTER",
    "RD_5B_STEP_NUMBER",
    "RD_5B_DOTTED",
    "RD_5B_MAPPING_VERB",
    "RD_5B_SCHEME_TOKENS",
    "RD_5B_MAPPING_WINDOW",
    "rd_5b_schemes_present",
    "rd_5b_has_mapping_clause",
    "passes_rd_5b",
]
