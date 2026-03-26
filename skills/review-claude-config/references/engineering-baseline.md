---
name: engineering-baseline
description: Evidence-based prompt, context, and tool design techniques for evaluating Claude Code skills and agents
last_refreshed: 2026-03-24
---

# Engineering Baseline

## Prompt Engineering Techniques

**Structured Output** — Define exact output format (headings, tables, code blocks). Reduces format ambiguity and hallucination. Check: does the item specify what the output looks like?

**Role Priming** — Assign a specific role/persona ("You are a Kubernetes SRE"). Most effective when domain-specific. Check: does it establish behavioral context beyond generic instructions?

**Chain-of-Thought** — Guide multi-step reasoning explicitly ("First check X, then evaluate Y based on the result"). 19-point boost on MMLU-Pro for standard models. Skip explicit CoT for reasoning models — they chain internally. Check: are complex decisions broken into explicit sequential steps?

**Few-Shot Examples** — Provide 2-3 diverse, canonical examples showing expected behavior. Avoid laundry lists of edge cases. Check: are examples present where output format or decision logic is non-obvious?

**Constraint Specification** — State what NOT to do and define boundaries. Check: are negative constraints and scope limits explicit?

**Output Format Templates** — Literal templates with placeholders the model fills in. Check: is there a template or just a description of the output?

**Degrees of Freedom** — Match instruction specificity to task fragility: low freedom (exact scripts) for fragile/error-prone operations, high freedom (text guidance) when multiple approaches are valid (Anthropic). Check: does the specificity level match the task's risk?

**Verification Criteria** — Include tests, validators, or expected outputs so the agent can self-check. "Dramatically better" performance when agents verify their own work (Anthropic). Check: can the agent confirm its output is correct without human review?

**Feedback Loops** — Run validator → fix errors → repeat for quality-critical outputs. Catches errors early and enables iterative improvement without human intervention (Anthropic). Check: do quality-critical steps include a validate-fix cycle?

**Evidence-First Critique** — In review tasks, prefer recommendations grounded in explicit quotes, paths, or line references rather than generic quality judgments. Check: would another reviewer be able to verify the claim from the artifact alone?

## Context Engineering Techniques

**Context Budget** — A focused 300-token context often outperforms 113K unfocused (Anthropic). Only add context the model doesn't already have — challenge each piece: "Does it justify its token cost?" (Anthropic 2026). Minimize tokens, maximize signal. Check: is information density high? Could the item achieve the same with fewer tokens?

**Just-in-Time Retrieval** — Maintain lightweight identifiers (file paths, queries), load data on demand rather than pre-loading. Check: does the item load all context upfront or progressively?

**Subagent Isolation** — Delegate focused subtasks to subagents with clean context windows. Return condensed summaries (1-2K tokens). Check: are complex tasks decomposed into isolated subtasks?

**Reference File Separation** — Offload stable knowledge (rubrics, checklists, domain guides) to `references/` files loaded only when needed. Keep main file under 500 lines, references one level deep, ToC for files >100 lines (Anthropic 2026). Check: is large stable content embedded inline or separated?

**Tool Set Curation** — Minimal, unambiguous tools. "If a human can't say which tool to use, the agent can't either" (Anthropic). Check: could any tools be removed without losing capability? Do any tools overlap?

**Output Conciseness** — Structured, concise outputs prevent downstream context bloat. Check: does the output format avoid unnecessary verbosity?

**Activation Precision** — Descriptions should make it obvious when a skill or agent should trigger and when it should not. Check: would this wording accidentally activate on unrelated user requests?

**Error Preservation** — Keep failed attempts in context for self-correction rather than hiding them (Manus/Meta). Check: does the item acknowledge and learn from errors?

**KV-Cache Friendliness** — Stable prefixes, append-only patterns. Single-token prefix differences invalidate cache (10x cost difference). Check: for multi-agent dispatch, are shared prefixes byte-identical?

## Tool Design Techniques

**Descriptions as Onboarding** — Write tool descriptions as if explaining to a new team member. Make implicit context explicit. "Small refinements yield dramatic improvements" (Anthropic). Check: would someone unfamiliar understand when and how to use each tool?

**High-Signal Returns** — Tools should return only relevant information using pagination, filtering, truncation. Check: could tool outputs overwhelm the context with irrelevant data?

**Consolidation** — Combine related operations into fewer tools rather than proliferating. Check: are there tools that could be merged without ambiguity?

**Meaningful Identifiers** — Semantic names over cryptic IDs reduce hallucination. Check: are parameter names and identifiers self-describing?

**Actionable Errors** — Error messages should suggest specific fixes, not return opaque codes. Check: do error paths guide the agent toward resolution?

**Avoid Time-Sensitive Guidance** — Stable prompt assets should avoid phrases like "today", "latest", or "current year" unless the task is explicitly time-bound. Check: will the instruction still make sense months later?

## Sources
- Anthropic: "Effective context engineering for AI agents"
- Anthropic: "Writing tools for agents"
- Anthropic: "Equipping agents with agent skills"
- Anthropic: "Skill authoring best practices" (2026) — https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Anthropic: "Best practices for Claude Code" (2026) — https://code.claude.com/docs/en/best-practices
- Fowler: "Context Engineering for Coding Agents" — https://martinfowler.com/articles/exploring-gen-ai/context-engineering-coding-agents.html
- Manus/Meta: "Context Engineering for AI Agents"
- Chroma Research: "Context Rot"
- Schulhoff et al.: "The Prompt Report" (2024) — https://arxiv.org/abs/2406.06608
