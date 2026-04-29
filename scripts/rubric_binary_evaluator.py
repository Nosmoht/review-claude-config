#!/usr/bin/env python3
"""Deterministic binary-rubric evaluator for Claude Code skills and agents.

Produces PASS / FAIL / NA verdicts for 28 binary-verifiable rubric items
against a single skill or agent artifact. Written JSON to stdout. Moves
regex execution out of the LLM prompt so every perspective reviewer sees
byte-identical verdicts, eliminating the ~80% run-to-run variance
observed in the /review-skill convergence retest.

Scope:
  * skills/<name>/SKILL.md — all 28 items evaluated (full scope).
  * agents/*.md — 26 items evaluated; COMP-X and META-3b return NA
    because the rubric clauses encode skill-semantics (review-skill
    convergence predicate; skills/*/SKILL.md sibling glob). Full
    agent-semantic coverage (TC-3 for COMP-X analogue, agent-namespace
    sibling policy for META-3b) is tracked under issue #75 (perspective
    ownership) + issue #76 (merge ITEM_DIMENSION extension).
  * rules/plugins — not yet supported; may return spurious verdicts on
    checks that detect cross-primitive context.

Usage:
    python3 scripts/rubric_binary_evaluator.py <absolute-artifact-path>

Exit codes:
    0 — evaluator ran, stats.runner_error == 0 (all 28 items produced a
        verdict). Also used by argparse --help per GNU convention, which
        downstream consumers disambiguate by checking for the
        "schema_version" key in stdout JSON.
    2 — evaluator ran, stats.runner_error > 0 (at least one per-item
        check raised an exception and degraded to NA).
    1 — global crash (bad argv, unreadable file, JSON serialisation
        failure). Stdout still carries {"runner_error": "<msg>",
        "verdicts": {}}; stderr carries the traceback.

Schema-version forward-compat contract (currently schema_version=1):
    Non-breaking (no bump): adding a new item to verdicts, adding new
        keys under evidence.<item> (consumers MUST tolerate unknowns),
        adding new counters to stats.
    Breaking (bump): removing or renaming a rubric item, changing a
        verdict enum value, changing stats counter semantics.

Important invariants documented in this module and enforced by tests:
    * LOOP_PATTERN vs AGENTIC_LOOP_PATTERN asymmetry: see
      rubric_patterns.py module docstring. `until` is a loop-trigger
      for agentic detection but a loop-continuation marker in COMP-W.
    * RL-9b fires on a narrower sub-predicate than the 3-branch
      is_agentic() (see needs_rl9b() below).
    * Inline `## Hard Rules` section counts as body; separate
      references/*.md files are NOT resolved (known limitation).

Source of truth: skills/review-claude-config/references/scoring-rubric.md
    section "Binary-Verifiable Rubric Items" (L93-188).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import traceback

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from rubric_patterns import (  # noqa: E402
    AGENTIC_DISPATCH_PATTERN,
    AGENTIC_LOOP_PATTERN,
    AGENTIC_WRITE_TOOLS,
    BARE_PRONOUN_VERB,
    FUZZY_QUANTIFIER,
    PE_1_PATTERN,
    PE_2_PATTERN,
    WS_2B_BLOCK_MARKER,
    WS_2B_IF_CLAUSE,
    WS_2B_MARKER_WINDOW,
    WS_2B_PREDICATE_WINDOW,
    WS_2B_PROSE_PREDICATE,
    WS_5B_NEGATIVE_LIST,
    WS_5B_POSITIVE_WHITELIST,
    WS_5B_WINDOW,
    has_loop,
    is_third_person,
    passes_clar1,
    passes_clar2,
    passes_comp_w,
    rd_5b_has_mapping_clause,
    rd_5b_schemes_present,
    strip_code,
)

SCHEMA_VERSION = 1

# ---------------------------------------------------------------------------
# Runner-only regex constants (patterns not shared with tests/).
# Every pattern below mirrors a rubric line cited in the comment.
# ---------------------------------------------------------------------------

# META-2 (rubric L104).
META_2_PATTERN = re.compile(r"do ?not use|not for|skip (when|if)", re.IGNORECASE)

# META-3a (rubric L105) — exclusion.
META_3A_EXCLUSION = re.compile(r"as needed|if appropriate|when useful", re.IGNORECASE)

# CLAR-3 (rubric L115) — universal quantifier: every trigger must pair
# with a recovery within 200 chars.
CLAR_3_TRIGGER = re.compile(r"\b(abort|refuse|bail|halt|timeout)\b", re.IGNORECASE)
CLAR_3_RECOVERY = re.compile(
    r"(status\s*[:=]\s*(terminal|partial|missing|failure|success)|"
    r"write\s+[^.]{0,80}\s+stub|append\s+[^.]{0,80}\s+to\s+|"
    r"fall\s?back\s+to|continue\s+to\s+(step|b\.)|retry\s+with|"
    r"report\s+and\s+(stop|exit|terminate)|terminal\s+(stop|state|action)|"
    r"NONE\s*[—-]\s*terminal)",
    re.IGNORECASE,
)

# CLAR-4 (rubric L116).
CLAR_4_DEPENDENCY = re.compile(
    r"(depends on|after step \d|after b\.\d|requires output of)",
    re.IGNORECASE,
)
CLAR_4_FAILURE_BRANCH = re.compile(
    r"\bif\b[^.]{0,200}?(fails?|missing|unavailable|stubbed)",
    re.IGNORECASE,
)
CLAR_4_FALLBACK_HEADING = re.compile(
    r"^\s*#+\s*(Error Handling|Degraded Mode|Fallback)\b",
    re.IGNORECASE | re.MULTILINE,
)

# CE-X (rubric L122).
CE_X_TRIGGER = re.compile(
    r"(conversation history|summariz(e|ation)|compact(ion)?)",
    re.IGNORECASE,
)
CE_X_JUSTIFICATION = re.compile(
    r"(masking|irreversible|cannot be masked|"
    r"justif(y|ied|ication)[^.]{0,80}summariz)",
    re.IGNORECASE,
)

# COMP-X (rubric L126).
COMP_X_SUCCESS = re.compile(r"complete when|success when|done when", re.IGNORECASE)
COMP_X_CONVERGENCE = re.compile(
    r"re-run variance|identical finding|<=\s*\d+[-\s]letter\s*Δ",
    re.IGNORECASE,
)
COMP_X_PRIMARY_VERB = re.compile(
    r"\b(reviews?|audits?|classify|classifies|"
    r"evaluates?|scores?|certify|certifies)\b",
    re.IGNORECASE,
)
COMP_X_NAME_TOKENS = frozenset({"review", "audit", "classify", "evaluate", "score", "certify"})

# COMP-Y (rubric L127).
COMP_Y_EXCLUSION = re.compile(r"looks good|seems correct|appears valid", re.IGNORECASE)
COMP_Y_BINARY = re.compile(r"(verify|validate|check|assert|count|match)", re.IGNORECASE)

# COMP-Z (rubric L128).
COMP_Z_PATTERN = re.compile(
    r"evidence|citation|quote|verified against",
    re.IGNORECASE,
)

# SAMP-1 / SAMP-2 (rubric L142/L143).
SAMPLING_PARAM = re.compile(r"\b(temperature|top_p|top_k)\s*[:=]", re.IGNORECASE)

# SP-2b (rubric L149).
SP_2B_BINDING = re.compile(
    r"(restricted to|allowlisted|limited to|scoped to|"
    r"policy[-_ ]?gate|used only for|invoked only when|"
    r"guarded by|Read-only|read\s+only)",
    re.IGNORECASE,
)
READ_ONLY_TOOLS = frozenset({"Read", "Glob", "Grep", "NotebookRead", "WebSearch"})

# Mutating tools that require SP-2b per-tool binding.
MUTATING_TOOLS = frozenset({"Write", "Edit", "Bash", "Agent", "WebFetch"})

# SP-4b (rubric L150).
SP_4B_CONSTRAINT = re.compile(
    r"(restricted|limited|scoped|allowlist(ed)?|confined|must not)\s+"
    r"(to|for|outside|beyond)\s+[^.]{0,200}?"
    r"(path|directory|folder|command|script|subagent_type|"
    r"url|domain|allowlist)",
    re.IGNORECASE,
)
TIER_A_PARTNERS = frozenset({"Bash", "Agent", "WebFetch"})

# IJ-1b (rubric L151-154).
IJ_1B_VALIDATION = re.compile(
    r"(validate|matches|conforms?|conforms\s+to|format|pattern|regex)"
    r"\s+[^.]{0,200}?"
    r"(\$ARGUMENTS|repo[-_ ]?slug|path|url|input|argument|"
    r"[`'\"]\^.*\$[`'\"])",
    re.IGNORECASE,
)
IJ_1B_WRITE_GATE = re.compile(
    r"(AskUserQuestion|preview|confirm|approval|ExitPlanMode)"
    r"[^.]{0,400}?"
    r"(Write|Edit|create|overwrite|append|save)",
    re.IGNORECASE | re.DOTALL,
)
EXTERNAL_INPUT_MARKERS = re.compile(
    r"\$ARGUMENTS|repo[-_ ]?slug|user-supplied|fetched URL|MCP-tool output",
    re.IGNORECASE,
)

# RL-1b (rubric L174-177) — three OR-joined alternatives.
RL_1B_NUMERIC = re.compile(
    r"\b(<=\s*\d+|≤\s*\d+|"
    r"max(imum)?\s+(wait|duration|depth|iterations?|retries?|turns?|calls?)?"
    r"\s*(of\s+)?\d+\s*"
    r"(minutes?|seconds?|ms|iterations?|retries?|turns?|calls?|levels?)?)\b",
    re.IGNORECASE,
)
RL_1B_MAX_KEY = re.compile(
    r"\bmax\s+(iterations?|turns?|calls?|retries?|depth|budget)\s*[:=]?\s*\d+\b",
    re.IGNORECASE,
)
RL_1B_STATUS = re.compile(
    r"\bstatus\s*[:=]\s*[\"']?"
    r"(terminal|success|partial|failure|done|complete)[\"']?",
    re.IGNORECASE,
)

# RL-3b (rubric L179).
RL_3B_RETRY = re.compile(r"\b(retry|regenerate|redisplay|ask\s+again|adjust)\b", re.IGNORECASE)
RL_3B_CAP = re.compile(
    r"\b(max(imum)?\s*\d+|up\s+to\s+\d+|<=\s*\d+|≤\s*\d+|"
    r"after\s+\d+\s+(consecutive|failed|attempts)|"
    r"\d+\s+(times|attempts|cycles))\b",
    re.IGNORECASE,
)

# RL-4b (rubric L180).
RL_4B_HITL = re.compile(r"\b(AskUserQuestion|confirm|approval)\b")
RL_4B_PARTIAL = re.compile(r"\bstatus\s*[:=]\s*[\"']?partial[\"']?", re.IGNORECASE)
RL_4B_ESCALATE_HEADING = re.compile(
    r"(^|\n)\s*[-*#]?\s*"
    r"(escalate|on\s+escalation|partial\s+result|"
    r"fallback\s+to\s+user|defer\s+to\s+user|hand\s+off\s+to)",
    re.IGNORECASE,
)

# RL-9b (rubric L181-185) — four OR-joined alternatives.
RL_9B_REDACT = re.compile(
    r"redact(s|ed|ing)?\s+[^.]{0,120}"
    r"(token|secret|credential|key|match|substring|"
    r"\[A-Za-z0-9_-\]\\\{\d+,\\\})",
    re.IGNORECASE,
)
RL_9B_TRUNCATE = re.compile(
    r"truncate(s|d|ing)?\s+[^.]{0,120}(at|to)\s+\d+\s+"
    r"(chars?|characters?|tokens?|bytes?)",
    re.IGNORECASE,
)
RL_9B_SKIP = re.compile(
    r"skip(s|ping|ped)?\s+[^.]{0,120}"
    r"(\.env|\.ssh|credential|secret|\.aws|\.pem)",
    re.IGNORECASE,
)
RL_9B_TOKEN_LIKE = re.compile(
    r"token[-_\s]?like|\[A-Za-z0-9_-\]\\\{20,\\\}",
    re.IGNORECASE,
)

# AH-2b (rubric L161-167) — existential pair.
AH_2B_TRIGGER = re.compile(
    r"\b(if\s+[^.]{0,100}?(\$ARGUMENTS|argument|input|parameter)"
    r"[^.]{0,80}?"
    r"(empty|missing|absent|not\s+provided|not\s+supplied|unset|null|blank))",
    re.IGNORECASE,
)
AH_2B_RESPONSE = re.compile(
    r"(default(s|ing)?\s+to|fall\s?back\s+to|"
    r"use(s|d)?\s+[^.]{0,50}?as\s+default|"
    r"prompt\s+the\s+user|ask\s+the\s+user\s+for|request\s+input|"
    r"stop\s+with\s+(error|usage|message)|"
    r"report\s+[^.]{0,50}?(error|usage).*stop)",
    re.IGNORECASE,
)

# META-3b sibling counter-reference — PASS-override when skills
# explicitly name-and-exclude siblings.
META_3B_COUNTER_REFERENCE = re.compile(
    r"\buse\s+/(review|scaffold|apply|audit)-\S+\s+instead\b|"
    r"\bdo\s+not\s+use\s+for\b",
    re.IGNORECASE,
)

# Stopwords for META-1a token-set overlap.
STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "to",
        "use",
        "when",
        "with",
        "this",
        "that",
        "these",
        "those",
        "do",
        "not",
        "but",
        "are",
        "was",
        "were",
    }
)

# Items the guide lists but that remain LLM-interpretive.
NON_BINARY_ITEMS: list[str] = [
    # Progressive disclosure
    "PD-1",
    "PD-2",
    "PD-3",
    "PD-4",
    "PD-5",
    # Workflow sequencing
    "WS-1",
    "WS-2",
    "WS-3",
    "WS-4",
    "WS-5",  # narrative parent; superseded by WS-5b — dropped in merge layer (issue #89)
    "WS-6",
    "WS-7",
    "WS-8",
    # Metadata trigger-consistency (issue #98 — letter-suffix, narrative)
    "META-3c",
    # Reference files
    "RF-1",
    "RF-2",
    "RF-3",
    # Argument handling
    "AH-1",
    "AH-2",
    "AH-3",
    "AH-4",
    # Output format
    "OF-1",
    "OF-2",
    "OF-3",
    "OF-4",
    # Safety / policy — non-binary variants
    "SP-1",
    "SP-2",
    "SP-3",
    "SP-4",
    # Reliability — non-binary variants
    "RL-1",
    "RL-3",
    "RL-4",
    "RL-9",
    # Anti-patterns
    "AP-1",
    "AP-2",
    "AP-3",
    "AP-4",
    # Repo defaults / distinctness
    "RD-1",
    "RD-2",
    "RD-3",
    "RD-4",
    "RD-5",
    "RD-6",
    # Recovery / tolerance
    "RT-1",
    "RT-2",
    "RT-3",
    # Injection — non-binary variant
    "IJ-1",
    # Metadata — LLM-judgment alternative
    "META-1b",
]


# ---------------------------------------------------------------------------
# Helper: frontmatter parsing, classification, location utilities.
# ---------------------------------------------------------------------------


def parse_frontmatter(path: pathlib.Path) -> tuple[dict, str]:
    """Return (fields, raw_frontmatter_text).

    Supports key: value; indented-dash list; inline [a, b, c]; and comma
    list form for allowed-tools-style keys. Returns ({}, "") when the
    file does not start with '---'.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, ""
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return {}, ""

    raw_lines: list[str] = []
    fields: dict = {}
    i = 1
    current_list_key: str | None = None
    while i < len(lines):
        line = lines[i]
        if line.strip() == "---":
            break
        raw_lines.append(line)

        # Indented-dash list continuation.
        if current_list_key and (line.startswith(" - ") or line.startswith("  - ") or line.startswith("\t- ")):
            item = line.split("-", 1)[1].strip().strip("'").strip('"')
            if item:
                fields[current_list_key].append(item)
            i += 1
            continue
        current_list_key = None

        # Top-level key: value.
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            if value in ("", ">", "|"):
                # Block scalar — for ">" / "|", consume indented lines
                # and join as a space-separated string. For "" (bare),
                # assume an indented-dash list.
                if value == "":
                    fields[key] = []
                    current_list_key = key
                else:
                    # Block scalar body.
                    block_parts: list[str] = []
                    j = i + 1
                    while j < len(lines):
                        sub = lines[j]
                        if sub.strip() == "---":
                            break
                        if not sub.startswith((" ", "\t")) and sub.strip() != "":
                            break
                        block_parts.append(sub.strip())
                        raw_lines.append(sub)
                        j += 1
                    fields[key] = " ".join(p for p in block_parts if p)
                    i = j
                    continue
            elif value.startswith("[") and value.endswith("]"):
                inner = value[1:-1]
                fields[key] = [tok.strip().strip("'").strip('"') for tok in inner.split(",") if tok.strip()]
            elif "," in value and key in ("allowed-tools", "tools"):
                fields[key] = [tok.strip() for tok in value.split(",") if tok.strip()]
            else:
                fields[key] = value.strip().strip('"').strip("'")
        i += 1

    raw_frontmatter = "\n".join(raw_lines)
    return fields, raw_frontmatter


