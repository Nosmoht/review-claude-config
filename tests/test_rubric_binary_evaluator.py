r"""Tests for scripts/rubric_binary_evaluator.py.

Source of truth: skills/review-claude-config/references/scoring-rubric.md
section "Binary-Verifiable Rubric Items" (L93-188).

The runner produces PASS / FAIL / NA verdicts for 24 binary rubric
items. Per-item classes below pin at minimum one PASS, one FAIL, and
(where applicable) one NA fixture. Integration classes cover the
full pipeline against frozen SKILL.md fixtures and the exit-code
contract.

Schema-version contract: the runner emits ``schema_version: 1``.
Breaking changes (removed / renamed items, changed verdict enum)
require a bump; additive keys under ``evidence.<item>`` or new rubric
items in ``verdicts`` do not.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from rubric_binary_evaluator import (  # noqa: E402
    BINARY_ITEM_IDS,
    NON_BINARY_ITEMS,
    SCHEMA_VERSION,
    check_AH_2b,
    check_CE_X,
    check_CLAR_1,
    check_CLAR_2,
    check_CLAR_3,
    check_CLAR_4,
    check_COMP_W,
    check_COMP_X,
    check_COMP_Y,
    check_COMP_Z,
    check_IJ_1b,
    check_META_1a,
    check_META_2,
    check_META_3a,
    check_META_3b,
    check_META_4,
    check_RD_5b,
    check_RL_1b,
    check_RL_3b,
    check_RL_4b,
    check_PE_1,
    check_PE_2,
    check_RL_9b,
    check_SAMP_1,
    check_SAMP_2,
    check_SP_2b,
    check_SP_4b,
    check_WS_2b,
    check_WS_5b,
    evaluate,
    is_agentic,
    needs_rl9b,
    parse_frontmatter,
    primary_verb,
    tools_list,
)
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "rubric_evaluator"
REVIEW_SKILL_FIXTURE = FIXTURE_DIR / "review-skill.SKILL.md"
SCAFFOLD_SKILL_FIXTURE = FIXTURE_DIR / "scaffold-skill.SKILL.md"
REVIEW_PERSPECTIVE_CLARITY_AGENT_FIXTURE = FIXTURE_DIR / "agents" / "review-perspective-clarity.md"


# ---------------------------------------------------------------------------
# Frontmatter parser — three list forms + absent/empty + malformed.
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def _write(self, tmp_path: pathlib.Path, body: str) -> pathlib.Path:
        p = tmp_path / "fixture.md"
        p.write_text(body, encoding="utf-8")
        return p

    def test_flat_string(self, tmp_path):
        p = self._write(tmp_path, "---\nname: foo\ndescription: bar\n---\nbody")
        fm, _ = parse_frontmatter(p)
        assert fm["name"] == "foo"
        assert fm["description"] == "bar"

    def test_inline_bracket_list(self, tmp_path):
        p = self._write(tmp_path, "---\nallowed-tools: [Read, Write, Bash]\n---\nbody")
        fm, _ = parse_frontmatter(p)
        assert fm["allowed-tools"] == ["Read", "Write", "Bash"]

    def test_comma_list(self, tmp_path):
        p = self._write(tmp_path, "---\nallowed-tools: Read, Write, Bash\n---\nbody")
        fm, _ = parse_frontmatter(p)
        assert fm["allowed-tools"] == ["Read", "Write", "Bash"]

    def test_dash_list(self, tmp_path):
        p = self._write(
            tmp_path,
            "---\nallowed-tools:\n  - Read\n  - Write\n  - Bash\n---\nbody",
        )
        fm, _ = parse_frontmatter(p)
        assert fm["allowed-tools"] == ["Read", "Write", "Bash"]

    def test_absent_key(self, tmp_path):
        p = self._write(tmp_path, "---\nname: foo\n---\nbody")
        fm, _ = parse_frontmatter(p)
        assert "allowed-tools" not in fm

    def test_no_frontmatter(self, tmp_path):
        p = self._write(tmp_path, "no frontmatter here")
        fm, raw = parse_frontmatter(p)
        assert fm == {}
        assert raw == ""

    def test_html_comment_before_frontmatter(self, tmp_path):
        # HTML comment on line 1 breaks parser per validate_schema.py L30 —
        # runner returns empty fm, which cascades to NAs downstream.
        p = self._write(tmp_path, "<!-- Frozen -->\n---\nname: foo\n---\nbody")
        fm, _ = parse_frontmatter(p)
        assert fm == {}

    def test_raw_frontmatter_preserved(self, tmp_path):
        p = self._write(tmp_path, "---\nname: foo\ntemperature: 0.3\n---\nbody")
        _, raw = parse_frontmatter(p)
        assert "temperature: 0.3" in raw

    def test_block_scalar_description(self, tmp_path):
        p = self._write(
            tmp_path,
            "---\nname: foo\ndescription: >\n  Evaluates a skill across\n  dimensions.\n---\nbody",
        )
        fm, _ = parse_frontmatter(p)
        assert fm["name"] == "foo"
        assert "Evaluates a skill across" in fm["description"]


# ---------------------------------------------------------------------------
# is_agentic / needs_rl9b branch coverage.
# ---------------------------------------------------------------------------


class TestIsAgentic:
    def test_dispatch_verb_pascal_case_matches(self):
        assert is_agentic("Invoke Agent(subagent_type=...)", [])

    def test_dispatch_verb_lowercase_does_not_match(self):
        # Case-sensitive branch 1.
        assert not is_agentic("invoke agent only as helper", [])

    def test_loop_verb_matches(self):
        assert is_agentic("for each candidate, score", [])

    def test_until_matches_agentic_but_not_loop_pattern(self):
        # AGENTIC_LOOP_PATTERN includes `until`; LOOP_PATTERN does not.
        assert is_agentic("Retry until stable", [])

    def test_write_tool_matches(self):
        assert is_agentic("plain body", ["Write"])

    def test_edit_tool_matches(self):
        assert is_agentic("plain body", ["Edit"])

    def test_bash_tool_matches(self):
        assert is_agentic("plain body", ["Bash"])

    def test_lowercase_write_does_not_match(self):
        # Branch 3 is exact-case membership.
        assert not is_agentic("plain body", ["write"])

    def test_read_only_tools_not_agentic(self):
        assert not is_agentic("parse and emit", ["Read", "Glob"])


class TestNeedsRL9B:
    def test_read_paths_with_arguments(self):
        assert needs_rl9b("process $ARGUMENTS file", ["Read", "Glob"])

    def test_write_tool(self):
        assert needs_rl9b("plain body", ["Write"])

    def test_read_only_without_arguments(self):
        assert not needs_rl9b("plain body", ["Read", "Glob"])

    def test_arguments_without_read_tool(self):
        assert not needs_rl9b("process $ARGUMENTS", ["WebSearch"])


# ---------------------------------------------------------------------------
# primary_verb — COMP-X review-skill clause trigger.
# ---------------------------------------------------------------------------


class TestPrimaryVerb:
    # issue #102: review-skill clause now applies only to skills in
    # COMP_X_REVIEW_ALLOWLIST. Description-verb classification was
    # removed; non-allowlisted skills return None regardless of their
    # description prefix.
    def test_non_allowlisted_returns_none(self):
        # Skill name not in allowlist — description first verb is no
        # longer used to classify as review-class (would be a false
        # positive for one-time bug detectors / estimators).
        fm = {"description": "Evaluates a single SKILL.md", "name": "foo"}
        assert primary_verb(fm) is None

    def test_allowlisted_review_skill(self):
        fm = {"description": "Use when something", "name": "review-skill"}
        assert primary_verb(fm) == "review"

    def test_allowlisted_audit_skill(self):
        fm = {"description": "Audits trust chain", "name": "audit-trust-chain"}
        assert primary_verb(fm) == "audit"

    def test_scaffold_returns_none(self):
        fm = {"description": "Creates a research-optimized skill", "name": "scaffold-skill"}
        assert primary_verb(fm) is None

    def test_audit_mcp_auth_returns_none(self):
        # audit-mcp-auth is a one-time bug detector, not a graded review.
        fm = {"description": "Audits MCP OAuth credential storage", "name": "audit-mcp-auth"}
        assert primary_verb(fm) is None

    def test_check_repo_health_returns_none(self):
        # check-repo-health: ``Verifies`` is the primary verb; ``reviews``
        # appears only in object position (``before running reviews``).
        fm = {
            "description": "Verifies reference freshness, token budgets, before running reviews",
            "name": "check-repo-health",
        }
        assert primary_verb(fm) is None


# ---------------------------------------------------------------------------
# Per-item check functions. PASS + FAIL + NA where applicable.
# ---------------------------------------------------------------------------


class TestMETA1a:
    def test_overlap_passes(self):
        fm = {"description": "Evaluates MCP server configs"}
        result = check_META_1a("mcp server evaluation body", fm)
        assert result["verdict"] == "PASS"

    def test_no_overlap_fails(self):
        fm = {"description": "Evaluates MCP configs"}
        result = check_META_1a("totally unrelated prose about airplanes and fjords", fm)
        assert result["verdict"] == "FAIL"

    def test_absent_description_na(self):
        assert check_META_1a("body", {})["verdict"] == "NA"


class TestMETA2:
    def test_do_not_use_passes(self):
        fm = {"description": "Use when X. Do NOT use for agents."}
        assert check_META_2("body", fm)["verdict"] == "PASS"

    def test_not_for_passes(self):
        fm = {"description": "Scaffolds a skill. Not for rules."}
        assert check_META_2("body", fm)["verdict"] == "PASS"

    def test_no_exclusion_fails(self):
        fm = {"description": "Use when X."}
        assert check_META_2("body", fm)["verdict"] == "FAIL"


class TestMETA3a:
    def test_concrete_trigger_passes(self):
        fm = {"description": "Use when file contains hooks.json"}
        assert check_META_3a("body", fm)["verdict"] == "PASS"

    def test_fuzzy_trigger_fails(self):
        fm = {"description": "Apply as needed during config work"}
        assert check_META_3a("body", fm)["verdict"] == "FAIL"

    def test_when_useful_fails(self):
        fm = {"description": "Apply when useful during review"}
        assert check_META_3a("body", fm)["verdict"] == "FAIL"


class TestMETA3b:
    def test_empty_description_na(self, tmp_path):
        # Without tokens there is nothing to overlap with siblings.
        p = tmp_path / "SKILL.md"
        p.write_text("---\nname: x\n---\nbody")
        fm, _ = parse_frontmatter(p)
        assert check_META_3b(p, fm)["verdict"] == "NA"

    def test_counter_reference_overrides_overlap(self):
        # review-skill description contains "Do NOT use for agents or rules" —
        # counter-reference overrides any token overlap with siblings.
        fm, _ = parse_frontmatter(REVIEW_SKILL_FIXTURE)
        assert check_META_3b(REVIEW_SKILL_FIXTURE, fm)["verdict"] == "PASS"

    def test_agent_artifact_returns_na(self, tmp_path):
        # Issue #74: META-3b globs skills/*/SKILL.md for siblings, which is
        # skill-to-skill semantics. Agents must NA until issue #75 defines the
        # agent-namespace sibling policy.
        p = tmp_path / "agent.md"
        p.write_text("---\nname: some-agent\ndescription: Verifies things\n---\nbody")
        fm, _ = parse_frontmatter(p)
        result = check_META_3b(p, fm, artifact_type="agent")
        assert result["verdict"] == "NA"
        assert "#75" in result["evidence"]["reason"]


class TestMETA4:
    def test_third_person_passes(self):
        assert check_META_4({"description": "Evaluates a skill"})["verdict"] == "PASS"

    def test_first_person_fails(self):
        assert check_META_4({"description": "I review skills"})["verdict"] == "FAIL"

    def test_second_person_fails(self):
        assert check_META_4({"description": "Use your workbook"})["verdict"] == "FAIL"

    def test_absent_description_na(self):
        assert check_META_4({})["verdict"] == "NA"


class TestCLAR1:
    def test_exact_quantifier_passes(self):
        assert check_CLAR_1("retry 3 times")["verdict"] == "PASS"

    def test_fuzzy_fails(self):
        assert check_CLAR_1("retry roughly 10 times")["verdict"] == "FAIL"


class TestCLAR2:
    def test_resolved_pronoun_passes(self):
        assert check_CLAR_2("parse the output; store the matches")["verdict"] == "PASS"

    def test_bare_pronoun_fails(self):
        result = check_CLAR_2("parse output; process them")
        assert result["verdict"] == "FAIL"
        assert result["evidence"].get("heuristic") is True

    # issue #104 boundary cases — antecedent-aware narrowing.
    def test_if_X_use_it_passes(self):
        # ``If <antecedent>, use it`` — pronoun resolves to clause subject.
        body = "If `$ARGUMENTS` contains a file path, use it."
        assert check_CLAR_2(body)["verdict"] == "PASS"

    def test_otherwise_use_it_passes(self):
        body = "First try the cache. Otherwise, use it as the fresh source."
        assert check_CLAR_2(body)["verdict"] == "PASS"

    def test_when_X_with_parentheticals_passes(self):
        # Antecedent prefix may include parenthetical commas (issue #104).
        body = (
            "If the user provided explicit domain information in their "
            'request (e.g., "Go MCP server", "Python FastAPI"), use it directly.'
        )
        assert check_CLAR_2(body)["verdict"] == "PASS"

    def test_determiner_that_passes(self):
        # ``Use that <noun>`` is determiner usage, not bare pronoun.
        body = "Locate the contract via Glob. Use that contract's schema below."
        assert check_CLAR_2(body)["verdict"] == "PASS"

    def test_em_dash_recovery_passes(self):
        # ``<noun-phrase> — re-run that <noun>`` em-dash construct.
        body = "A bare heading is INCOMPLETE — re-run that category."
        assert check_CLAR_2(body)["verdict"] == "PASS"

    def test_backtick_quoted_string_passes(self):
        body = "- Option label: `\"Use this domain context for skill\"`"
        assert check_CLAR_2(body)["verdict"] == "PASS"


class TestCLAR3:
    def test_trigger_with_recovery_passes(self):
        body = 'On timeout, write a {"status": "missing"} stub and continue to step b.4.'
        assert check_CLAR_3(body)["verdict"] == "PASS"

    def test_trigger_without_recovery_fails(self):
        # Plain ``abort`` with no recovery and no negation (issue #105).
        body = "Run the check. If the file is missing, abort."
        result = check_CLAR_3(body)
        assert result["verdict"] == "FAIL"
        assert result["evidence"]["trigger"] == "abort"

    def test_no_trigger_na(self):
        assert check_CLAR_3("plain descriptive body")["verdict"] == "NA"

    # issue #105 boundary cases.
    def test_refuse_and_ask_passes(self):
        body = "If the file already exists, refuse and ask for a different name."
        assert check_CLAR_3(body)["verdict"] == "PASS"

    def test_abort_with_noun_passes(self):
        body = "If Grep fails, abort with structured error block."
        assert check_CLAR_3(body)["verdict"] == "PASS"

    def test_negation_skipped(self):
        # ``do not abort`` is a negation; the trigger is non-actionable.
        body = "Collect errors per perspective; do not abort the whole dispatch."
        result = check_CLAR_3(body)
        assert result["verdict"] == "NA"

    def test_timeout_as_config_noun_skipped(self):
        body = "5. **Timeout** — command handlers default to 600 seconds."
        result = check_CLAR_3(body)
        assert result["verdict"] == "NA"

    def test_timeout_field_path_skipped(self):
        body = "Mark FAIL with note 'agent timeout or crash' if `case.execution.timeout_seconds` exceeded."
        result = check_CLAR_3(body)
        assert result["verdict"] == "NA"


class TestCLAR4:
    def test_no_dependency_na(self):
        assert check_CLAR_4("plain body with no dependencies")["verdict"] == "NA"

    def test_dependency_with_failure_branch_passes(self):
        # CLAR_4_FAILURE_BRANCH uses [^.]{0,200}?; the `if ... fails`
        # clause must not contain a period between them.
        body = (
            "Step 5 depends on step 4 completed; "
            "if upstream fails or is missing, degrade via fallback"
        )
        assert check_CLAR_4(body)["verdict"] == "PASS"

    def test_dependency_with_fallback_heading_passes(self):
        body = "b.5 depends on b.4 completed.\n\n## Error Handling\n\nFallback: ..."
        assert check_CLAR_4(body)["verdict"] == "PASS"

    def test_dependency_without_branch_fails(self):
        body = "Step 5 depends on step 4 completed. Continue onwards."
        assert check_CLAR_4(body)["verdict"] == "FAIL"


class TestCEX:
    def test_no_summarisation_mention_na(self):
        assert check_CE_X("plain procedural body")["verdict"] == "NA"

    def test_summarisation_with_justification_passes(self):
        # CE_X_TRIGGER uses American spelling `summariz(e|ation)` and
        # `compact(ion)?`. British variants ("summarisation") do not
        # match the trigger.
        body = (
            "We keep the conversation history for 20 turns and summarize each. "
            "Masking is justified: summarization irreversibly drops tool outputs."
        )
        assert check_CE_X(body)["verdict"] == "PASS"

    def test_summarisation_without_justification_fails(self):
        body = "Keep the conversation history across 20 turns and summarize periodically."
        assert check_CE_X(body)["verdict"] == "FAIL"


class TestCOMPX:
    def test_non_review_success_passes(self):
        fm = {"description": "Creates a scaffold"}
        body = "Complete when all output sections are emitted."
        assert check_COMP_X(body, fm)["verdict"] == "PASS"

    def test_review_without_convergence_fails(self):
        fm = {"description": "Evaluates a skill", "name": "review-skill"}
        body = "Complete when every checklist item has a verdict."
        assert check_COMP_X(body, fm)["verdict"] == "FAIL"

    def test_review_with_convergence_passes(self):
        fm = {"description": "Evaluates a skill", "name": "review-skill"}
        body = "Complete when all verdicts recorded AND re-run variance is zero across two consecutive runs."
        assert check_COMP_X(body, fm)["verdict"] == "PASS"

    def test_agent_artifact_returns_na(self):
        # Issue #74: COMP-X encodes skill-review-semantics (convergence predicate
        # on review-* skills). Agents emit structured output validated by the
        # merge layer; their success contract is captured by TC-3 in
        # agent-evaluation-guide.md (not yet a binary item). Return NA until
        # TC-3 is binarised under issue #75 / #76.
        fm = {"description": "Verifies step ordering in a skill", "name": "review-perspective-clarity"}
        body = "emit certificate. return exactly this structure."
        result = check_COMP_X(body, fm, artifact_type="agent")
        assert result["verdict"] == "NA"
        assert "#75" in result["evidence"]["reason"]

    def test_skill_artifact_explicit_still_evaluated(self):
        # Positive control: explicit artifact_type="skill" keeps existing behavior.
        fm = {"description": "Creates a scaffold"}
        body = "Complete when all output sections are emitted."
        assert check_COMP_X(body, fm, artifact_type="skill")["verdict"] == "PASS"

    # issue #102 boundary cases — primary-verb + allowlist refinement.
    def test_audit_mcp_auth_uses_standard_clause(self):
        # audit-mcp-auth is NOT in the review allowlist (one-time bug
        # detector). Description verb ``Audits`` no longer triggers
        # the review-skill clause. Standard skill clause applies; if
        # the body lacks ``complete when``, it FAILs on success-condition.
        fm = {"description": "Audits MCP OAuth credential storage", "name": "audit-mcp-auth"}
        body = "Run security check. Report findings."
        result = check_COMP_X(body, fm)
        assert result["verdict"] == "FAIL"
        assert result["evidence"]["reason"] == "no explicit success condition"

    def test_check_repo_health_object_position_skipped(self):
        # ``before running reviews`` puts ``reviews`` in object position;
        # the old substring-anywhere logic mis-classified this as a
        # review-class skill. New logic: not in allowlist → standard.
        fm = {
            "description": "Verifies reference freshness, before running reviews.",
            "name": "check-repo-health",
        }
        body = "Complete when all references are scanned."
        assert check_COMP_X(body, fm)["verdict"] == "PASS"

    def test_evaluate_first_word_not_allowlisted(self):
        # ``Evaluates a single SKILL.md`` no longer auto-classifies as
        # review-class — only allowlist membership counts.
        fm = {"description": "Evaluates a single SKILL.md", "name": "foo"}
        body = "Complete when output emitted."
        assert check_COMP_X(body, fm)["verdict"] == "PASS"

    def test_youre_done_when_passes(self):
        # Extended success-condition: ``You are done when ...``
        fm = {"description": "Scaffolds", "name": "scaffold-something"}
        body = "You are done when all sections are emitted."
        assert check_COMP_X(body, fm)["verdict"] == "PASS"

    def test_completion_block_marker_passes(self):
        # Extended success-condition: ``COMPLETION:`` block marker.
        fm = {"description": "Audits stuff", "name": "audit-something"}
        body = "Run checks.\n\nCOMPLETION: End response with SCAN COMPLETE."
        assert check_COMP_X(body, fm)["verdict"] == "PASS"

    def test_review_with_evidence_citation_passes(self):
        # Extended convergence: ``must cite at least one checklist ID``
        # is recognized as evidence-citation predicate.
        fm = {"description": "Evaluates a skill", "name": "review-skill"}
        body = "Complete when justifications must cite at least one checklist ID."
        assert check_COMP_X(body, fm)["verdict"] == "PASS"


class TestCOMPY:
    def test_binary_predicate_passes(self):
        assert check_COMP_Y("validate that the count equals 24")["verdict"] == "PASS"

    def test_holistic_phrase_fails(self):
        assert check_COMP_Y("output looks good when complete")["verdict"] == "FAIL"

    def test_no_predicate_fails(self):
        assert check_COMP_Y("emit the report")["verdict"] == "FAIL"


class TestCOMPZ:
    def test_evidence_passes(self):
        assert check_COMP_Z("each finding has Evidence: <quote>")["verdict"] == "PASS"

    def test_no_trail_fails(self):
        assert check_COMP_Z("emit findings as a list")["verdict"] == "FAIL"


class TestCOMPW:
    def test_non_iterative_na(self):
        assert check_COMP_W("parse input, emit report")["verdict"] == "NA"

    def test_loop_with_termination_passes(self):
        body = "Retry up to 3 times; escalate after 3 consecutive failures."
        assert check_COMP_W(body)["verdict"] == "PASS"

    def test_loop_without_termination_fails(self):
        assert check_COMP_W("retry on failure")["verdict"] == "FAIL"

    # issue #103 boundary cases — bounded-iteration / context-aware NA.
    def test_for_each_no_longer_triggers(self):
        # ``for each`` was removed from LOOP_PATTERN; bounded list
        # iteration is termination by construction.
        body = "For each finding, emit a diagnostic line."
        assert check_COMP_W(body)["verdict"] == "NA"

    def test_negated_retry_skipped(self):
        body = "Process the entry. Do not retry on failure — surface as evidence."
        assert check_COMP_W(body)["verdict"] == "NA"

    def test_loop_back_to_phase_skipped(self):
        # ``loop back to Phase 3`` is one-shot reprocess of a finite set,
        # not an unbounded loop.
        body = "On 'Address findings': loop back to Phase 3 with the Low recommendations."
        assert check_COMP_W(body)["verdict"] == "NA"

    def test_iterate_field_path_skipped(self):
        # ``Iterate case.scenarios`` is bounded by the enumerable.
        body = "Iterate `case.scenarios` (each has mode + name + expected_writes_under)."
        assert check_COMP_W(body)["verdict"] == "NA"

    def test_genuine_unbounded_retry_fails(self):
        # Plain ``retry on failure`` still FAILs (positive control).
        body = "On error, retry the request. Always retry until success."
        assert check_COMP_W(body)["verdict"] == "FAIL"


class TestSAMP1:
    def test_no_param_na(self):
        assert check_SAMP_1("plain body")["verdict"] == "NA"

    def test_temperature_fails(self):
        assert check_SAMP_1("Set temperature=0.5 during scoring")["verdict"] == "FAIL"

    def test_top_p_fails(self):
        assert check_SAMP_1("Use top_p: 0.9 for variety")["verdict"] == "FAIL"


class TestSAMP2:
    def test_no_param_na(self):
        assert check_SAMP_2("name: foo\ndescription: bar")["verdict"] == "NA"

    def test_temperature_in_frontmatter_fails(self):
        assert check_SAMP_2("name: foo\ntemperature: 0.3")["verdict"] == "FAIL"


class TestPE1:
    def test_clean_body_passes(self):
        assert check_PE_1("Verify the output matches the schema.")["verdict"] == "PASS"

    def test_think_step_by_step_fails(self):
        assert check_PE_1("Think step by step before answering.")["verdict"] == "FAIL"

    def test_reason_carefully_about_fails(self):
        assert check_PE_1("Reason carefully about each tool call.")["verdict"] == "FAIL"

    def test_lets_think_fails(self):
        assert check_PE_1("Let's think through this problem.")["verdict"] == "FAIL"

    def test_benign_think_carefully_passes(self):
        # 'think carefully' alone must NOT fire — too common in benign prose.
        assert check_PE_1("Think carefully about tool choice.")["verdict"] == "PASS"

    def test_code_block_exemplar_passes(self):
        # Phrases quoted inside code fences are anti-pattern catalog entries.
        body = "The following is a known anti-pattern:\n```\nThink step by step first.\n```\nThe correct directive is to verify output."
        assert check_PE_1(body)["verdict"] == "PASS"

    def test_inline_code_exemplar_passes(self):
        body = "Avoid phrases like `think step by step` in directives."
        assert check_PE_1(body)["verdict"] == "PASS"


class TestPE2:
    def test_clean_body_passes(self):
        assert check_PE_2("Write the report. Abort on unwritable path.")["verdict"] == "PASS"

    def test_try_to_fails(self):
        assert check_PE_2("Try to format the response.")["verdict"] == "FAIL"

    def test_if_possible_fails(self):
        assert check_PE_2("Return JSON if possible.")["verdict"] == "FAIL"

    def test_as_appropriate_fails(self):
        assert check_PE_2("Handle errors as appropriate.")["verdict"] == "FAIL"

    def test_as_needed_not_flagged(self):
        # 'as needed' is intentionally excluded — collides with Anthropic's
        # progressive-disclosure canonical phrasing ("loaded as needed").
        body = "Progressive disclosure: resources are loaded as needed."
        assert check_PE_2(body)["verdict"] == "PASS"

    def test_code_block_exemplar_passes(self):
        body = "Known anti-pattern:\n```\nTry to handle it if possible.\n```\nUse concrete triggers instead."
        assert check_PE_2(body)["verdict"] == "PASS"

    def test_inline_code_exemplar_passes(self):
        body = "Reviewers flag hedges like `try to` and `if possible` in directives."
        assert check_PE_2(body)["verdict"] == "PASS"


class TestSP2b:
    def test_absent_tools_na(self):
        assert check_SP_2b("body", {})["verdict"] == "NA"

    def test_read_only_subset_na(self):
        fm = {"allowed-tools": ["Read", "Glob"]}
        assert check_SP_2b("body", fm)["verdict"] == "NA"

    def test_mutating_tool_with_binding_passes(self):
        fm = {"allowed-tools": ["Read", "Write"]}
        body = "Write is restricted to $CLAUDE_PLUGIN_DATA/reports/ only. Read is used only for loading references."
        assert check_SP_2b(body, fm)["verdict"] == "PASS"

    def test_mutating_tool_without_binding_fails(self):
        fm = {"allowed-tools": ["Read", "Write", "Bash"]}
        body = "This skill uses Write and Bash to emit reports."
        assert check_SP_2b(body, fm)["verdict"] == "FAIL"


class TestSP4b:
    def test_no_write_na(self):
        fm = {"allowed-tools": ["Read", "Bash"]}
        assert check_SP_4b("body", fm)["verdict"] == "NA"

    def test_write_without_partner_na(self):
        fm = {"allowed-tools": ["Read", "Write"]}
        assert check_SP_4b("body", fm)["verdict"] == "NA"

    def test_tier_a_all_constrained_passes(self):
        fm = {"allowed-tools": ["Write", "Bash", "Agent"]}
        body = (
            "Write is restricted to report paths only. "
            "Bash is allowlisted to specific commands via policy_gate. "
            "Agent is restricted to allowlisted subagent_type values."
        )
        assert check_SP_4b(body, fm)["verdict"] == "PASS"

    def test_tier_a_unconstrained_fails(self):
        fm = {"allowed-tools": ["Write", "Bash"]}
        body = "This skill uses Write and Bash freely without scope limits."
        assert check_SP_4b(body, fm)["verdict"] == "FAIL"


class TestIJ1b:
    def test_no_write_na(self):
        fm = {"allowed-tools": ["Read"]}
        assert check_IJ_1b("$ARGUMENTS body", fm)["verdict"] == "NA"

    def test_no_external_input_na(self):
        fm = {"allowed-tools": ["Write"]}
        assert check_IJ_1b("plain body no inputs", fm)["verdict"] == "NA"

    def test_both_predicates_passes(self):
        fm = {"allowed-tools": ["Write"]}
        body = (
            "Validate repo-slug matches ^[a-z0-9-]+$ before constructing the path. "
            "Preview via AskUserQuestion before first Write."
        )
        assert check_IJ_1b(body, fm)["verdict"] == "PASS"

    def test_missing_validation_fails(self):
        fm = {"allowed-tools": ["Write"]}
        body = "Use $ARGUMENTS. Preview via AskUserQuestion before Write."
        result = check_IJ_1b(body, fm)
        assert result["verdict"] == "FAIL"
        assert "validation-predicate" in result["evidence"]["missing"]

    def test_missing_write_gate_fails(self):
        fm = {"allowed-tools": ["Write"]}
        body = "Validate $ARGUMENTS format matches ^[a-z]+$ then write."
        result = check_IJ_1b(body, fm)
        assert result["verdict"] == "FAIL"
        assert "write-gate-predicate" in result["evidence"]["missing"]


class TestRL1b:
    def test_non_agentic_na(self):
        assert check_RL_1b("body", is_agentic_flag=False)["verdict"] == "NA"

    def test_max_wait_passes(self):
        assert check_RL_1b("with max wait 5 minutes", is_agentic_flag=True)["verdict"] == "PASS"

    def test_max_iterations_passes(self):
        assert check_RL_1b("max iterations: 3", is_agentic_flag=True)["verdict"] == "PASS"

    def test_status_predicate_passes(self):
        assert check_RL_1b('status: "terminal"', is_agentic_flag=True)["verdict"] == "PASS"

    def test_no_predicate_fails(self):
        assert check_RL_1b("keep trying", is_agentic_flag=True)["verdict"] == "FAIL"

    # issue #108 boundary cases — bounded-iteration NA.
    def test_for_each_intervention_na(self):
        body = "For each intervention, follow the type-specific procedure below."
        assert check_RL_1b(body, is_agentic_flag=True)["verdict"] == "NA"

    def test_for_each_recommendation_na(self):
        body = "For each mapped recommendation, verify it can drive a real Edit."
        assert check_RL_1b(body, is_agentic_flag=True)["verdict"] == "NA"

    def test_repeat_for_each_recommendation_na(self):
        body = "[Repeat for each recommendation, ordered by impact]"
        assert check_RL_1b(body, is_agentic_flag=True)["verdict"] == "NA"

    def test_unbounded_while_true_fails(self):
        # ``while true`` is a genuine unbounded loop — must FAIL even
        # if a ``for each`` is also present.
        body = "For each finding: while true, retry the operation."
        assert check_RL_1b(body, is_agentic_flag=True)["verdict"] == "FAIL"

    def test_keep_verbing_fails(self):
        body = "For each entry, keep retrying until the response is complete."
        # ``keep retrying`` is unbounded — must FAIL despite for-each.
        assert check_RL_1b(body, is_agentic_flag=True)["verdict"] == "FAIL"


class TestRL3b:
    def test_non_agentic_na(self):
        assert check_RL_3b("retry", is_agentic_flag=False)["verdict"] == "NA"

    def test_no_retry_na(self):
        assert check_RL_3b("plain body", is_agentic_flag=True)["verdict"] == "NA"

    def test_retry_with_cap_passes(self):
        body = "Maximum 3 reflection cycles; retry each up to 2 times on failure."
        assert check_RL_3b(body, is_agentic_flag=True)["verdict"] == "PASS"

    def test_retry_without_cap_fails(self):
        body = "retry the call and continue"
        assert check_RL_3b(body, is_agentic_flag=True)["verdict"] == "FAIL"

    def test_negated_retry_na(self):
        # issue #113: ``do not retry`` should not trigger RL-3b.
        assert check_RL_3b("Do not retry on transient errors.", is_agentic_flag=True)["verdict"] == "NA"

    def test_never_regenerate_na(self):
        # issue #113: ``never regenerate`` is a negated retry.
        assert check_RL_3b("Never regenerate the token mid-session.", is_agentic_flag=True)["verdict"] == "NA"

    def test_adjust_no_longer_triggers_na(self):
        # issue #113: ``adjust`` dropped from RL_3B_RETRY — option-label false positive.
        assert check_RL_3b('Option label "Adjust" lets the user reconfigure.', is_agentic_flag=True)["verdict"] == "NA"

    def test_backtick_quoted_retry_na(self):
        # issue #113: backtick-quoted retry tokens are documentation, not directives.
        assert check_RL_3b("The `retry` field configures behavior.", is_agentic_flag=True)["verdict"] == "NA"

    def test_real_retry_without_cap_still_fails(self):
        # issue #113: regression guard — non-negated, non-quoted retry still FAILs without cap.
        body = "On error, retry the API call until success."
        assert check_RL_3b(body, is_agentic_flag=True)["verdict"] == "FAIL"

    def test_capless_regenerate_still_fails(self):
        # issue #113: second FAIL case across a different retained token.
        body = "If the response is malformed, regenerate the answer and continue."
        assert check_RL_3b(body, is_agentic_flag=True)["verdict"] == "FAIL"

    @pytest.mark.parametrize("token", ["retry", "regenerate", "redisplay", "ask again"])
    def test_retained_tokens_each_trigger(self, token):
        # issue #113: regression guard against accidental over-deletion when
        # ``adjust`` was dropped from RL_3B_RETRY. Each retained token without a
        # cap must still produce FAIL.
        body = f"On error, {token} the call until success."
        assert check_RL_3b(body, is_agentic_flag=True)["verdict"] == "FAIL"


class TestRL4b:
    def test_non_agentic_na(self):
        assert check_RL_4b("body", is_agentic_flag=False)["verdict"] == "NA"

    def test_askuserquestion_passes(self):
        assert check_RL_4b("ask via AskUserQuestion", is_agentic_flag=True)["verdict"] == "PASS"

    def test_partial_status_passes(self):
        assert check_RL_4b('status: "partial"', is_agentic_flag=True)["verdict"] == "PASS"

    def test_escalate_heading_passes(self):
        body = "\n- escalate when budget exhausted\n"
        assert check_RL_4b(body, is_agentic_flag=True)["verdict"] == "PASS"

    def test_no_path_fails(self):
        assert check_RL_4b("silently continue on failure", is_agentic_flag=True)["verdict"] == "FAIL"


class TestRL9b:
    def test_not_needed_na(self):
        assert check_RL_9b("body", "name: foo", needs_rl9b_flag=False)["verdict"] == "NA"

    def test_redact_rule_passes(self):
        body = "redact token-like substrings matching /[A-Za-z0-9_-]{20,}/ with <REDACTED>"
        assert check_RL_9b(body, "", needs_rl9b_flag=True)["verdict"] == "PASS"

    def test_truncate_rule_passes(self):
        body = "truncate evidence blocks at 500 characters before write"
        assert check_RL_9b(body, "", needs_rl9b_flag=True)["verdict"] == "PASS"

    def test_skip_env_rule_passes(self):
        body = "skip writes entirely when path matches **/*.env or credentials.*"
        assert check_RL_9b(body, "", needs_rl9b_flag=True)["verdict"] == "PASS"

    def test_no_rule_fails(self):
        body = "read user file and write output"
        assert check_RL_9b(body, "", needs_rl9b_flag=True)["verdict"] == "FAIL"


class TestAH2b:
    def test_no_trigger_na(self):
        assert check_AH_2b("plain body")["verdict"] == "NA"

    def test_trigger_with_default_passes(self):
        body = "If $ARGUMENTS is empty, default to **/SKILL.md glob and prompt the user to pick."
        assert check_AH_2b(body)["verdict"] == "PASS"

    def test_trigger_with_prompt_stop_passes(self):
        body = 'If $ARGUMENTS is empty, prompt the user: "Provide the path to a SKILL.md file to review." and stop.'
        assert check_AH_2b(body)["verdict"] == "PASS"

    def test_trigger_without_response_fails(self):
        body = "If $ARGUMENTS is missing, the skill cannot run."
        assert check_AH_2b(body)["verdict"] == "FAIL"


class TestWS2b:
    """WS-2b conditional specificity with block marker context — issue #70."""

    def test_no_marker_na(self):
        body = "Regular skill body with no block markers anywhere.\n\nIf present → do X."
        result = check_WS_2b(body)
        assert result["verdict"] == "NA"
        assert "no block-marker" in result["evidence"]["reason"]

    def test_marker_without_if_clause_na(self):
        body = "Here is the block:\n\n---config---\nmode: x\n---\n\nEnd of body."
        result = check_WS_2b(body)
        assert result["verdict"] == "NA"

    def test_marker_with_prose_predicate_passes(self):
        body = (
            "Check whether the prompt contains an orchestration metadata block:\n\n"
            "---orchestration---\nmode: orchestrated\n---\n\n"
            "- If present → orchestrated mode\n- If absent → standalone mode\n"
        )
        assert check_WS_2b(body)["verdict"] == "PASS"

    def test_marker_without_prose_predicate_fails(self):
        body = (
            "Some intro text with no predicate here.\n\n"
            "---orchestration---\nmode: x\n---\n\n"
            "- If present → X\n- If absent → Y\n"
        )
        result = check_WS_2b(body)
        assert result["verdict"] == "FAIL"
        assert "no prose predicate" in result["evidence"]["reason"]

    def test_review_skill_fixture_passes(self):
        body = REVIEW_SKILL_FIXTURE.read_text(encoding="utf-8")
        assert check_WS_2b(body)["verdict"] == "PASS"

    def test_scaffold_skill_fixture_na(self):
        body = SCAFFOLD_SKILL_FIXTURE.read_text(encoding="utf-8")
        assert check_WS_2b(body)["verdict"] == "NA"


