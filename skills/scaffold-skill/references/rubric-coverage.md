---
name: rubric-coverage
description: Maps each binary skill rubric item to a scaffold-skill generator directive or documents why it is runtime-OOS. Source of truth for check_scaffold_quality.py --verify-matrix-complete.
last_refreshed: 2026-05-27
---

# Rubric Coverage Matrix — scaffold-skill

Maps every binary rubric item in `scoring-rubric.md §Item Inventory §Binary-Evaluated Items (skill rubric, 30)` to either a generator directive in this skill's references or an explicit `runtime-OOS` rationale.

`Enforcement` closed set: `by-template | by-AskUserQuestion | by-directive | runtime-OOS`

- `by-template` — scaffold's `skill-template.md` file embeds the requirement at a named slot.
- `by-AskUserQuestion` — scaffold's SKILL.md step 3 collects the value via user-facing prompt.
- `by-directive` — scaffold's `quality-patterns.md` contains an explicit generation directive.
- `runtime-OOS` — runtime-resolved-by-user; NOT scaffold-enforceable. Rationale text mandatory.

| Item ID | Dimension | Cap | Generator directive (file:section) | Enforcement | Status |
|---|---|---|---|---|---|
| META-1a | Metadata | — | `quality-patterns.md §META-1a Trigger-Match-Primary` — directive instructs LLM to embed the body's primary trigger keyword in the description | by-directive | in-scope |
| META-2 | Metadata | C | `quality-patterns.md §META-2 Anti-Pattern Example` — directive instructs LLM to include a "Do NOT use for" exclusion clause | by-directive | in-scope |
| META-3a | Metadata | — | `quality-patterns.md §META-3a Concrete Trigger` — directive forbids "as needed / if appropriate / when useful" in description | by-directive | in-scope |
| META-3b | Metadata | — | Not enforceable at scaffold time — sibling descriptions are unknown. Scaffold cannot prevent cross-skill keyword overlap. | runtime-OOS | Rationale: sibling plugin context is not available to scaffold; maintainer must run `/validate-primitive-dependencies` after installing the scaffolded skill to check overlap |
| META-3c | Metadata | — | `quality-patterns.md §META-3c Discriminating-Keyword-Presence` — directive instructs LLM to include ≥1 domain-specific token not present in generic descriptions | by-directive | in-scope |
| META-4 | Metadata | C | `quality-patterns.md §META-4 Third-Person Description` — directive instructs LLM to write description in third person; bans first-person ("I", "my", "me") and second-person ("you can", "your") | by-directive | in-scope |
| SAMP-2 | Metadata | F | `skill-template.md §Frontmatter` — template slot for frontmatter never includes temperature/top_p/top_k; `quality-patterns.md §SAMP-2` directive forbids sampling params in generated frontmatter | by-template | in-scope |
| CLAR-2 | Clarity | C | `quality-patterns.md §CLAR-2 Resolved-Pronoun` — directive instructs LLM to resolve all pronouns referring to tool output with explicit antecedent in same/preceding step | by-directive | in-scope |
| CLAR-3 | Clarity | C | `quality-patterns.md §CLAR-3 Stop/Recovery` — directive instructs LLM: every abort/refuse/bail/halt/timeout must name a recovery target within 200 chars | by-directive | in-scope |
| CLAR-4 | Clarity | C | `quality-patterns.md §CLAR-4 Step-Dependency-Mitigation` — directive instructs LLM: every declared upstream dependency must name a failure branch | by-directive | in-scope |
| WS-2b | Clarity | C | `quality-patterns.md §WS-2b Conditional-Specificity` — directive instructs LLM: every "If present/absent" following a block marker must have a preceding prose predicate naming the marker | by-directive | in-scope |
| WS-5b | Clarity | — | `quality-patterns.md §WS-5b Negation-Positive-Whitelist` — directive instructs LLM: every NEVER/DO NOT/MUST NOT + verb-list must be followed within 200 chars by an ALLOWED/use-only/whitelist clause | by-directive | in-scope |
| WS-6 | Clarity | — | `quality-patterns.md §WS-6 Quantifier-Range-Anchor` — directive instructs LLM: every bare comparator (more/fewer/older) must have a numeric/unit anchor within 80 chars | by-directive | in-scope |
| RD-5b | Clarity | C | `quality-patterns.md §RD-5b Step-Naming-Consistency` — directive instructs LLM: use a single step-naming scheme OR include a mapping clause when mixing ≥2 schemes | by-directive | in-scope |
| CE-X | Context Engineering | C | `quality-patterns.md §CE-X Compaction-Strategy` — directive instructs LLM: if workflow keeps ≥10 turns of history AND uses LLM summarization, include a sentence justifying why masking is insufficient | by-directive | in-scope |
| COMP-V | Completeness | — | `quality-patterns.md §COMP-V Verifiable-Predicate` — directive instructs LLM: every "complete when" / "success when" / "done when" must contain a numeric threshold, regex marker, exit-code check, schema reference, or tool-output binding | by-directive | in-scope |
| COMP-W | Completeness | C | `quality-patterns.md §COMP-W Termination-Criteria` — directive instructs LLM: iterative skills (for each/retry/iterate/while/until) must declare an explicit termination predicate distinct from COMP-X success | by-directive | in-scope |
| COMP-X | Completeness | — | `quality-patterns.md §COMP-X Success-Criteria` — directive instructs LLM: define explicit success condition (not just output format); for review skills add convergence predicate | by-directive | in-scope |
| COMP-Y | Completeness | — | `quality-patterns.md §COMP-Y Verification-Method` — directive instructs LLM: use programmatic check or explicit binary LLM item; forbid "looks good / seems correct / appears valid" | by-directive | in-scope |
| COMP-Z | Completeness | — | `quality-patterns.md §COMP-Z Evidence-Trail` — directive instructs LLM: output spec must include evidence/citation/quote/verified-against language | by-directive | in-scope |
| AH-2b | Completeness | C | `quality-patterns.md §AH-2b Default-Handling-Pair` — directive instructs LLM: when $ARGUMENTS is referenced, include a named missing-argument handler (fallback value, prompt, or stop-with-error) | by-directive | in-scope |
| SF-3 | Metadata | — | Agent-only item (SF-3 maps to `Metadata` dimension in agent rubric; skill rubric lists it as binary but `rubric_binary_evaluator.py` known-limitations marks it NA for non-agent skills) | runtime-OOS | Rationale: SF-3 checks agent-specific frontmatter fields (description field conventions for agents); skill scaffold does not produce agent files. Item returns NA in evaluator. |
| SAMP-1 | Prompt Engineering | C | `quality-patterns.md §SAMP-1` — directive forbids hardcoded temperature/top_p/top_k in body text | by-directive | in-scope |
| SP-2b | Safety | C | `quality-patterns.md §SP-2b Tool-Archetype-Binding` — directive instructs LLM: each allowed-tools entry must have a per-tool binding sentence near an archetype keyword; read-only archetype gets NA exemption | by-directive | in-scope |
| SP-4b | Safety | C | `quality-patterns.md §SP-4b Tier-A-Constraint-Sentence` — directive instructs LLM: Tier-A tool combinations (Write + Bash/Agent/WebFetch) require a per-tool scope constraint sentence | by-directive | in-scope |
| IJ-1b | Safety | C | `quality-patterns.md §IJ-1b Input-Validation-Pair` — directive instructs LLM: Write/Edit tool + external-input reference requires BOTH a validation predicate AND a write-gate predicate | by-directive | in-scope |
| RL-1b | Safety | C | `quality-patterns.md §RL-1b Termination-Regex` — directive instructs LLM: agentic skills must include a numeric/enum termination predicate | by-directive | in-scope (conditional: applies only when generated skill is agentic) |
| RL-3b | Safety | C | `quality-patterns.md §RL-3b Retry-Ceiling` — directive instructs LLM: every retry/regenerate/adjust must have a numeric cap within 400 chars | by-directive | in-scope (conditional: applies only when generated skill is agentic) |
| RL-4b | Safety | C | `quality-patterns.md §RL-4b Escalation-Trigger` — directive instructs LLM: autonomous/dispatch paths must include a named HITL or partial-status branch | by-directive | in-scope (conditional: applies only when generated skill is agentic) |
| RL-9b | Safety | C | `quality-patterns.md §RL-9b Credential-Scope-Regex` — directive instructs LLM: agentic skills writing external-sourced content must include a credential-scope / redaction rule | by-directive | in-scope (conditional: applies only when generated skill is agentic) |