def split_content(path: pathlib.Path) -> tuple[str, str]:
    """Return (full_text, body_after_frontmatter)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return text, text
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return text, text
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return text, "\n".join(lines[i + 1 :])
    return text, text


def classify_artifact(path: pathlib.Path, fm: dict) -> str:
    name_lower = path.name.lower()
    # Production skills are always exactly SKILL.md; test fixtures use the
    # <name>.SKILL.md convention to colocate multiple skill snapshots in one
    # directory. Both shapes classify as "skill".
    if name_lower == "skill.md" or name_lower.endswith(".skill.md"):
        return "skill"
    if name_lower.endswith(".md") and "agents" in path.parts:
        return "agent"
    if name_lower == "plugin.json":
        return "plugin"
    return "rule"


def tools_list(fm: dict) -> list[str]:
    """Return normalised allowed-tools / tools list as strings."""
    for key in ("allowed-tools", "tools"):
        if key in fm and isinstance(fm[key], list):
            return [t for t in fm[key] if t]
        if key in fm and isinstance(fm[key], str) and fm[key].strip():
            return [t.strip() for t in fm[key].split(",") if t.strip()]
    return []


def is_agentic(body: str, tools: list[str]) -> bool:
    """Three-branch disjunction per scoring-rubric.md L181."""
    if AGENTIC_DISPATCH_PATTERN.search(body):
        return True
    if AGENTIC_LOOP_PATTERN.search(body):
        return True
    if AGENTIC_WRITE_TOOLS.intersection(tools):
        return True
    return False


def needs_rl9b(body: str, tools: list[str]) -> bool:
    """Narrower sub-predicate for RL-9b (rubric L181 intro text).

    Fires only if the skill (a) reads user-supplied paths or (b) writes
    externally-quoted content. Pure read-only skills without
    $ARGUMENTS path-handling get NA even when agentic by the broader
    predicate.
    """
    tools_set = set(tools)
    writes = bool(tools_set.intersection({"Write", "Edit"}))
    reads_paths = ("$ARGUMENTS" in body) and bool(tools_set.intersection({"Read", "Glob"}))
    return writes or reads_paths


def find_sibling_skills(path: pathlib.Path) -> list[pathlib.Path]:
    """Return sibling SKILL.md files under skills/*/SKILL.md minus self."""
    skills_root = REPO_ROOT / "skills"
    if not skills_root.exists():
        return []
    self_resolved = path.resolve()
    return [p for p in sorted(skills_root.glob("*/SKILL.md")) if p.resolve() != self_resolved]