class TestWS5b:
    """WS-5b negation paired with positive whitelist — issue #89."""

    def test_no_negation_list_na(self):
        body = "Regular skill body with no NEVER or DO NOT lists anywhere."
        assert check_WS_5b(body)["verdict"] == "NA"

    def test_single_token_after_negation_na(self):
        # Spec requires verb-list (≥2 comma-separated items); single token
        # without commas does not trigger.
        body = "Do NOT panic."
        assert check_WS_5b(body)["verdict"] == "NA"

    def test_negation_with_whitelist_passes(self):
        # Single-token list per spec regex (\S+ requires no inner whitespace).
        body = (
            "DO NOT use rm, mv, dd, sed. ALLOWED: ls, cat, grep — read-only "
            "operations only."
        )
        assert check_WS_5b(body)["verdict"] == "PASS"

    def test_negation_with_only_pattern_passes(self):
        body = (
            "NEVER write rm, mv, dd, sudo in this skill — only read "
            "and only use git for inspection."
        )
        assert check_WS_5b(body)["verdict"] == "PASS"

    def test_negation_without_whitelist_fails(self):
        body = (
            "NEVER use rm, mv, dd, sed in this workflow. "
            "The agent should be careful with destructive operations."
        )
        result = check_WS_5b(body)
        assert result["verdict"] == "FAIL"
        assert "lacks positive whitelist" in result["evidence"]["reason"]

    def test_must_not_with_whitelist_passes(self):
        body = (
            "MUST NOT call: api, db, kafka, redis. "
            "Use only the file system and stdin."
        )
        assert check_WS_5b(body)["verdict"] == "PASS"


