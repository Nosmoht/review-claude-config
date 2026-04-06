# Research Backlog: Review Suite Quality Gaps

Identified 2026-04-02 after applying review-claude-config findings to aegis-runtime (62 primitives, 49 stubs filled across P0-P1 work). These are gaps where the review suite lacks research-backed criteria and had to fall back on first-principles reasoning during real remediation work.

Each item includes: the gap, why it matters (observed failure mode), what to research, and where findings land in the suite.

## Status

| # | Topic | Status | Research file | Rubric/baseline impact |
|---|-------|--------|---------------|----------------------|
| 1 | Autonomous agent reliability | DONE | `research/autonomous-agent-reliability/` | Safety, Completeness |
| 2 | Multi-primitive dependency integrity | TODO | `research/multi-primitive-dependencies/` | Completeness, audit-repo |
| 3 | Instruction following under rule load | TODO | `research/instruction-following-at-scale/` | Rule-specific scoring |
| 4 | Least-privilege tool grants | TODO | `research/agent-tool-least-privilege/` | Safety dimension |
| 5 | Low-evidence baseline refresh | PARTIAL | (updates existing research files) | Baseline evidence classes |
| 6 | Agent definition quality benchmarks | DONE | `research/agent-definition-quality/` | Agent checklist (+3 items), baseline (2 updates), review-agent SKILL.md |

---

## 1. Autonomous agent reliability patterns

**Gap:** The rubric checks structural quality (has steps, output format, constraints) but cannot assess whether a primitive will work unsupervised in a multi-step chain. No baseline techniques for: circuit breakers, failure cascades, MCP/tool failure fallbacks, session caps, `[INCOMPLETE]` failure paths, idempotency, split-cascade guards.

**Observed failure mode:** aegis-runtime's autopilot chain (`bootstrap-runtime-autopilot` → `run-program-phase` → `derive-backlog` → 5 skills) silently no-oped through stub skills. The review correctly graded stubs F but couldn't assess whether *filled* skills were operationally sound for autonomous execution. Patterns like "if MCP tool call fails, treat as `[INCOMPLETE]`, do not retry" and "do not re-split already-split tasks" had to be added through plan review subagent findings, not rubric criteria.

**Research targets:**
- Academic: agent reliability frameworks, failure mode taxonomies for LLM agents, autonomous agent safety benchmarks
- Industry: Anthropic's building effective agents (already referenced — check for reliability-specific guidance), OpenAI agent safety research, LangChain/LangGraph failure handling patterns
- Standards: emerging AI agent safety standards (NIST AI 600-1, ISO/IEC 42001 agent-specific sections)

**Where findings land:**
- New baseline techniques under Context Engineering or new "Reliability" subsection: failure fallback, circuit breaker, idempotency check, session cap
- Rubric Safety dimension: new A-criteria for "failure path defined for every external dependency" and "stop condition prevents infinite recursion"
- Rubric Completeness dimension: new criteria for "chain-level completeness" (does this primitive handle the case where its upstream or downstream dependency fails?)

---

## 2. Multi-primitive dependency integrity

**Gap:** The rubric evaluates primitives in isolation. A skill can score B individually while being part of a broken execution chain. No systematic detection of: orphaned references (skill calls a stub/nonexistent agent), circular dependencies, tool grant mismatches (skill delegates to agent that lacks required tools), `[INCOMPLETE]` state propagation across chains, dead-letter paths (skill writes output that nothing reads).

**Observed failure mode:** aegis-runtime had `enrich-with-public-research` calling `regulatory-researcher` (a stub agent with kitchen-sink tools). The audit flagged stubs but didn't map the dependency graph to show which *filled* skills were broken by *stub* dependencies. The 19-agent tool restriction required manual per-agent reasoning because no framework linked caller tool needs to callee tool grants.

**Research targets:**
- Academic: dependency analysis in multi-agent systems, call graph analysis for LLM orchestration
- Industry: LangGraph/CrewAI dependency management, Anthropic tool-use orchestration patterns
- Adjacent: microservice dependency analysis (service mesh observability) as analogy for agent mesh

**Where findings land:**
- New audit-repo check: "dependency integrity" — map skill→agent, skill→skill, skill→rule references and flag broken links
- Rubric Completeness: sub-criterion for "all referenced primitives exist and are non-stub"
- Rubric Context Engineering: sub-criterion for "callee tool grants are sufficient for delegated work"
- Possibly a new reference file: `references/dependency-integrity-checklist.md`

---

## 3. Instruction following under rule load

**Gap:** aegis-runtime loads 22+ rules into every session. The AGENTIF paper (already in baseline sources) benchmarks instruction following but not specifically rule-count scaling. No guidance on: how many rules an LLM can reliably follow simultaneously, when rules start conflicting or getting silently ignored, when to consolidate vs keep separate, optimal rule granularity.

**Observed failure mode:** Not a direct failure — but aegis-runtime's rule numbering scheme (00-70 with sub-rules) was designed for organization, not for LLM compliance. Rules 40-43 each add 6-7 bullets. At some point, adding more rules has diminishing or negative returns. The rule-specific scoring (Clarity 30%, Completeness 30%, Goal Alignment 40%) doesn't account for rule-set-level effects.

