---
name: peer-reference-anti-pattern
description: Why Claude Code subagent files (agents/*.md) must not name peer agents in their prose body — dispatcher reads only the YAML description field; body-text peer references are dead documentation that creates O(N²) coupling
last_refreshed: 2026-05-06
---

# Peer-Reference Anti-Pattern in Claude Code Subagents

## Definition

A Claude Code subagent file (`agents/<x>.md`) carries an authoring decision: the prose body either describes only the agent's own job, or it also names other agents (typically in "hand-off", "next steps", "recommended review chain" blocks). The second pattern looks like coordination, but in this dispatcher model it is mechanically inert: the routing layer never reads it. This document is the evidence base for why the second pattern must be flagged when it appears in a reviewed plugin and avoided when scaffolding a new one.

## Tier-1 Evidence

### Anthropic spec — dispatcher reads `description:` only

- **Source:** [Claude Code — Sub-Agents](https://code.claude.com/docs/en/sub-agents) (canonical URL after redirect from `docs.claude.com/en/docs/claude-code/sub-agents`).
- **Verbatim:** *"Claude uses each subagent's description to decide when to delegate tasks. When you create a subagent, write a clear description so Claude knows when to use it."*
- **Verbatim:** *"This prevents infinite nesting (subagents cannot spawn other subagents) while still gathering necessary context."*
- **Verbatim:** *"Subagents cannot spawn other subagents, so `Agent(agent_type)` has no effect in subagent definitions."*
- **Implication:** Body content is loaded only after dispatch, into the subagent's private context. The page contains no field, no example, and no recommendation for one subagent file to reference another by name in its body. Allow-listing exists only on the parent/coordinator side via `tools: [Agent(worker)]`.

### Anthropic Engineering — multi-agent research system

- **Source:** [How we built our multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system).
- **Operational confirmation:** the lead agent decomposes queries dynamically and describes them to subagents; subagents have separation of concerns ("distinct tools, prompts, and exploration trajectories") and do not coordinate peer-to-peer; results return to the lead for synthesis. No subagent references another by name.

## Tier-1 Evidence — research literature on agent coupling at scale

| Paper | Finding | URL |
|---|---|---|
| arXiv 2511.02200 — Optimal-Agent-Selection | Capability is a property *of* the agent (a vector); routing is performed *by* the supervisor. Workers do not enumerate peers. | https://arxiv.org/abs/2511.02200 |
| arXiv 2510.01285 — LLM-Based Multi-Agent Blackboard System | Motivates the blackboard pattern explicitly to avoid O(N²) coupling: agents post to / read from a shared workspace; no agent names another. | https://arxiv.org/abs/2510.01285 |
| arXiv 2512.08296 — Towards a Science of Scaling Agent Systems | Quantitative scaling laws; coordination cost is named as a first-class scaling factor. | https://arxiv.org/abs/2512.08296 |
| arXiv 2512.00614 — Hierarchical Decentralized Coordination | "Cluster-based hierarchies… enabling efficient task routing while maintaining full decentralization." Routing emerges from capability metadata, not hardcoded peer lists. | https://arxiv.org/abs/2512.00614 |

## Tier-2 Evidence — cross-framework consensus

All five mature multi-agent frameworks externalise routing. When peer references exist they live in *structured fields* (graph edges, `handoffs=[]` lists, `Agent()` allowlists), never in worker prose.

| Framework | Where peer references live | URL |
|---|---|---|
| LangGraph Supervisor | Centralised. Supervisor node holds the routing LLM call; conditional edges (graph build time) carry hand-offs. Workers unaware of peers. | https://reference.langchain.com/python/langgraph-supervisor |
| LangGraph Swarm | Decentralised via tool-calling. Workers expose `transfer_to_X` *tools*; targets in graph topology, not prose. | https://docs.langchain.com/oss/python/langgraph/workflows-agents |
| CrewAI Hierarchical | Centralised in a `manager_agent`; workers do not name each other. | https://docs.crewai.com/en/learn/hierarchical-process |
| AutoGen GroupChat | Centralised via `GroupChatManager` LLM speaker-selection from a registered list. | https://microsoft.github.io/autogen/0.2/docs/notebooks/agentchat_groupchat_customized/ |
| AutoGen Swarm | Decentralised via `HandoffMessage`; targets declared on the agent's structured `handoffs=[…]` config field. | https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html |

## Why this matters quantitatively — the N×N argument

1. **Mechanical inertness.** The dispatcher does not parse worker bodies, so peer names there are not a routing mechanism. They are documentation that goes stale on every rename or addition. Definition of dead text in the routing path.
2. **Coupling growth.** With *N* agents, body-cross-references form an *N×(N-1)* possibility space. Empirical anchor (2026-05-06 audit of a separate user-owned config): at N=5, three agents already carried 1-3 peer references each — symmetric pairs (`python-staff-engineer ↔ postgres-expert`) plus a `reviewer → team-red` reference. At N=20 the worst-case pair count is 380.
3. **Framework consensus.** Five independent mature frameworks externalise routing; none place peer names into worker prose.
4. **Research convergence.** arXiv 2511.02200 / 2510.01285 explicitly propose capability vectors and blackboards specifically to *avoid* O(N²) coupling at scale.

The conclusion is not "naming peers in prose feels untidy"; it is that body-text peer references are mechanically dead text in a system whose dispatcher reads only `description:`.

## Distinguishing legitimate skill-side references from the agent-side anti-pattern

The asymmetry is deliberate and load-bearing for review heuristics:

- **Agents are workers.** Their body should describe only what the agent does, what it must verify before yielding, and its boundaries. Peer agent names in the body trigger an A1 violation.
- **Skills are orchestrators.** Their body *may* name agents because that is exactly their purpose: to choreograph dispatch. `code.claude.com/docs/en/skills` defines skills as user- or model-invocable workflows; the skill is the right altitude for `Agent(subagent_type="…")` calls and for "first dispatch X, then Y" sequencing.
- **Lexical false positives.** A grep for an agent name inside a skill body can match three semantically distinct uses: (a) genuine workflow dispatch (legitimate, e.g. `Agent(subagent_type="review-perspective-clarity", …)` in `skills/review-skill/SKILL.md`); (b) the word "reviewer" denoting a *human role* (legitimate, e.g. "the per-finding diff lists give the reviewer a precise picture"); (c) demo content in a scaffold template (legitimate, e.g. `name: pr-reviewer` inside an example frontmatter). Reviewers must inspect the surrounding 2-3 lines before flagging.

## Implication for plugin-skill artifacts

When reviewing a Claude Code plugin (this repo's primary use case):

1. **Agent files (`agents/*.md`):** the body must not contain peer agent file names or "Recommended next agent" prose. Hand-off blocks may emit *agent-name-free* signals (e.g. `SQL surface: YES with files`, `Stakes flags: YES with files`) that the parent uses to route — these are equivalent to the capability-vector idea (arXiv 2511.02200).
2. **Skill files (`skills/<x>/SKILL.md`):** named agent dispatch is allowed *and expected*. Distinguish workflow dispatch from incidental lexical hits before flagging.
3. **Routing rules:** when chaining `agent A → agent B` is a real workflow, encode it in a skill or in a path-scoped rule, never in either agent's body. The reviewed `rules/review.md` pattern in user-global Claude Code configs is the canonical shape: explicit "neither agent calls the other" with the routing handled by a path-scoped rule.

## Persistence layers for the meta-rule (informational)

For a Claude Code config wanting to prevent the anti-pattern from recurring across sessions and hosts, four persistence layers were validated empirically (2026-05-06):

| Layer | Mechanism | When loaded | Cross-host |
|---|---|---|---|
| L1 | `~/.claude/rules/agent-antipatterns.md` with `paths:` frontmatter | Only when working tree contains a matching file | Yes (via `~/.claude/` rsync) |
| L2 | `~/.claude/references/<topic>.md` | On-demand read by skills/agents | Yes |
| L3 | `~/.claude/projects/<proj>/memory/feedback_*.md` + index in `MEMORY.md` | First 200 lines of MEMORY.md at session start | **No** — machine-local per Anthropic spec ([code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory)) |
| L4 | KB-server `kb_create_source` + `kb_create_claim`, cross-linked | On `kb_search` | Yes (centralised KB) |

L1 is the lightest sufficient form for *behavioural* guardrails that must influence authoring decisions: zero token cost outside the trigger window, full re-injection inside it.

## Open / unverified items

- Anthropic has not published an explicit *anti-pattern callout* against peer references in subagent bodies. The spec is silent (no recommendation either way). The anti-pattern designation rests on (a) the dispatcher mechanism, (b) the cross-framework consensus, (c) the arXiv decoupling evidence — not on a direct quote forbidding the practice.
- Specific token-overhead numbers for hierarchical coordination (one Tier-3 source claims 30-50 % CrewAI overhead) — not cross-validated.

## Sources for this section

Tier 1:
- [Claude Code — Sub-Agents](https://code.claude.com/docs/en/sub-agents)
- [Anthropic — How we built our multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system)
- [Claude Code — Memory](https://code.claude.com/docs/en/memory)
- [arXiv 2511.02200 — Optimal-Agent-Selection](https://arxiv.org/abs/2511.02200)
- [arXiv 2510.01285 — LLM-Based Multi-Agent Blackboard System](https://arxiv.org/abs/2510.01285)
- [arXiv 2512.08296 — Towards a Science of Scaling Agent Systems](https://arxiv.org/abs/2512.08296)
- [arXiv 2512.00614 — Hierarchical Decentralized Coordination](https://arxiv.org/abs/2512.00614)

Tier 2:
- [LangGraph Supervisor reference](https://reference.langchain.com/python/langgraph-supervisor)
- [LangGraph workflows-and-agents docs](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [CrewAI Hierarchical Process docs](https://docs.crewai.com/en/learn/hierarchical-process)
- [AutoGen Swarm docs](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html)
- [AutoGen GroupChat docs](https://microsoft.github.io/autogen/0.2/docs/notebooks/agentchat_groupchat_customized/)