class TestRD5b:
    """RD-5b step-naming consistency — issue #70."""

    def test_no_schemes_na(self):
        body = "Plain body with no numbered steps or phase markers."
        result = check_RD_5b(body)
        assert result["verdict"] == "NA"

    def test_single_step_number_scheme_na(self):
        body = "## Workflow\n\n### 1. First\n\n### 2. Second\n\n### 3. Third\n"
        result = check_RD_5b(body)
        assert result["verdict"] == "NA"
        assert "single scheme" in result["evidence"]["reason"]

    def test_two_schemes_with_mapping_clause_na(self):
        body = (
            "## Phase 1 — Setup\n\n### Step A: Probe\n\n"
            "**Note:** Phase 1 contains Step A as the entry point.\n"
        )
        result = check_RD_5b(body)
        assert result["verdict"] == "NA"
        assert "mapping clause" in result["evidence"]["reason"]

    def test_three_schemes_without_mapping_fails(self):
        body = (
            "## Phase 1 — Setup\n"
            "## Phase 2 — Evaluation\n\n"
            "### Step A: Goal\n\n"
            "### Step B-multi — Dispatch\n\n"
            "**b.0 — First substep.**\n\n"
            "**b.1 — Second substep.**\n"
        )
        result = check_RD_5b(body)
        assert result["verdict"] == "FAIL"
        assert set(result["evidence"]["schemes"]) == {"PHASE", "STEP_LETTER", "DOTTED"}

    def test_review_skill_fixture_fails(self):
        body = REVIEW_SKILL_FIXTURE.read_text(encoding="utf-8")
        result = check_RD_5b(body)
        assert result["verdict"] == "FAIL"

    def test_scaffold_skill_fixture_na(self):
        body = SCAFFOLD_SKILL_FIXTURE.read_text(encoding="utf-8")
        result = check_RD_5b(body)
        assert result["verdict"] == "NA"

    def test_depth_4_heading_excluded_from_step_number(self):
        # `#### 1. [Title]` inside a certificate template must NOT
        # count as STEP_NUMBER scheme (heading depth > 3).
        body = (
            "## Phase 2\n\n### Step A\n\n#### 1. Certificate field\n\n#### 2. Another field\n"
        )
        result = check_RD_5b(body)
        # Only PHASE + STEP_LETTER detected → 2 schemes, no mapping → FAIL.
        assert result["verdict"] == "FAIL"
        assert "STEP_NUMBER" not in set(result["evidence"]["schemes"])