def line_of_offset(text: str, offset: int) -> int:
    """Return 1-based line number for an offset into text."""
    return text[:offset].count("\n") + 1


def has_sibling_counter_reference(own_fm: dict, sibling_fm: dict) -> bool:
    for fm in (own_fm, sibling_fm):
        desc = str(fm.get("description", ""))
        if META_3B_COUNTER_REFERENCE.search(desc):
            return True
    return False


def tokenize_description(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]*", text.lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) > 2}


def primary_verb(fm: dict) -> str | None:
    """Extract primary verb for the COMP-X review-skill clause."""
    description = str(fm.get("description", ""))
    match = COMP_X_PRIMARY_VERB.search(description)
    if match:
        verb = match.group(1).lower()
        for root in COMP_X_NAME_TOKENS:
            if verb.startswith(root):
                return root
    # Fall back to name-stem tokens.
    name = str(fm.get("name", ""))
    for token in re.split(r"[^A-Za-z]+", name.lower()):
        if token in COMP_X_NAME_TOKENS:
            return token
    return None


# ---------------------------------------------------------------------------
# Per-item check functions. Each returns a dict with keys {verdict, evidence}.
# ---------------------------------------------------------------------------


def _pass(**evidence: object) -> dict:
    return {"verdict": "PASS", "evidence": evidence}


