---
name: engineering-baseline
description: Evidence-based prompt, context, and tool design techniques for evaluating Claude Code skills and agents
last_refreshed: 2026-04-03
---

# Engineering Baseline

## Prompt Engineering Techniques

**Structured Output** `[Proven result]` — Define exact output structure when the task depends on reliable formatting. Check: is the expected output shape explicit?

**Role Priming** `[Engineering guidance]` — Use a role or operating stance when domain context materially changes judgment or vocabulary. Check: does the role add real behavioral context rather than decoration? Most effective when domain-specific; generic personas show no factual accuracy improvement (Zheng et al., EMNLP 2024 Findings, ACL Anthology 2024.findings-emnlp.888).

**Stepwise Decision Flow** `[Engineering guidance]` — Break fragile reasoning into explicit ordered steps for analysis, validation, or branching work. Check: are complex decisions sequenced instead of left implicit?

**Few-Shot Examples** `[Engineering guidance]` — Add a small number of canonical examples when output or trigger logic is easy to misread. Check: are examples present where behavior would otherwise be ambiguous?

**Constraint Specification** `[Proven result]` — State prohibitions, boundaries, and success conditions explicitly. Check: are negative constraints and scope limits visible?

**Verification Criteria** `[Engineering guidance]` — Tell the agent how to confirm correctness using checks, validators, or expected outcomes. Check: can the agent verify the output without relying only on intuition?

**Feedback Loops** `[Engineering guidance]` — For quality-critical work, use a validate-fix-repeat pattern instead of a single-pass instruction. Check: does the workflow include a correction loop where failure is likely?

**Evidence-First Critique** `[Engineering guidance]` — In review tasks, ground findings in quotes, paths, or specific examples rather than generic quality language. Check: could another reviewer verify the claim from the artifact?

**Constraint Load** `[Engineering guidance]` — When a step carries many simultaneous constraints, split it into smaller steps. Check: would breaking the step reduce ambiguity or hidden tradeoffs? Anthropic recommends task decomposition to manage constraint scope (Effective Context Engineering for AI Agents). Degradation under constraint load demonstrated by ScaledIF (arXiv:2510.14842), Prospective Memory Failures (arXiv:2603.23530), and IF Reliability (arXiv:2512.14754).

**Deterministic Conditionals** `[Proven result]` — Write branch conditions as observable tests, not vague phrases like "if needed" or "as appropriate". Check: would two models take the same branch from the same input?

## Context Engineering Techniques

**Context Budget** `[Proven result]` — Focused, relevant context usually beats large but noisy context. Check: is each piece of context earning its token cost?

**Just-in-Time Retrieval** `[Engineering guidance]` — Keep references lightweight and load deeper material only when the task actually needs it. Check: does the item retrieve context progressively instead of front-loading everything?

**Subagent Isolation** `[Engineering guidance]` — Use subagents or isolated workers for bounded subtasks so each sees only the context it needs. Check: are large tasks decomposed into focused units?

**Reference File Separation** `[Engineering guidance]` — Move stable knowledge into `references/` files and keep the main instruction surface concise. Check: is reusable background knowledge separated from the workflow?

**Tool Set Curation** `[Engineering guidance]` — Give agents the smallest tool set that still lets them complete the task. Check: could any tool be removed without reducing required capability?

**Activation Precision** `[Engineering guidance]` — Describe clearly when a skill or agent should trigger and when it should not. Check: would unrelated requests accidentally match this wording?

**Error Preservation** `[Engineering guidance]` — Preserve failed attempts or error traces when they help the system avoid repeating the same mistake. Check: does the workflow retain useful failure context for correction?

**KV-Cache Friendliness** `[Engineering guidance]` — Keep shared prefixes and repeated orchestration blocks stable when dispatching similar work. Check: are repeated agent prompts and tool sets stable enough to benefit from reuse?