class TestBinaryItemIdsSync:
    """Parity between evaluator.BINARY_ITEM_IDS and merge_findings.BINARY_ITEM_IDS."""

    def test_sync(self):
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import importlib

        merge_findings = importlib.import_module("merge_findings")
        assert set(BINARY_ITEM_IDS) == set(merge_findings.BINARY_ITEM_IDS)

    def test_wsb_rdb_in_item_dimension(self):
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import importlib

        merge_findings = importlib.import_module("merge_findings")
        assert merge_findings.ITEM_DIMENSION["WS-2b"] == "Clarity"
        assert merge_findings.ITEM_DIMENSION["WS-4"] == "Clarity"
        assert merge_findings.ITEM_DIMENSION["RD-5b"] == "Clarity"

    def test_narrative_parents_include_ws_rd(self):
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import importlib

        merge_findings = importlib.import_module("merge_findings")
        assert "WS-2" in merge_findings.NARRATIVE_PARENT_IDS
        assert "WS-4" in merge_findings.NARRATIVE_PARENT_IDS
        assert "RD-5" in merge_findings.NARRATIVE_PARENT_IDS


# ---------------------------------------------------------------------------
# Schema stability + end-to-end fixtures.
# ---------------------------------------------------------------------------

EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "artifact_path",
    "artifact_type",
    "artifact_frontmatter",
    "verdicts",
    "stats",
    "non_binary_items",
    "runner_error",
}