def _fail(**evidence: object) -> dict:
    return {"verdict": "FAIL", "evidence": evidence}


def _na(reason: str) -> dict:
    return {"verdict": "NA", "evidence": {"reason": reason}}


def check_META_1a(body: str, fm: dict) -> dict:
    description = str(fm.get("description", ""))
    if not description:
        return _na("description absent")
    desc_tokens = tokenize_description(description)
    # Primary trigger nouns: file extensions + common trigger words in body.
    body_tokens = tokenize_description(body[:2000])
    overlap = desc_tokens & body_tokens
    if overlap:
        return {
            "verdict": "PASS",
            "evidence": {"overlap": sorted(overlap)[:5], "heuristic": True},
        }
    return {
        "verdict": "FAIL",
        "evidence": {
            "reason": "no token overlap between description and body prefix",
            "heuristic": True,
        },
    }


def check_META_2(body: str, fm: dict) -> dict:
    description = str(fm.get("description", ""))
    match = META_2_PATTERN.search(description)
    if match:
        return _pass(match=match.group(0), location="description")
    # The rubric PASS requires an explicit exclusion — absence is not PASS.
    return _fail(reason="description lacks do-not-use exclusion phrase")


def check_META_3a(body: str, fm: dict) -> dict:
    description = str(fm.get("description", ""))
    match = META_3A_EXCLUSION.search(description)
    if match:
        return _fail(match=match.group(0), reason="fuzzy trigger phrase present")
    return _pass(reason="no fuzzy trigger phrase")