**Research targets:**
- Academic: AGENTIF (already cited — mine for rule-count findings), instruction following degradation studies, "lost in the middle" for instructions (not just retrieval), constraint satisfaction under load
- Industry: Claude system prompt best practices (official docs), real-world rule-set sizes in production agent systems
- Experimental: if no literature exists, note as a gap worth benchmarking

**Where findings land:**
- Rule-specific scoring: add guidance on when rule count signals a problem (e.g., "if >N rules share a theme, consider consolidation")
- Baseline: Constraint Load upgraded from `[Low-evidence area]` to `[Engineering guidance]` (2026-04-03) based on Anthropic's effective context engineering guidance and three tier 1 papers (ScaledIF arXiv:2510.14842, Prospective Memory arXiv:2603.23530, IF Reliability arXiv:2512.14754)
- Review recommendations: when reviewing a rule set (review-claude-config batch mode), flag rule count and overlap

---

## 4. Least-privilege tool grants for LLM agents

**Gap:** The rubric states kitchen-sink=F (Context Engineering) and least-privilege=A (Safety), but provides no criteria for what tool set fits what agent role. Restricting 19 aegis-runtime agents required per-agent reasoning: "this agent only reads and writes files, never runs commands" → remove Bash. "This agent annotates metadata on existing files" → keep Edit, remove Write. No decision framework existed.

**Observed failure mode:** All 19 agents had `Read, Grep, Glob, LS, Edit, Write, Bash` regardless of role. The review flagged "kitchen-sink" but the fix required classifying agents into archetypes (read-only researcher, file writer, file editor, orchestrator with MCP tools) and deriving minimum tool sets per archetype.

**Research targets:**
- Academic: least-privilege in AI agent systems, tool selection and confusion in LLM agents, security implications of tool breadth
- Industry: Anthropic tool-use documentation (tool filtering, tool selection behavior), MCP security model, Claude Code agent tool grants in practice
- Adjacent: RBAC/ABAC models applied to agent tool grants

**Where findings land:**
- New reference file: `references/tool-grant-decision-tree.md` — given agent role (researcher, writer, editor, orchestrator), recommended minimum tool set
- Baseline: upgrade Tool Set Curation from `[Engineering guidance]` to `[Proven result]` if evidence supports, add agent-archetype-to-tool mapping
- Rubric Safety: concrete criteria beyond "least-privilege" — e.g., "Bash requires justification in agent description", "Write-only agents should not have Edit"

---

## 5. Low-evidence baseline refresh

**Gap:** Two baseline techniques remain marked `[Low-evidence area]`: Dynamic Tool Loadout, Context Compression. Constraint Load was upgraded to `[Engineering guidance]` on 2026-04-03. These are used in review recommendations but acknowledged as weakly grounded.

**Observed relevance:** Context Compression and Constraint Load both applied during aegis-runtime work (rule 70 defines compaction triggers; rules 40-43 each carry ~7 constraints per rule). Dynamic Tool Loadout is relevant to topic 4 above.

**Research targets:**
- Context Compression: summarization strategies for long agent sessions, KV-cache optimization, Manus context engineering lessons (already in research/)
- Dynamic Tool Loadout: tool filtering benchmarks, effect of tool count on selection accuracy
- Constraint Load: DONE — upgraded to `[Engineering guidance]` (see status table)

**Where findings land:**
- Baseline: upgrade evidence class if research supports, or add specific caveats/thresholds
- This is incremental — do after topics 1-4

---

---

## 6. Agent definition quality benchmarks

**Gap:** The repo evaluates agent definitions using a 14-item structural checklist but no research basis existed for whether these checks predict actual agent quality. No academic benchmark evaluates agent definition quality at design time.

**Observed failure mode:** Not from aegis-runtime work. Identified 2026-04-06 during dedicated research into quality benchmarks for agent definitions — a proactive gap-filling exercise rather than a reactive remediation.

**Research targets explored:**
- KDD 2025 survey (arXiv:2507.21504) — confirmed no design-time benchmark exists
- ICLR 2026 Workshop (arXiv:2604.00594) — IRT decomposition separating definition quality from runtime quality
- arXiv:2602.16666 — prompt robustness and heterogeneous failure profiles
- Adjacent fields: requirements engineering quality (IEEE 830, ISO/IEC/IEEE 29148) — relevant conceptually but not adapted to LLM agents

**Where findings landed:**
- New research file: `research/agent-definition-quality/agent-definition-quality-benchmarks.md`
- Agent evaluation guide: +3 items (TC-3 verification criteria, DA-5 description-body consistency, AP-4 language calibration)
- Engineering baseline: 2 inline updates (Activation Precision, Constraint Load)
- Review-agent SKILL.md: definition-runtime separation reviewer guidance
- Eval cases: Case 7 for new item discrimination testing

---

## How to work through this backlog

For each topic:
1. `/refresh-engineering-baseline` covers the web research and baseline update workflow
2. Create `research/{topic-slug}/{topic-slug}.md` following existing research file conventions (sources, evidence tiers, key findings)
3. Update `scoring-rubric.md` and/or `engineering-baseline.md` with new criteria/techniques
4. Run `/review-eval-cases` against the eval cases to check for regressions
5. Mark status as DONE in the table above

Topics 1-4 are independent and can be tackled in any order. Topic 5 is incremental and should come last. Topic 1 has the highest impact on review quality for autonomous agent systems.
