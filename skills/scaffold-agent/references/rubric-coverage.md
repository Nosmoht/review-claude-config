---
name: rubric-coverage
description: Maps each binary skill rubric item and agent rubric item to a scaffold-agent generator directive or documents why it is runtime-OOS. Source of truth for check_scaffold_quality.py --verify-matrix-complete.
last_refreshed: 2026-05-27
---

# Rubric Coverage Matrix — scaffold-agent

Maps every item from two tables in `scoring-rubric.md §Item Inventory`:
1. `§Binary-Evaluated Items (skill rubric, 30)` — applicable subset for agents
2. `§Agent Items` — all 35 agent-specific items

`Enforcement` closed set: `by-template | by-AskUserQuestion | by-directive | runtime-OOS`

- `by-template` — scaffold's `agent-template.md` file embeds the requirement at a named slot.
- `by-AskUserQuestion` — scaffold's SKILL.md step 3 collects the value via user-facing prompt.
- `by-directive` — scaffold's `quality-patterns.md` contains an explicit generation directive.
- `runtime-OOS` — runtime-resolved-by-user; NOT scaffold-enforceable. Rationale text mandatory.

## Skill Binary Items (applicable subset for agents)

Items marked `NA-per-evaluator` are documented as NA in `rubric_binary_evaluator.py` known-limitations for agent artifacts.

| Item ID | Dimension | Cap | Generator directive (file:section) | Enforcement | Status |
|---|---|---|---|---|---|
| META-1a | Metadata | — | `quality-patterns.md §META-1a` — directive instructs LLM to embed body's primary trigger keyword in the description | by-directive | in-scope |
| META-2 | Metadata | C | `quality-patterns.md §META-2` — directive instructs LLM to include "Do NOT use for" exclusion clause | by-directive | in-scope |
| META-3a | Metadata | — | `quality-patterns.md §META-3a` — directive forbids vague trigger phrases in description | by-directive | in-scope |
| META-3b | Metadata | — | Not enforceable at scaffold time — sibling descriptions are unknown. | runtime-OOS | Rationale: sibling agent context is not available to scaffold; maintainer must run `/validate-primitive-dependencies` post-install to check cross-agent trigger overlap |
| META-3c | Metadata | — | `quality-patterns.md §META-3c` — directive instructs LLM to include ≥1 discriminating domain token in description | by-directive | in-scope |
| META-4 | Metadata | C | `quality-patterns.md §META-4` — directive instructs LLM to write description in third person | by-directive | in-scope |
| SAMP-2 | Metadata | F | `agent-template.md §Frontmatter` — template never includes sampling params; `quality-patterns.md §SAMP-2` directive forbids them | by-template | in-scope |
| CLAR-2 | Clarity | C | `quality-patterns.md §CLAR-2` — directive: resolve all pronouns referring to tool output | by-directive | in-scope |
| CLAR-3 | Clarity | C | `quality-patterns.md §CLAR-3` — directive: every abort/refuse/bail/halt/timeout must name a recovery target | by-directive | in-scope |
| CLAR-4 | Clarity | C | `quality-patterns.md §CLAR-4` — directive: every declared upstream dependency must name a failure branch | by-directive | in-scope |
| WS-2b | Clarity | C | `quality-patterns.md §WS-2b` — directive: "If present/absent" following a block marker must have a preceding prose predicate | by-directive | in-scope |
| WS-5b | Clarity | — | `quality-patterns.md §WS-5b` — directive: NEVER/DO NOT/MUST NOT + verb-list must be followed by ALLOWED/whitelist clause | by-directive | in-scope |
| WS-6 | Clarity | — | `quality-patterns.md §WS-6` — directive: bare comparators must have a numeric/unit anchor within 80 chars | by-directive | in-scope |
| RD-5b | Clarity | C | `quality-patterns.md §RD-5b` — directive: single step-naming scheme OR mapping clause when mixing ≥2 schemes | by-directive | in-scope |
| CE-X | Context Engineering | C | Evaluator marks NA for agents per `rubric_binary_evaluator.py` known-limitations (CE-X targets skill compaction patterns; agents use different context model) | runtime-OOS | Rationale: CE-X checks skill-specific compaction-strategy declaration; agent context patterns are governed by DA-* agent items instead |
| COMP-V | Completeness | — | `quality-patterns.md §COMP-V` — directive: "complete when" must have verifiable component | by-directive | in-scope |
| COMP-W | Completeness | C | `quality-patterns.md §COMP-W` — directive: iterative workflows must declare termination predicate | by-directive | in-scope |
| COMP-X | Completeness | — | `quality-patterns.md §COMP-X` — directive: define explicit success condition | by-directive | in-scope |
| COMP-Y | Completeness | — | `quality-patterns.md §COMP-Y` — directive: programmatic verification method required | by-directive | in-scope |
| COMP-Z | Completeness | — | `quality-patterns.md §COMP-Z` — directive: output spec must include evidence-trail language | by-directive | in-scope |
| AH-2b | Completeness | C | `quality-patterns.md §AH-2b` — directive: $ARGUMENTS reference requires named missing-argument handler | by-directive | in-scope |
| SF-3 | Metadata | — | `quality-patterns.md §SF-3` — agent-specific: directive instructs LLM to include third-person description following Anthropic agent best-practices | by-directive | in-scope |
| SAMP-1 | Prompt Engineering | C | `quality-patterns.md §SAMP-1` — directive forbids temperature/top_p/top_k in body | by-directive | in-scope |
| SP-2b | Safety | C | `quality-patterns.md §SP-2b` — directive: per-tool archetype binding sentence for each allowed-tools entry | by-directive | in-scope |
| SP-4b | Safety | C | `quality-patterns.md §SP-4b` — directive: Tier-A combination requires per-tool scope constraint | by-directive | in-scope |
| IJ-1b | Safety | C | `quality-patterns.md §IJ-1b` — directive: Write/Edit + external-input requires validation + write-gate pair | by-directive | in-scope |
| RL-1b | Safety | C | `quality-patterns.md §RL-1b` — directive: agentic patterns require numeric/enum termination predicate | by-directive | in-scope |
| RL-3b | Safety | C | `quality-patterns.md §RL-3b` — directive: retry/adjust must have numeric cap within 400 chars | by-directive | in-scope |
| RL-4b | Safety | C | `quality-patterns.md §RL-4b` — directive: autonomous/dispatch paths require named HITL or partial-status branch | by-directive | in-scope |
| RL-9b | Safety | C | `quality-patterns.md §RL-9b` — directive: writing external-sourced content requires credential-scope/redaction rule | by-directive | in-scope |