def check_META_3b(path: pathlib.Path, fm: dict, artifact_type: str = "skill") -> dict:
    # Agents share descriptions with their orchestrator skill by design
    # (perspective-clarity's description intentionally shadows review-skill's
    # subject area). Sibling-overlap semantics for agents require an
    # agent-namespace-aware counter-reference policy — see issue #75.
    if artifact_type != "skill":
        return _na("META-3b scope: skill-to-skill sibling check only; agent-namespace policy pending issue #75")
    own_desc = str(fm.get("description", ""))
    own_tokens = tokenize_description(own_desc)
    if not own_tokens:
        return _na("description absent or stopword-only")
    siblings = find_sibling_skills(path)
    if not siblings:
        return _na("no sibling skills found")
    for sib in siblings:
        try:
            sib_fm, _ = parse_frontmatter(sib)
        except Exception:
            continue
        sib_desc = str(sib_fm.get("description", ""))
        sib_tokens = tokenize_description(sib_desc)
        shared = own_tokens & sib_tokens
        if len(shared) >= 2 and not has_sibling_counter_reference(fm, sib_fm):
            return {
                "verdict": "FAIL",
                "evidence": {
                    "sibling": str(sib.relative_to(REPO_ROOT)),
                    "shared_tokens": sorted(shared)[:6],
                    "heuristic": True,
                },
            }
    return {"verdict": "PASS", "evidence": {"heuristic": True}}


def check_META_4(fm: dict) -> dict:
    description = str(fm.get("description", ""))
    if not description:
        return _na("description absent")
    if is_third_person(description):
        return _pass(reason="no first/second-person match")
    return _fail(reason="first-person or second-person imperative in description")


def check_CLAR_1(body: str) -> dict:
    if passes_clar1(body):
        return _pass(reason="no fuzzy quantifier")
    match = FUZZY_QUANTIFIER.search(body)
    return _fail(
        line=line_of_offset(body, match.start()),
        match=match.group(0),
    )


def check_CLAR_2(body: str) -> dict:
    if passes_clar2(body):
        return {"verdict": "PASS", "evidence": {"reason": "no bare pronoun+verb", "heuristic": True}}
    match = BARE_PRONOUN_VERB.search(body)
    return {
        "verdict": "FAIL",
        "evidence": {
            "line": line_of_offset(body, match.start()),
            "match": match.group(0),
            "heuristic": True,
        },
    }


def check_CLAR_3(body: str) -> dict:
    triggers = list(CLAR_3_TRIGGER.finditer(body))
    if not triggers:
        return _na("no abort/refuse/bail/halt/timeout trigger in body")
    for trig in triggers:
        window_start = trig.start()
        window_end = min(len(body), trig.end() + 200)
        if not CLAR_3_RECOVERY.search(body[window_start:window_end]):
            return _fail(
                line=line_of_offset(body, trig.start()),
                trigger=trig.group(0),
                reason="no recovery predicate within 200 chars",
            )
    return _pass(reason=f"{len(triggers)} trigger(s) each paired with recovery")


def check_CLAR_4(body: str) -> dict:
    deps = list(CLAR_4_DEPENDENCY.finditer(body))
    if not deps:
        return _na("no numbered upstream dependency declared")
    if CLAR_4_FALLBACK_HEADING.search(body):
        return {"verdict": "PASS", "evidence": {"reason": "fallback section heading present", "heuristic": True}}
    for dep in deps:
        window_end = min(len(body), dep.end() + 500)
        if not CLAR_4_FAILURE_BRANCH.search(body[dep.start() : window_end]):
            return {
                "verdict": "FAIL",
                "evidence": {
                    "line": line_of_offset(body, dep.start()),
                    "dependency": dep.group(0),
                    "reason": "no failure-branch clause within 200 chars",
                    "heuristic": True,
                },
            }
    return {"verdict": "PASS", "evidence": {"reason": "all dependencies paired with failure branch", "heuristic": True}}


def check_CE_X(body: str) -> dict:
    if not CE_X_TRIGGER.search(body):
        return _na("no conversation-history / summarisation / compaction mention")
    if CE_X_JUSTIFICATION.search(body):
        return {
            "verdict": "PASS",
            "evidence": {"reason": "masking / justification sentence present", "heuristic": True},
        }
    return {
        "verdict": "FAIL",
        "evidence": {"reason": "summarisation without masking / justification", "heuristic": True},
    }


def check_COMP_X(body: str, fm: dict, artifact_type: str = "skill") -> dict:
    # COMP-X encodes skill-semantics: "complete when / success when / done when"
    # prose predicate plus an optional review-skill convergence-predicate
    # clause. Agents emit structured output validated by the merge layer;
    # their success contract is captured by TC-3 in agent-evaluation-guide.md
    # (not yet a binary item). Return NA for agents until TC-3 is binarised
    # under issue #75 / #76.
    if artifact_type != "skill":
        return _na("COMP-X scope: skill-semantics only; agent analog is TC-3, pending binary — see issue #75")
    success_count = len(COMP_X_SUCCESS.findall(body))
    verb = primary_verb(fm)
    if verb is None:
        if success_count >= 1:
            return _pass(success_count=success_count)
        return _fail(reason="no explicit success condition")
    # Review-skill clause: require convergence / confidence / evidence-citation predicate.
    if not COMP_X_CONVERGENCE.search(body):
        return _fail(
            reason=(f"review-skill ({verb}) missing convergence / grade-distribution / evidence-citation predicate"),
            primary_verb=verb,
        )
    return _pass(primary_verb=verb, reason="review-skill convergence predicate present")


def check_COMP_Y(body: str) -> dict:
    if COMP_Y_EXCLUSION.search(body):
        match = COMP_Y_EXCLUSION.search(body)
        return _fail(
            line=line_of_offset(body, match.start()),
            match=match.group(0),
            reason="holistic non-binary phrase in verification",
        )
    if COMP_Y_BINARY.search(body):
        return _pass(reason="binary verification predicate present")
    return _fail(reason="no binary verification predicate and no exclusion")


def check_COMP_Z(body: str) -> dict:
    match = COMP_Z_PATTERN.search(body)
    if match:
        return _pass(
            line=line_of_offset(body, match.start()),
            match=match.group(0),
        )
    return _fail(reason="no evidence/citation/quote/verified against in body")