class TestSchemaStability:
    def test_top_level_keys_exact(self):
        result = evaluate(REVIEW_SKILL_FIXTURE)
        assert set(result.keys()) == EXPECTED_TOP_LEVEL_KEYS

    def test_schema_version_is_one(self):
        result = evaluate(REVIEW_SKILL_FIXTURE)
        assert result["schema_version"] == 1
        assert SCHEMA_VERSION == 1

    def test_verdicts_cover_all_binary_items(self):
        result = evaluate(REVIEW_SKILL_FIXTURE)
        assert set(result["verdicts"].keys()) == set(BINARY_ITEM_IDS)

    def test_evidence_tolerates_unknown_keys(self):
        result = evaluate(REVIEW_SKILL_FIXTURE)
        for item_id, v in result["verdicts"].items():
            assert "verdict" in v, f"{item_id} missing verdict"
            assert "evidence" in v, f"{item_id} missing evidence"
            assert isinstance(v["evidence"], dict)

    def test_stats_counts_sum_to_32(self):
        result = evaluate(REVIEW_SKILL_FIXTURE)
        s = result["stats"]
        assert s["pass"] + s["fail"] + s["na"] == 32


REVIEW_SKILL_EXPECTED = {
    "META-1a": "PASS",
    "META-2": "PASS",
    "META-3a": "PASS",
    "META-3b": "PASS",
    "META-3c": "FAIL",  # review-skill has no token unique vs all 31 siblings
    "META-4": "PASS",
    "CLAR-1": "PASS",
    "CLAR-2": "PASS",  # issue #104: antecedent-aware narrowing
    "CLAR-3": "FAIL",
    "CLAR-4": "PASS",
    "WS-2b": "PASS",
    "WS-5b": "NA",
    "WS-6": "NA",
    "RD-5b": "FAIL",
    "CE-X": "PASS",
    "COMP-V": "PASS",
    "COMP-X": "PASS",  # issue #102: extended convergence patterns
    "COMP-Y": "PASS",
    "COMP-Z": "PASS",
    "COMP-W": "NA",  # issue #103: ``for each`` removed from LOOP_PATTERN
    "SAMP-1": "NA",
    "SAMP-2": "NA",
    "PE-1": "PASS",
    "PE-2": "PASS",
    "SP-2b": "PASS",
    "SP-4b": "PASS",
    "IJ-1b": "FAIL",
    "RL-1b": "PASS",
    "RL-3b": "NA",
    "RL-4b": "PASS",
    "RL-9b": "PASS",
    "AH-2b": "PASS",
}

