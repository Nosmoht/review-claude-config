# Prompt Engineering Techniques: Evidence-Based Summary

**Sources:**
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (few-shot, system prompt guidance)
- [Anthropic: Equipping agents with agent skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) (progressive layering, evaluation-first)
- [arXiv 2505.17037: Prompt Engineering: How Prompt Vocabulary affects Domain Knowledge](https://arxiv.org/abs/2505.17037) (specificity sweet spot)
- [Comprehensive taxonomy of prompt engineering techniques](https://jamesthez.github.io/files/liu-fcs26.pdf) (technique categorization)

**Fetched:** 2026-03-24

## Relationship to Context Engineering

Prompt engineering is a subset of context engineering. It focuses on the textual instructions given to an LLM, while context engineering manages the entire information architecture. Both are important; prompt engineering matters for instruction quality, context engineering for information flow.

## Core Techniques

### Structured Output Specification
Define exact output format (headings, tables, code blocks, JSON schemas). Reduces format ambiguity and hallucination in structured outputs.
- **Evidence:** Consistently improves output quality across benchmarks
- **When to use:** Always when a specific output format is expected

### Role Priming
Assign a specific role or persona ("You are a senior Kubernetes SRE"). Most effective when domain-specific rather than generic.
- **Evidence:** Establishes behavioral context, improves domain-appropriate responses
- **When to use:** When domain expertise matters for the task

### Chain-of-Thought (CoT)
Guide the model through explicit sequential reasoning steps rather than asking for a direct answer.
- **Evidence:** Improves reasoning for multi-step tasks significantly
- **When to use:** Complex decisions, multi-step analysis, debugging workflows

### Few-Shot Examples
Provide 2-3 diverse, canonical examples showing expected behavior. Quality over quantity — "laundry lists of edge cases" hurt more than they help (Anthropic).
- **Evidence:** Most effective for format-sensitive outputs and non-obvious decision logic
- **When to use:** When output format or decision criteria are non-obvious

### Constraint Specification
Explicitly state what NOT to do, define scope boundaries, and set limitations.
- **Evidence:** Explicit constraints reduce unwanted behaviors more reliably than relying on implicit understanding
- **When to use:** When the model might over-generate, go out of scope, or take unwanted actions

### Output Format Templates
Provide literal templates with placeholders the model fills in. More precise than describing the format in prose.
- **Evidence:** Reduces hallucination in structured outputs compared to prose descriptions
- **When to use:** Reports, certificates, structured documents

### Error Handling Patterns
Define what to do when things go wrong — not just the happy path.
- **Evidence:** Engineering best practice for robustness
- **When to use:** Any skill/agent that interacts with external systems or uncertain inputs

### Stop Conditions
Define when the model should stop, ask for help, or escalate.
- **Evidence:** Prevents runaway behavior and token waste
- **When to use:** Long-running tasks, tasks with destructive potential

## Meta-Observations

- There is a **specificity sweet spot** — overly generic and overly specific prompts both underperform moderate specificity (arXiv 2505.17037)
- **Smarter models require less prescriptive engineering** — as models improve, heavy scaffolding can hurt more than help (Anthropic)
- **"Do the simplest thing that works"** (Anthropic) — avoid over-engineering prompts