def check_COMP_W(body: str) -> dict:
    if not has_loop(body):
        return _na("non-iterative body")
    if passes_comp_w(body):
        return _pass(reason="loop has termination predicate")
    return _fail(reason="loop without termination predicate")


def check_SAMP_1(body: str) -> dict:
    match = SAMPLING_PARAM.search(body)
    if match:
        return _fail(
            line=line_of_offset(body, match.start()),
            match=match.group(0),
        )
    return _na("no sampling param in body")


def check_SAMP_2(fm_raw: str) -> dict:
    match = SAMPLING_PARAM.search(fm_raw)
    if match:
        return _fail(match=match.group(0), location="frontmatter")
    return _na("no sampling param in frontmatter")


def check_PE_1(body: str) -> dict:
    """CoT-scaffolding in body prose (code-fenced exemplars excluded)."""
    stripped = strip_code(body)
    match = PE_1_PATTERN.search(stripped)
    if match:
        return _fail(
            line=line_of_offset(body, body.find(match.group(0))) if match.group(0) in body else None,
            match=match.group(0),
        )
    return {"verdict": "PASS", "evidence": {"reason": "no CoT scaffolding in prose"}}


def check_PE_2(body: str) -> dict:
    """Hedges in directives (code-fenced exemplars excluded)."""
    stripped = strip_code(body)
    match = PE_2_PATTERN.search(stripped)
    if match:
        return _fail(
            line=line_of_offset(body, body.find(match.group(0))) if match.group(0) in body else None,
            match=match.group(0),
        )
    return {"verdict": "PASS", "evidence": {"reason": "no hedge in directive prose"}}


def check_SP_2b(body: str, fm: dict) -> dict:
    tools = tools_list(fm)
    if not tools:
        return _na("allowed-tools absent or empty")
    if set(tools).issubset(READ_ONLY_TOOLS):
        return _na("allowed-tools is read-only subset")
    text = body + "\n" + str(fm.get("description", ""))
    mutating = [t for t in tools if t in MUTATING_TOOLS]
    if not mutating:
        return _na("no mutating tools (Write/Edit/Bash/Agent/WebFetch) in allowed-tools")
    unbound: list[str] = []
    for tool in mutating:
        bound = False
        for tool_match in re.finditer(rf"\b{re.escape(tool)}\b", text):
            window_start = max(0, tool_match.start() - 200)
            window_end = min(len(text), tool_match.end() + 200)
            if SP_2B_BINDING.search(text[window_start:window_end]):
                bound = True
                break
        if not bound:
            unbound.append(tool)
    if unbound:
        return _fail(unbound_tools=unbound)
    return _pass(mutating_tools=mutating)


def check_SP_4b(body: str, fm: dict) -> dict:
    tools = set(tools_list(fm))
    if "Write" not in tools:
        return _na("no Tier-A combination (Write absent)")
    tier_a = sorted(tools & TIER_A_PARTNERS)
    if not tier_a:
        return _na("Write present but no Tier-A partner (Bash/Agent/WebFetch)")
    text = body + "\n" + str(fm.get("description", ""))
    unconstrained: list[str] = []
    for tool in ["Write", *tier_a]:
        found = False
        for tool_match in re.finditer(rf"\b{re.escape(tool)}\b", text):
            window_start = max(0, tool_match.start() - 400)
            window_end = min(len(text), tool_match.end() + 400)
            if SP_4B_CONSTRAINT.search(text[window_start:window_end]):
                found = True
                break
        if not found:
            unconstrained.append(tool)
    if unconstrained:
        return _fail(tier_a_tools=["Write", *tier_a], unconstrained=unconstrained)
    return _pass(tier_a_tools=["Write", *tier_a])


def check_IJ_1b(body: str, fm: dict) -> dict:
    tools = set(tools_list(fm))
    if not tools.intersection({"Write", "Edit"}):
        return _na("no Write/Edit tool granted")
    text = body + "\n" + str(fm.get("description", ""))
    if not EXTERNAL_INPUT_MARKERS.search(text):
        return _na("no external-input reference in body")
    has_validation = bool(IJ_1B_VALIDATION.search(text))
    has_write_gate = bool(IJ_1B_WRITE_GATE.search(text))
    if has_validation and has_write_gate:
        return _pass(validation=True, write_gate=True)
    missing = []
    if not has_validation:
        missing.append("validation-predicate")
    if not has_write_gate:
        missing.append("write-gate-predicate")
    return _fail(missing=missing)


def check_RL_1b(body: str, is_agentic_flag: bool) -> dict:
    if not is_agentic_flag:
        return _na("non-agentic")
    if RL_1B_NUMERIC.search(body) or RL_1B_MAX_KEY.search(body) or RL_1B_STATUS.search(body):
        return _pass(reason="numeric / max-key / status predicate present")
    return _fail(reason="no numeric or enum termination predicate")


def check_RL_3b(body: str, is_agentic_flag: bool) -> dict:
    if not is_agentic_flag:
        return _na("non-agentic")
    retries = list(RL_3B_RETRY.finditer(body))
    if not retries:
        return _na("no retry/regenerate/redisplay/adjust token")
    for r in retries:
        window_start = max(0, r.start() - 400)
        window_end = min(len(body), r.end() + 400)
        if not RL_3B_CAP.search(body[window_start:window_end]):
            return _fail(
                line=line_of_offset(body, r.start()),
                retry_token=r.group(0),
                reason="no numeric cap within 400 chars",
            )
    return _pass(retry_count=len(retries))


def check_RL_4b(body: str, is_agentic_flag: bool) -> dict:
    if not is_agentic_flag:
        return _na("non-agentic")
    if RL_4B_HITL.search(body) or RL_4B_PARTIAL.search(body) or RL_4B_ESCALATE_HEADING.search(body):
        return {
            "verdict": "PASS",
            "evidence": {"reason": "HITL / partial / escalate path present", "heuristic": True},
        }
    return {
        "verdict": "FAIL",
        "evidence": {
            "reason": "no HITL / partial / escalate path on autonomous body",
            "heuristic": True,
        },
    }