REVIEW_PERSPECTIVE_CLARITY_AGENT_EXPECTED = {
    "META-1a": "PASS",
    "META-2": "FAIL",
    "META-3a": "PASS",
    "META-3b": "NA",  # Issue #74: skill-to-skill semantics; agent policy pending #75.
    "META-3c": "NA",  # skill-only scope per check_META_3c
    "META-4": "PASS",
    "CLAR-1": "PASS",
    "CLAR-2": "PASS",
    "CLAR-3": "NA",
    "CLAR-4": "NA",
    "WS-2b": "NA",
    "WS-5b": "NA",
    "WS-6": "NA",
    "RD-5b": "NA",
    "CE-X": "NA",
    "COMP-V": "NA",
    "COMP-X": "NA",  # Issue #74: skill-review-semantics only; agent TC-3 pending #75/#76.
    "COMP-Y": "PASS",
    "COMP-Z": "PASS",
    "COMP-W": "NA",  # issue #103
    "SAMP-1": "NA",
    "SAMP-2": "NA",
    "PE-1": "PASS",
    "PE-2": "PASS",
    "SP-2b": "NA",
    "SP-4b": "NA",
    "IJ-1b": "NA",
    "RL-1b": "NA",  # issue #108: bounded-iteration NA
    "RL-3b": "NA",
    "RL-4b": "FAIL",
    "RL-9b": "NA",
    "AH-2b": "NA",
}

