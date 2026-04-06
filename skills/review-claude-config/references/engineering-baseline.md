---
name: engineering-baseline
description: Evidence-based prompt, context, and tool design techniques for evaluating Claude Code skills and agents
last_refreshed: 2026-04-04
---

# Engineering Baseline

## Prompt Engineering Techniques

**Structured Output** `[Proven result]` — Define exact output structure when the task depends on reliable formatting. Check: is the expected output shape explicit?

**Role Priming** `[Engineering guidance]` — Use a functional role statement when domain context materially changes judgment. Use functional descriptions ("You are a dependency checker that…"), not demographic or expert personas — they improve generative tasks but damage factual accuracy on discriminative tasks (arXiv:2603.18507; arXiv:2311.10054v3). Task-irrelevant cues cause up to 26.2% degradation (arXiv:2602.12285, AAAI 2026). Check: does the role add behavioral context, or is it decorative?

**Stepwise Decision Flow** `[Engineering guidance]` — Break fragile reasoning into explicit ordered steps for analysis, validation, or branching work. Check: are complex decisions sequenced instead of left implicit?

**Few-Shot Examples** `[Engineering guidance]` — Add 3-5 canonical examples when output or trigger logic is easy to misread; wrap in `<example>` tags. Check: are examples present where behavior would otherwise be ambiguous? Excessive examples actively degrade performance — optimal count is model-specific, and more is not better (arXiv 2509.13196, 7 models tested; Anthropic Claude 4 Best Practices, April 2026).

**Constraint Specification** `[Proven result]` — State prohibitions, boundaries, and success conditions explicitly. Check: are negative constraints and scope limits visible?

**Verification Criteria** `[Engineering guidance]` — Tell the agent how to confirm correctness using checks, validators, or expected outcomes. Check: can the agent verify the output without relying only on intuition?

**Feedback Loops** `[Engineering guidance]` — For quality-critical work, use a validate-fix-repeat pattern instead of a single-pass instruction. Check: does the workflow include a correction loop where failure is likely?

**Evidence-First Critique** `[Engineering guidance]` — In review tasks, ground findings in quotes, paths, or specific examples rather than generic quality language. Check: could another reviewer verify the claim from the artifact?

**Constraint Load** `[Engineering guidance]` — When a step carries many simultaneous constraints, split it into smaller steps. Performance collapses beyond ~100 simultaneous instances; instance count matters more than raw token count — batch large workloads (arXiv:2603.22608; arXiv:2510.05381; ScaledIF arXiv:2510.14842; arXiv:2512.14754). For agent definitions specifically, dense per-section constraint packing risks the same degradation at smaller scale `[Repo default]`. Check: would breaking the step reduce ambiguity?

**Deterministic Conditionals** `[Proven result]` — Write branch conditions as observable tests, not vague phrases like "if needed" or "as appropriate". Check: would two models take the same branch from the same input?

**Instruction Calibration** `[Engineering guidance]` — Smarter models need less aggressive prompting. Claude 4.6 overtriggers on MUST/CRITICAL/ALWAYS — use natural phrasing ("use this tool when…"). Prefilled responses deprecated in Claude 4.6; use `thinking: {type: "adaptive"}` instead of prescriptive step-by-step chains. Check: does the skill use aggressive imperative language? (Anthropic Claude 4 Best Practices, April 2026)

**Subagent Guardrails** `[Engineering guidance]` — Claude 4.6 natively delegates to subagents but may overuse them and over-engineer solutions. Skills should steer when subagents are/are not warranted and include "keep solutions minimal" constraints. Check: does the skill guide subagent use, or leave the decision fully open? (Anthropic Claude 4 Best Practices, April 2026)

## Context Engineering Techniques

**Context Budget** `[Proven result]` — Focused, relevant context usually beats large but noisy context. Check: is each piece of context earning its token cost?

**Just-in-Time Retrieval** `[Engineering guidance]` — Keep references lightweight and load deeper material only when the task actually needs it. Check: does the item retrieve context progressively instead of front-loading everything?

**Subagent Isolation** `[Engineering guidance]` — Use subagents or isolated workers for bounded subtasks so each sees only the context it needs. Subagents do NOT inherit parent permissions — tool grants must be declared explicitly per subagent (Anthropic Agent SDK, 26-event hook system with deny>ask>allow priority). Check: are large tasks decomposed into focused units, and do subagent tool grants reflect least-privilege rather than assuming inheritance?

**Reference File Separation** `[Engineering guidance]` — Move stable knowledge into `references/` files and keep the main instruction surface concise. Check: is reusable background knowledge separated from the workflow?

**Tool Set Curation** `[Engineering guidance]` — Give agents the smallest tool set that still lets them complete the task. Least-privilege enforcement is practical: MiniScope achieves it with only 1-6% latency overhead vs. standard tool-calling agents (arXiv:2512.11147). Check: could any tool be removed without reducing required capability?

**Activation Precision** `[Engineering guidance]` — Describe clearly when a skill or agent should trigger and when it should not. The description is the sole activation signal for auto-dispatch — trigger logic that appears only in the body is invisible to the dispatcher (Anthropic Tier 1, April 2026). Check: would unrelated requests accidentally match this wording? Does the body contradict what the description says about when to activate?

**Error Preservation** `[Engineering guidance]` — Preserve failed attempts or error traces when they help the system avoid repeating the same mistake. Check: does the workflow retain useful failure context for correction?