def check_RL_9b(body: str, fm_raw: str, needs_rl9b_flag: bool) -> dict:
    if not needs_rl9b_flag:
        return _na("no user-supplied path reads and no write tool")
    text = fm_raw + "\n" + body
    for name, pattern in (
        ("redact", RL_9B_REDACT),
        ("truncate", RL_9B_TRUNCATE),
        ("skip", RL_9B_SKIP),
        ("token_like", RL_9B_TOKEN_LIKE),
    ):
        m = pattern.search(text)
        if m:
            return _pass(rule=name, match=m.group(0)[:80])
    return _fail(reason="no credential-scope rule found in frontmatter+body")


def check_WS_2b(body: str) -> dict:
    """WS-2b conditional-specificity with block-marker context.

    Operates on raw body (no ``strip_code``) because block markers often live
    inside fenced YAML examples and must remain discoverable.

    PASS: every in-scope `If present|If absent` occurrence (within 500 chars
        after a `---marker---` line) has a prose predicate naming the block
        within 400 chars before the marker.
    FAIL: at least one in-scope occurrence lacks a preceding predicate.
    NA: no block markers in body, or no `If present|If absent` occurrence is
        in-scope.
    """
    markers = list(WS_2B_BLOCK_MARKER.finditer(body))
    if not markers:
        return _na("no block-marker in body")
    any_in_scope = False
    for m in WS_2B_IF_CLAUSE.finditer(body):
        preceding_markers = [mk for mk in markers if mk.end() <= m.start()]
        if not preceding_markers:
            continue
        nearest = preceding_markers[-1]
        if m.start() - nearest.end() > WS_2B_MARKER_WINDOW:
            continue
        any_in_scope = True
        window_start = max(0, nearest.start() - WS_2B_PREDICATE_WINDOW)
        window_end = nearest.start()
        if not WS_2B_PROSE_PREDICATE.search(body[window_start:window_end]):
            return _fail(
                line=line_of_offset(body, m.start()),
                trigger=m.group(0),
                reason="no prose predicate naming the block marker within 400 chars before the marker",
            )
    if not any_in_scope:
        return _na("no `If present|If absent` occurrence within 500 chars after a marker")
    return _pass(reason="all in-scope occurrences paired with preceding prose predicate")


def check_WS_5b(body: str) -> dict:
    """WS-5b negation paired with adjacent positive whitelist (issue #89).

    PASS: every NEVER / DO NOT / MUST NOT + verb-list match in
        ``strip_code(body)`` has a positive-whitelist signal within ±200 chars.
    FAIL: at least one such match lacks an adjacent whitelist signal.
    NA: no NEVER / DO NOT / MUST NOT verb-list patterns in body.
    """
    stripped = strip_code(body)
    matches = list(WS_5B_NEGATIVE_LIST.finditer(stripped))
    if not matches:
        return _na("no NEVER/DO NOT/MUST NOT + verb-list patterns in body")
    for m in matches:
        before = max(0, m.start() - WS_5B_WINDOW)
        after = min(len(stripped), m.end() + WS_5B_WINDOW)
        window = stripped[before:after]
        if not WS_5B_POSITIVE_WHITELIST.search(window):
            return _fail(
                line=line_of_offset(stripped, m.start()),
                trigger=m.group(0)[:80],
                reason="negative imperative + verb-list lacks positive whitelist within 200 chars",
            )
    return _pass(reason="all negative imperatives paired with positive whitelist")


def check_RD_5b(body: str) -> dict:
    """RD-5b step-naming consistency.

    PASS: body uses ≤1 step-naming scheme (no ambiguity possible).
    NA: body uses ≥2 schemes AND has a mapping clause with a mapping verb +
        2+ scheme tokens within 200 chars. (NA, not PASS, to match
        CLAR-3 / AH-2b pattern where doesn't-apply == NA.)
    FAIL: body uses ≥2 schemes AND has no such mapping clause.
    """
    schemes = rd_5b_schemes_present(body)
    if len(schemes) <= 1:
        if not schemes:
            return _na("no step-naming scheme detected in body")
        return _na(f"single scheme ({schemes[0]}) — no ambiguity possible")
    if rd_5b_has_mapping_clause(body):
        return _na(f"{len(schemes)} schemes present but mapping clause resolves ambiguity")
    return _fail(
        schemes=schemes,
        reason=f"{len(schemes)} step-naming schemes present without mapping clause",
    )


def check_AH_2b(body: str) -> dict:
    triggers = list(AH_2B_TRIGGER.finditer(body))
    if not triggers:
        return _na("no missing-argument trigger sentence")
    for trig in triggers:
        window_start = trig.start()
        window_end = min(len(body), trig.end() + 200)
        if AH_2B_RESPONSE.search(body[window_start:window_end]):
            return _pass(
                line=line_of_offset(body, trig.start()),
                trigger=trig.group(0)[:80],
                reason="trigger paired with response within 200 chars",
            )
    return _fail(
        line=line_of_offset(body, triggers[0].start()),
        trigger=triggers[0].group(0)[:80],
        reason="missing-arg trigger without PASS-response within 200 chars",
    )


# ---------------------------------------------------------------------------
# Dispatch + main.
# ---------------------------------------------------------------------------

# Order matches the rubric sections so JSON output is readable.
BINARY_ITEM_IDS: list[str] = [
    "META-1a",
    "META-2",
    "META-3a",
    "META-3b",
    "META-4",
    "CLAR-1",
    "CLAR-2",
    "CLAR-3",
    "CLAR-4",
    "WS-2b",
    "WS-5b",
    "RD-5b",
    "CE-X",
    "COMP-X",
    "COMP-Y",
    "COMP-Z",
    "COMP-W",
    "SAMP-1",
    "SAMP-2",
    "PE-1",
    "PE-2",
    "SP-2b",
    "SP-4b",
    "IJ-1b",
    "RL-1b",
    "RL-3b",
    "RL-4b",
    "RL-9b",
    "AH-2b",
]