SCAFFOLD_SKILL_EXPECTED = {
    "META-1a": "PASS",
    "META-2": "PASS",
    "META-3a": "PASS",
    "META-3b": "FAIL",
    "META-3c": "FAIL",
    "META-4": "PASS",
    "CLAR-1": "PASS",
    "CLAR-2": "PASS",  # issue #104
    "CLAR-3": "PASS",  # issue #105
    "CLAR-4": "NA",
    "WS-2b": "NA",
    "WS-5b": "NA",
    "WS-6": "PASS",
    "RD-5b": "NA",
    "CE-X": "FAIL",
    "COMP-V": "NA",
    "COMP-X": "FAIL",
    "COMP-Y": "FAIL",
    "COMP-Z": "FAIL",
    "COMP-W": "NA",  # issue #103
    "SAMP-1": "NA",
    "SAMP-2": "NA",
    "PE-1": "PASS",
    "PE-2": "PASS",
    "SP-2b": "PASS",
    "SP-4b": "FAIL",
    "IJ-1b": "PASS",
    "RL-1b": "PASS",
    "RL-3b": "FAIL",
    "RL-4b": "PASS",
    "RL-9b": "FAIL",
    "AH-2b": "NA",
}


class TestEndToEndFixtures:
    """Pinned verdicts against frozen fixture copies of review-skill
    and scaffold-skill SKILL.md (not live files). Drift catcher."""

    @pytest.mark.parametrize(
        "fixture, expected",
        [
            (REVIEW_SKILL_FIXTURE, REVIEW_SKILL_EXPECTED),
            (SCAFFOLD_SKILL_FIXTURE, SCAFFOLD_SKILL_EXPECTED),
            (REVIEW_PERSPECTIVE_CLARITY_AGENT_FIXTURE, REVIEW_PERSPECTIVE_CLARITY_AGENT_EXPECTED),
        ],
        ids=["review-skill", "scaffold-skill", "review-perspective-clarity-agent"],
    )
    def test_fixture_verdicts(self, fixture, expected):
        assert fixture.exists(), f"fixture missing: {fixture}"
        result = evaluate(fixture)
        assert result["stats"]["runner_error"] == 0
        assert result["stats"]["pass"] + result["stats"]["fail"] + result["stats"]["na"] == 32
        actual = {k: v["verdict"] for k, v in result["verdicts"].items()}
        assert actual == expected

    def test_agent_fixture_classified_as_agent(self):
        # Issue #74: verify classify_artifact correctly returns "agent" for a
        # fixture under tests/fixtures/rubric_evaluator/agents/*.md, and the
        # agent-only NA clauses fire (COMP-X, META-3b).
        result = evaluate(REVIEW_PERSPECTIVE_CLARITY_AGENT_FIXTURE)
        assert result["artifact_type"] == "agent"
        assert result["verdicts"]["COMP-X"]["verdict"] == "NA"
        assert result["verdicts"]["META-3b"]["verdict"] == "NA"
        # Sanity: these two are the only items the gating changes for this
        # fixture — compare against the expected map to catch silent drift.
        assert "#75" in result["verdicts"]["COMP-X"]["evidence"]["reason"]
        assert "#75" in result["verdicts"]["META-3b"]["evidence"]["reason"]


