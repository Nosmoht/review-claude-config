---
domain: context-engineering
last_refreshed: 2026-04-02
queries:
  - "agentic context engineering LLM 2025 academic"
  - "context window optimization AI agents KV cache 2025"
  - "ACE agentic context engineering playbook 2025"
sources:
  - url: https://arxiv.org/abs/2510.04618
    title: "ACE: Agentic Context Engineering — arXiv 2510.04618"
  - url: https://arxiv.org/abs/2507.13334
    title: "A Survey of Context Engineering for Large Language Models — arXiv 2507.13334"
  - url: https://manus.im/blog/context-engineering-for-agents
    title: "Context Engineering for AI Agents: Lessons from Building Manus"
---

# Context Engineering — Domain Best Practices

## ACE: Agentic Context Engineering (arXiv 2510.04618)
- ACE framework achieves +10.6% improvement on agent task benchmarks via evolving playbooks that encode past task solutions
- Context budgets must be explicit: agents operating without defined token limits degrade toward context rot in multi-step tasks
- Stop conditions and confirmation gates are first-class context controls, not optional safety layers
- Playbooks (persistent, structured task solutions) outperform blank-slate prompting on complex agent workflows

## Survey of Context Engineering (arXiv 2507.13334)
- Context engineering is a formal discipline: covers 1400+ papers, distinct from prompt engineering
- Key components: context selection, context compression, context retrieval, context formatting
- JIT (just-in-time) retrieval outperforms full-context injection by preserving token budget for task-relevant data
- Subagent isolation (separate context windows per agent) prevents cross-task context contamination
- Tool curation reduces decision overhead: each extra available tool increases instruction-following failure rate
- Activation precision: inject context only when the agent needs it, not at session start

## Manus Production Lessons
- KV-cache optimization via byte-identical shared prefixes enables parallel agent batches without redundant computation
- Error preservation (keeping failure traces in context) improves recovery: agents that see prior failures recover 37% faster
- Context rot is the primary cause of multi-step agent failure in production deployments
- Minimal tool surface per agent role is a production requirement, not a theoretical preference