def _run_check(
    item_id: str,
    body: str,
    fm: dict,
    fm_raw: str,
    path: pathlib.Path,
    is_agentic_flag: bool,
    needs_rl9b_flag: bool,
    artifact_type: str = "skill",
) -> dict:
    """Dispatch a single check, wrapping exceptions as NA + runner_error."""
    try:
        if item_id == "META-1a":
            return check_META_1a(body, fm)
        if item_id == "META-2":
            return check_META_2(body, fm)
        if item_id == "META-3a":
            return check_META_3a(body, fm)
        if item_id == "META-3b":
            return check_META_3b(path, fm, artifact_type)
        if item_id == "META-4":
            return check_META_4(fm)
        if item_id == "CLAR-1":
            return check_CLAR_1(body)
        if item_id == "CLAR-2":
            return check_CLAR_2(body)
        if item_id == "CLAR-3":
            return check_CLAR_3(body)
        if item_id == "CLAR-4":
            return check_CLAR_4(body)
        if item_id == "WS-2b":
            return check_WS_2b(body)
        if item_id == "WS-5b":
            return check_WS_5b(body)
        if item_id == "RD-5b":
            return check_RD_5b(body)
        if item_id == "CE-X":
            return check_CE_X(body)
        if item_id == "COMP-X":
            return check_COMP_X(body, fm, artifact_type)
        if item_id == "COMP-Y":
            return check_COMP_Y(body)
        if item_id == "COMP-Z":
            return check_COMP_Z(body)
        if item_id == "COMP-W":
            return check_COMP_W(body)
        if item_id == "SAMP-1":
            return check_SAMP_1(body)
        if item_id == "SAMP-2":
            return check_SAMP_2(fm_raw)
        if item_id == "PE-1":
            return check_PE_1(body)
        if item_id == "PE-2":
            return check_PE_2(body)
        if item_id == "SP-2b":
            return check_SP_2b(body, fm)
        if item_id == "SP-4b":
            return check_SP_4b(body, fm)
        if item_id == "IJ-1b":
            return check_IJ_1b(body, fm)
        if item_id == "RL-1b":
            return check_RL_1b(body, is_agentic_flag)
        if item_id == "RL-3b":
            return check_RL_3b(body, is_agentic_flag)
        if item_id == "RL-4b":
            return check_RL_4b(body, is_agentic_flag)
        if item_id == "RL-9b":
            return check_RL_9b(body, fm_raw, needs_rl9b_flag)
        if item_id == "AH-2b":
            return check_AH_2b(body)
        return {
            "verdict": "NA",
            "evidence": {"reason": f"runner_error: unknown item {item_id}"},
        }
    except Exception as exc:  # noqa: BLE001 — loud NA > silent crash
        return {
            "verdict": "NA",
            "evidence": {"reason": f"runner_error: {type(exc).__name__}: {exc}"},
        }


def evaluate(path: pathlib.Path) -> dict:
    fm, fm_raw = parse_frontmatter(path)
    _, body = split_content(path)
    tools = tools_list(fm)
    is_agentic_flag = is_agentic(body, tools)
    needs_rl9b_flag = needs_rl9b(body, tools)
    artifact_type = classify_artifact(path, fm)

    verdicts: dict[str, dict] = {}
    stats = {"pass": 0, "fail": 0, "na": 0, "runner_error": 0}
    for item_id in BINARY_ITEM_IDS:
        result = _run_check(item_id, body, fm, fm_raw, path, is_agentic_flag, needs_rl9b_flag, artifact_type)
        verdicts[item_id] = result
        verdict = result.get("verdict")
        if verdict == "PASS":
            stats["pass"] += 1
        elif verdict == "FAIL":
            stats["fail"] += 1
        elif verdict == "NA":
            stats["na"] += 1
        ev = result.get("evidence", {})
        if isinstance(ev, dict) and str(ev.get("reason", "")).startswith("runner_error"):
            stats["runner_error"] += 1

    # Artifact path is recorded relative to repo root when possible.
    try:
        rel_path = str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        rel_path = str(path)

    fm_out = {
        "name": fm.get("name"),
        "description": fm.get("description"),
        "allowed-tools": tools,
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_path": rel_path,
        "artifact_type": artifact_type,
        "artifact_frontmatter": fm_out,
        "verdicts": verdicts,
        "stats": stats,
        "non_binary_items": list(NON_BINARY_ITEMS),
        "runner_error": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="rubric_binary_evaluator",
        description=(
            "Deterministic binary rubric evaluator for Claude Code skills. Emits a JSON verdicts document on stdout."
        ),
    )
    parser.add_argument(
        "artifact_path",
        help="Absolute or repo-relative path to a SKILL.md artifact.",
    )
    args = parser.parse_args(argv)

    try:
        path = pathlib.Path(args.artifact_path).expanduser()
        if not path.is_absolute():
            path = (REPO_ROOT / path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"artifact not found: {path}")
        result = evaluate(path)
    except Exception as exc:  # noqa: BLE001 — global crash path
        sys.stderr.write(traceback.format_exc())
        json.dump(
            {
                "schema_version": SCHEMA_VERSION,
                "runner_error": f"{type(exc).__name__}: {exc}",
                "verdicts": {},
                "stats": {"pass": 0, "fail": 0, "na": 0, "runner_error": 1},
                "non_binary_items": list(NON_BINARY_ITEMS),
            },
            sys.stdout,
            indent=2,
            sort_keys=False,
        )
        sys.stdout.write("\n")
        return 1

    json.dump(result, sys.stdout, indent=2, sort_keys=False)
    sys.stdout.write("\n")
    return 2 if result["stats"]["runner_error"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