**KV-Cache Friendliness** `[Engineering guidance]` — Keep shared prefixes and repeated orchestration blocks stable when dispatching similar work. Check: are repeated agent prompts and tool sets stable enough to benefit from reuse?

**Confirmation Gates** `[Engineering guidance]` — Require explicit user confirmation before destructive or irreversible actions. Check: can the item modify or delete important data without approval?

**Stop Conditions** `[Engineering guidance]` — Define clear termination criteria for retries, loops, and recursive work. For complex multi-step skills, use sprint contracts: define testable "done" criteria before execution begins, not after — this prevents agents from marking work complete without proper verification (Anthropic Planner-Generator-Evaluator, March 2026). Check: could the workflow continue indefinitely without a stopping rule, or are "done" criteria defined only implicitly?

**Retry Ceilings** `[Repo default]` — When a task includes retries, keep the retry budget small and explicit so failures escalate instead of looping invisibly. Check: is there a concrete retry limit?

**Idempotency Design** `[Proven result]` — Make tool operations produce the same result when executed multiple times, enabling safe retries. Check: can every tool call that creates, modifies, or deletes be safely retried? LLM agents retry 15-30% of tool calls due to timeouts or validation errors (Fast.io, Google Cloud Vertex AI, Inngest).

**Circuit Breaker Pattern** `[Engineering guidance]` — Track failures in a sliding window and temporarily halt requests when thresholds are exceeded to prevent cascade failures. Check: does the workflow stop calling a failing service after repeated failures? AWS, Microsoft, and academic research recommend circuit breakers as standard architectural components (AWS Prescriptive Guidance; arXiv:2512.16856; arXiv:2512.09458).

**Progressive Fallback** `[Engineering guidance]` — When operations fail, degrade through self-correction, fallback strategies, and escalation rather than immediate failure. Check: does the workflow have multiple recovery paths instead of binary success/failure? Fast.io and Maxim.ai recommend layered error handling for production agents.

**Knowledge Gap Detection** `[Engineering guidance]` — Teach the system to escalate, retrieve more context, or admit uncertainty when required knowledge is missing. Check: does the workflow prevent confident guessing when information is insufficient?

**Dynamic Tool Loadout** `[Low-evidence area]` — Pre-filter available tools when a large shared catalog creates selection ambiguity, but treat exact numeric cutoffs as heuristic unless benchmarked for the target environment. Check: does the agent see only the tools relevant to the current task?

**Context Compression** `[Engineering guidance]` — For long-running work, compress older context while preserving key decisions and failures. Guided compression (driven by failure-case analysis or learned guidelines) is safe and effective: ACON achieves 26-54% token reduction preserving >95% accuracy (arXiv:2510.00615); Focus achieves 22.7% autonomous compaction with identical SWE-bench accuracy (arXiv:2601.07190); Context-Folding yields 10x smaller active context vs. ReAct baselines (arXiv:2510.11967). Check: does the skill have a compaction strategy for workflows exceeding ~10 tool-call turns?

**Context Placement** `[Proven result]` — Place critical instructions at START and END, never only in the middle. LiM effect peaks at <50% context utilization; at >50%, weight toward END (arXiv:2508.07479, COLM 2025). Reduced in larger models (arXiv:2510.10276). Check: are key instructions anchored at both ends?

## Tool Design Techniques

**Descriptions as Onboarding** `[Engineering guidance]` — Write tool descriptions as if explaining usage to a new teammate. Check: would an unfamiliar engineer understand when and why to use the tool?

**High-Signal Returns** `[Engineering guidance]` — Return only the information needed for the next decision, using filtering or truncation where appropriate. Check: could the tool overwhelm the context with irrelevant output?

**Meaningful Identifiers** `[Engineering guidance]` — Prefer semantic names and explicit parameters over cryptic IDs or overloaded free text. Check: are identifiers self-describing at the call site?

**Actionable Errors** `[Engineering guidance]` — Make tool errors suggest the next fix instead of returning opaque failure states. Check: would the error help the agent recover?

**Avoid Time-Sensitive Guidance** `[Engineering guidance]` — Keep stable prompt assets free of time-bound wording unless the task is explicitly time-sensitive. Check: will the guidance still make sense months later?

**Poka-Yoke Tool Design** `[Engineering guidance]` — Remove common failure modes structurally, for example by requiring absolute paths or constrained parameters. Check: can the most common misuse be made impossible instead of merely warned about?

**Typed Schemas** `[Engineering guidance]` — Use explicit types and validation at tool boundaries so invalid inputs fail early. Check: do the tool parameters have an enforceable schema?

## Sources

**Anthropic:** Effective Context Engineering (2025); Writing Tools for Agents (2025); Building Effective Agents (2025); Claude 4 Best Practices (April 2026); Effective Harnesses for Long-Running Agents (March 2026); Agent SDK Hooks (April 2026); Claude Code Best Practices (2025).

**Research (inline citations link to these):** Schulhoff et al. arXiv:2406.06608; Mei et al. arXiv:2507.13334; Qi et al. arXiv:2505.16944; arXiv:2603.18507; arXiv:2311.10054v3; arXiv:2602.12285; arXiv:2509.13196; arXiv:2511.20836; arXiv:2603.22608; arXiv:2510.05381; arXiv:2512.02246; arXiv:2510.00615; arXiv:2601.07190; arXiv:2510.11967; arXiv:2508.07479; arXiv:2510.10276; arXiv:2511.02230; arXiv:2512.11147; arXiv:2601.08012. Full details in `research/` files.