## Agent-Specific Items (§Agent Items, 35)

| Item ID | Dimension | Generator directive (file:section) | Enforcement | Status |
|---|---|---|---|---|
| SF-2 | Clarity | `quality-patterns.md §SF-2` — directive: agent body uses structured, unambiguous step format with no bare vague conditionals | by-directive | in-scope |
| SF-3 | Metadata | `quality-patterns.md §SF-3` — directive: description written in third person per Anthropic agent best-practices | by-directive | in-scope |
| RL-7 | Clarity | `quality-patterns.md §RL-7` — directive: agentic loops have documented loop-exit conditions beyond the COMP-W termination predicate | by-directive | in-scope |
| DA-4 | Completeness | `quality-patterns.md §DA-4` — directive: delegation patterns name the delegated output format and handling procedure for degraded/partial results | by-directive | in-scope |
| TC-1 | Completeness | `quality-patterns.md §TC-1` — directive: tool usage steps include a concrete expected-output description | by-directive | in-scope |
| TC-2 | Completeness | `quality-patterns.md §TC-2` — directive: every tool invocation names the condition under which its output is considered valid | by-directive | in-scope |
| TC-3 | Completeness | `quality-patterns.md §TC-3` — directive: tool failure handling is documented per tool, not only at the global level | by-directive | in-scope |
| RL-2 | Completeness | `quality-patterns.md §RL-2` — directive: document explicit degraded/partial-state handling so the agent can continue with reduced capability | by-directive | in-scope |
| RL-5 | Completeness | `quality-patterns.md §RL-5` — directive: every escalation path names the artifact or state the human reviewer needs | by-directive | in-scope |
| RL-6 | Completeness | `quality-patterns.md §RL-6` — directive: output completeness is verified before reporting success (no silent stub-and-continue) | by-directive | in-scope |
| RL-10 | Completeness | `quality-patterns.md §RL-10` — directive: document the minimum viable output the agent produces if any step fails | by-directive | in-scope |
| RT-4 | Completeness | `quality-patterns.md §RT-4` — directive: resumable tasks document the checkpoint artifact and resume condition | by-directive | in-scope |
| AF-3 | Prompt Engineering | `quality-patterns.md §AF-3` — directive: adversarial inputs (injected content, unexpected tool output shape) are handled with explicit sanitization or rejection | by-directive | in-scope |
| DA-2a | Context Engineering | `quality-patterns.md §DA-2a` — directive: subagent briefs are authored as isolated context (no inline orchestrator prefix leakage) | by-directive | in-scope |
| DA-2b | Context Engineering | `quality-patterns.md §DA-2b` — directive: subagent briefs specify pre-specified decision branches; no mid-task disambiguation required | by-directive | in-scope |
| SF-1 | Context Engineering | `quality-patterns.md §SF-1` — directive: tool set is minimal; each tool is justified by a named use case | by-directive | in-scope |
| RT-5 | Context Engineering | `quality-patterns.md §RT-5` — directive: large state is externalized to files; orchestrator reads on-demand rather than holding in prefix | by-directive | in-scope |
| AF-2 | Context Engineering | `quality-patterns.md §AF-2` — directive: untrusted-data sources (external input, tool output, fetched content) are labeled and treated as data not instructions | by-directive | in-scope |
| TV-2 | Safety | `quality-patterns.md §TV-2` — directive: trust level is explicitly assigned to each data source; lower-trust sources do not inherit higher-trust agent permissions | by-directive | in-scope |
| TV-3 | Safety | `quality-patterns.md §TV-3` — directive: cross-trust-boundary data flows have an explicit sanitization or write-gate step | by-directive | in-scope |
| RL-8 | Safety | `quality-patterns.md §RL-8` — directive: loop/retry logic has a circuit-breaker path that stops silently-degrading iteration | by-directive | in-scope |
| IJ-2 | Safety | `quality-patterns.md §IJ-2` — directive: indirect injection surface (tool output → downstream write) is documented and mitigated | by-directive | in-scope |
| GV-1 | Safety | `quality-patterns.md §GV-1` — directive: destructive or irreversible actions require an explicit confirmation gate | by-directive | in-scope |
| GV-2 | Safety | `quality-patterns.md §GV-2` — directive: sensitive data paths (credentials, PII, secrets) are excluded from Write/Edit scope | by-directive | in-scope |
| AF-1 | Safety | `quality-patterns.md §AF-1` — directive: adversarial inputs that could redirect agent behavior are explicitly handled with reject or sanitize | by-directive | in-scope |
| AF-4 | Safety | `quality-patterns.md §AF-4` — directive: the agent's allowed-tools list is minimal and each tool is justified; Tier-A combinations include blast-radius rationale | by-directive | in-scope |
| AF-5 | Safety | `quality-patterns.md §AF-5` — directive: agent does not propagate untrusted content from one tool output to another without an intermediate validation step | by-directive | in-scope |
| MS-1 | Metadata | `quality-patterns.md §MS-1` — directive: agent description names the subagent-specific model (if non-default) and the activation condition | by-directive | in-scope |
| DA-1 | Metadata | `quality-patterns.md §DA-1` — directive: frontmatter lists tools, model, and permissionMode explicitly | by-template | in-scope |
| DA-5 | Metadata | `quality-patterns.md §DA-5` — directive: hooks frontmatter field is documented when agent uses PreToolUse path guards | by-directive | in-scope |
| TV-1 | Metadata | `quality-patterns.md §TV-1` — directive: trusted vs untrusted data sources are named in the agent description or preamble | by-directive | in-scope |
| TV-4 | Metadata | `quality-patterns.md §TV-4` — directive: agent description names the trust posture (read-only, plan-mode, etc.) | by-directive | in-scope |
| TV-5 | Metadata | `quality-patterns.md §TV-5` — directive: permissionMode frontmatter field is present and matches the agent's write/execute posture | by-template | in-scope |
| TV-6 | Metadata | `quality-patterns.md §TV-6` — directive: agent description does not overstate the permission scope | by-directive | in-scope |
| AF-6 | Metadata | `quality-patterns.md §AF-6` — directive: agent description names the injection-surface risk when the agent reads external content | by-directive | in-scope |
| AF-7 | Metadata | `quality-patterns.md §AF-7` — directive: output contract documents what the agent does NOT emit (e.g., raw secrets, unvalidated external content) | by-directive | in-scope |