# ---------------------------------------------------------------------------
# Repo-wide smoke — strict allow-list + lenient-on-all.
# ---------------------------------------------------------------------------


STRICT_ALLOWLIST = {"review-skill", "review-claude-config", "scaffold-skill"}


class TestRepoWideSmokeStrict:
    """Allow-listed skills MUST have runner_error == 0."""

    @pytest.mark.parametrize("skill_name", sorted(STRICT_ALLOWLIST))
    def test_stable_skill_runs_clean(self, skill_name):
        path = REPO_ROOT / "skills" / skill_name / "SKILL.md"
        assert path.exists(), f"allow-listed skill missing: {path}"
        result = evaluate(path)
        assert result["stats"]["runner_error"] == 0
        total = result["stats"]["pass"] + result["stats"]["fail"] + result["stats"]["na"]
        assert total == 32


class TestRepoWideSmokeLenient:
    """Every skills/*/SKILL.md evaluator invocation returns 32 verdicts;
    runner_error per skill is logged but not asserted."""

    def test_all_skills_produce_32_verdicts(self):
        skills = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))
        assert len(skills) >= 10, "expected multiple skill targets"
        errors: list[tuple[str, int]] = []
        for p in skills:
            result = evaluate(p)
            total = result["stats"]["pass"] + result["stats"]["fail"] + result["stats"]["na"]
            assert total == 32, f"{p}: total {total} != 32"
            if result["stats"]["runner_error"]:
                errors.append((str(p), result["stats"]["runner_error"]))
        # Surface drift without failing the suite: errors are reported
        # in the test output but allowed.
        if errors:
            sys.stderr.write(f"\nRepoWideSmokeLenient errors (non-blocking): {errors}\n")


# ---------------------------------------------------------------------------
# Non-binary coverage against the evaluation guide table.
# ---------------------------------------------------------------------------


class TestNonBinaryCoverage:
    def test_guide_items_subset_of_binary_union_non_binary(self):
        guide = REPO_ROOT / "skills" / "review-skill" / "references" / "skill-evaluation-guide.md"
        assert guide.exists()
        text = guide.read_text(encoding="utf-8")
        import re as _re

        # Table rows look like: | ID | ...
        rows = _re.findall(r"^\|\s*([A-Z]+-\d+[a-z]?)\s*\|", text, _re.MULTILINE)
        guide_ids = set(rows)
        covered = set(BINARY_ITEM_IDS) | set(NON_BINARY_ITEMS)
        missing = guide_ids - covered
        assert not missing, f"guide items not covered: {missing}"


# ---------------------------------------------------------------------------
# Runner-error handling + exit codes.
# ---------------------------------------------------------------------------


class TestRunnerErrorHandling:
    def test_missing_file_global_error(self, tmp_path):
        # evaluate() itself raises if the file doesn't exist — the global
        # try/except lives in main(). We test the CLI path in TestExitCodes.
        with pytest.raises(FileNotFoundError):
            evaluate(tmp_path / "missing.md")

    def test_empty_file_no_crash(self, tmp_path):
        p = tmp_path / "empty.md"
        p.write_text("", encoding="utf-8")
        result = evaluate(p)
        assert result["stats"]["runner_error"] == 0
        # All 32 items produce verdicts (mostly NA/FAIL for missing content).
        total = result["stats"]["pass"] + result["stats"]["fail"] + result["stats"]["na"]
        assert total == 32

    def test_no_frontmatter_no_crash(self, tmp_path):
        p = tmp_path / "body-only.md"
        p.write_text("# heading\n\nBody without any frontmatter.\n", encoding="utf-8")
        result = evaluate(p)
        assert result["stats"]["runner_error"] == 0


RUNNER_PATH = REPO_ROOT / "scripts" / "rubric_binary_evaluator.py"


class TestExitCodes:
    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(RUNNER_PATH), *args],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

    def test_exit_0_on_clean(self):
        result = self._run(str(REVIEW_SKILL_FIXTURE))
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["schema_version"] == 1
        assert data["stats"]["runner_error"] == 0

    def test_exit_1_on_missing_file(self, tmp_path):
        result = self._run(str(tmp_path / "nonexistent.md"))
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["runner_error"] is not None
        assert data["verdicts"] == {}

    def test_exit_1_on_bad_argv(self):
        result = subprocess.run(
            [sys.executable, str(RUNNER_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        # argparse exits 2 when required positional is missing; that's
        # the argparse default and is distinct from our exit-2-on-
        # runner_error. Both are non-zero and Phase 2 consumers must
        # check the JSON schema_version key, which argparse's error
        # message does NOT contain.
        assert result.returncode != 0
        assert "schema_version" not in result.stdout


# ---------------------------------------------------------------------------
# tools_list normalization.
# ---------------------------------------------------------------------------


class TestToolsList:
    def test_list_form(self):
        assert tools_list({"allowed-tools": ["Read", "Write"]}) == ["Read", "Write"]

    def test_comma_string_form(self):
        assert tools_list({"allowed-tools": "Read, Write, Bash"}) == ["Read", "Write", "Bash"]

    def test_absent(self):
        assert tools_list({}) == []

    def test_empty_string(self):
        assert tools_list({"allowed-tools": ""}) == []