**Confirmation Gates** `[Engineering guidance]` — Require explicit user confirmation before destructive or irreversible actions. Check: can the item modify or delete important data without approval?

**Stop Conditions** `[Engineering guidance]` — Define clear termination criteria for retries, loops, and recursive work. Check: could the workflow continue indefinitely without a stopping rule?

**Retry Ceilings** `[Repo default]` — When a task includes retries, keep the retry budget small and explicit so failures escalate instead of looping invisibly. Check: is there a concrete retry limit?

**Idempotency Design** `[Proven result]` — Make tool operations produce the same result when executed multiple times, enabling safe retries. Check: can every tool call that creates, modifies, or deletes be safely retried? LLM agents retry 15-30% of tool calls due to timeouts or validation errors (Fast.io, Google Cloud Vertex AI, Inngest).

**Circuit Breaker Pattern** `[Engineering guidance]` — Track failures in a sliding window and temporarily halt requests when thresholds are exceeded to prevent cascade failures. Check: does the workflow stop calling a failing service after repeated failures? AWS, Microsoft, and academic research recommend circuit breakers as standard architectural components (AWS Prescriptive Guidance; arXiv:2512.16856; arXiv:2512.09458).

**Progressive Fallback** `[Engineering guidance]` — When operations fail, degrade through self-correction, fallback strategies, and escalation rather than immediate failure. Check: does the workflow have multiple recovery paths instead of binary success/failure? Fast.io and Maxim.ai recommend layered error handling for production agents.

**Knowledge Gap Detection** `[Engineering guidance]` — Teach the system to escalate, retrieve more context, or admit uncertainty when required knowledge is missing. Check: does the workflow prevent confident guessing when information is insufficient?

**Dynamic Tool Loadout** `[Low-evidence area]` — Pre-filter available tools when a large shared catalog creates selection ambiguity, but treat exact numeric cutoffs as heuristic unless benchmarked for the target environment. Check: does the agent see only the tools relevant to the current task?

**Context Compression** `[Low-evidence area]` — For long-running work, summarize older context while preserving key decisions and failures, but treat exact compression thresholds as heuristic. Check: is there a strategy for long histories beyond simply keeping everything?

## Tool Design Techniques

**Descriptions as Onboarding** `[Engineering guidance]` — Write tool descriptions as if explaining usage to a new teammate. Check: would an unfamiliar engineer understand when and why to use the tool?

**High-Signal Returns** `[Engineering guidance]` — Return only the information needed for the next decision, using filtering or truncation where appropriate. Check: could the tool overwhelm the context with irrelevant output?

**Meaningful Identifiers** `[Engineering guidance]` — Prefer semantic names and explicit parameters over cryptic IDs or overloaded free text. Check: are identifiers self-describing at the call site?

**Actionable Errors** `[Engineering guidance]` — Make tool errors suggest the next fix instead of returning opaque failure states. Check: would the error help the agent recover?

**Avoid Time-Sensitive Guidance** `[Engineering guidance]` — Keep stable prompt assets free of time-bound wording unless the task is explicitly time-sensitive. Check: will the guidance still make sense months later?

**Poka-Yoke Tool Design** `[Engineering guidance]` — Remove common failure modes structurally, for example by requiring absolute paths or constrained parameters. Check: can the most common misuse be made impossible instead of merely warned about?

**Typed Schemas** `[Engineering guidance]` — Use explicit types and validation at tool boundaries so invalid inputs fail early. Check: do the tool parameters have an enforceable schema?

## Sources
- Anthropic (2025): "Effective context engineering for AI agents"
- Anthropic (2025): "Writing tools for agents"
- Claude Code docs (2025): "Best practices"
- Schulhoff et al. (2024): "The Prompt Report" (arXiv:2406.06608)
- Mei et al. (2025): "A Survey of Context Engineering for LLMs" (arXiv:2507.13334)
- Qi et al. (2025): "AGENTIF" (arXiv:2505.16944)
- Anthropic (2025): "Building Effective Agents"
